from flask import Blueprint, render_template, jsonify
import requests

details_bp = Blueprint("details", __name__)

@details_bp.route("/detalhes/<int:pokemon_id>")
def details(pokemon_id):
    try:
        # Requisição principal do Pokémon
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        pokemon_response = requests.get(pokemon_url)
        pokemon_response.raise_for_status()
        pokemon_data = pokemon_response.json()

        # Dados básicos
        pokemon_name = pokemon_data["name"]
        pokemon_types = [type_info["type"]["name"] for type_info in pokemon_data["types"]]
        pokemon_image = pokemon_data["sprites"]["front_default"]
        pokemon_moves = [move["move"]["name"] for move in pokemon_data["moves"][:4]]
        base_experience = pokemon_data["base_experience"]
        pokemon_stats = [{"base_stat": stat["base_stat"], "name": stat["stat"]["name"]} for stat in pokemon_data["stats"]]

        # Som (choro)
        cries_url = pokemon_data.get("cries", {}).get("latest", None)

        # --- Taxa de captura ---
        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}"
        species_response = requests.get(species_url)
        species_response.raise_for_status()
        species_data = species_response.json()
        capture_rate = species_data.get("capture_rate", 0)
        capture_percentage = round((capture_rate / 255) * 100)

        # --- Descrição da Pokédex (flavor text em inglês) ---
        description = "Descrição indisponível."
        for entry in species_data.get("flavor_text_entries", []):
            if entry["language"]["name"] == "en":
                description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

        # --- Linha evolutiva (com nível ou método de evolução) ---
        evolution_chain_url = species_data["evolution_chain"]["url"]
        evolution_response = requests.get(evolution_chain_url)
        evolution_response.raise_for_status()
        evolution_data = evolution_response.json()

        def extract_evolutions(chain):
            evo_chain = []
            current = chain
            while current:
                species_name = current["species"]["name"]
                evo_detail = current.get("evolution_details", [])
                trigger = evo_detail[0]["trigger"]["name"] if evo_detail else None
                min_level = evo_detail[0].get("min_level") if evo_detail else None

                evo_chain.append({
                    "name": species_name,
                    "trigger": trigger,
                    "min_level": min_level
                })

                evolves_to = current["evolves_to"]
                current = evolves_to[0] if evolves_to else None
            return evo_chain

        evo_steps = extract_evolutions(evolution_data["chain"])

        evolution_chain = []
        for evo in evo_steps:
            evo_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{evo['name']}").json()
            evolution_chain.append({
                "name": evo["name"],
                "sprite": evo_data["sprites"]["front_default"],
                "trigger": evo["trigger"],
                "min_level": evo["min_level"]
            })

        # --- Localizações (encontros selvagens) ---
        encounters_url = pokemon_data["location_area_encounters"]
        encounters_response = requests.get(encounters_url)
        encounters_response.raise_for_status()
        encounters_data = encounters_response.json()

        location_translations = {
            "kanto-route-1": "Rota 1 de Kanto",
            "tin-tower": "Torre de Latão",
            "seafoam-islands": "Ilhas Espuma do Mar",
            "johto-ice-path": "Caminho de Gelo (Johto)",
        }

        def infer_environment_icon(location_name):
            name = location_name.lower()
            if "cave" in name or "mt" in name or "rock" in name or "tunnel" in name:
                return "⛰️ Caverna"
            elif "forest" in name:
                return "🌲 Floresta"
            elif "sea" in name or "island" in name or "beach" in name:
                return "🌊 Ilha / Mar"
            elif "tower" in name:
                return "🏯 Torre"
            elif "city" in name or "town" in name:
                return "🏙️ Cidade"
            elif "route" in name or "road" in name or "path" in name:
                return "🛤️ Rota"
            else:
                return "❓ Outro"

        encounter_locations = []
        if encounters_data:
            for encounter in encounters_data:
                raw_name = encounter["location_area"]["name"]
                translated_name = location_translations.get(raw_name, raw_name.replace("-", " ").title())
                environment = infer_environment_icon(raw_name)
                versions = [v["version"]["name"].replace("-", " ").title() for v in encounter["version_details"]]

                encounter_locations.append({
                    "name": translated_name,
                    "environment": environment,
                    "versions": versions
                })
        else:
            encounter_locations = None

        # Renderiza o template
        return render_template(
            "details.html",
            pokemon_id=pokemon_id,
            pokemon_data=pokemon_data,
            pokemon_name=pokemon_name,
            pokemon_types=pokemon_types,
            pokemon_image=pokemon_image,
            pokemon_moves=pokemon_moves,
            base_experience=base_experience,
            pokemon_stats=pokemon_stats,
            capture_rate=capture_rate,
            capture_percentage=capture_percentage,
            encounter_locations=encounter_locations,
            description=description,
            cries_url=cries_url,
            evolution_chain=evolution_chain
        )

    except requests.exceptions.RequestException as e:
        return jsonify(error=str(e)), 500
