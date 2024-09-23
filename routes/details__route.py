from flask import Blueprint, render_template, jsonify
import requests

# Cria o blueprint para as rotas de detalhes
details_bp = Blueprint("details", __name__)

@details_bp.route("/detalhes/<int:pokemon_id>")
def details(pokemon_id):
    try:
        # Faz a requisição para a API do Pokémon
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        response.raise_for_status()
        pokemon_data = response.json()

        # Extrai os tipos, a imagem, os movimentos, a experiência base e os stats do Pokémon
        pokemon_types = [type_info["type"]["name"] for type_info in pokemon_data["types"]]
        pokemon_image = pokemon_data["sprites"]["front_default"]
        pokemon_name = pokemon_data["name"]
        pokemon_moves = [move["move"]["name"] for move in pokemon_data["moves"][:4]]
        base_experience = pokemon_data["base_experience"]
        pokemon_stats = [{"base_stat": stat["base_stat"], "name": stat["stat"]["name"]} for stat in pokemon_data["stats"]]

        # Renderiza o template com os dados do Pokémon
        return render_template(
            "details.html",
            pokemon_id=pokemon_id,
            pokemon_name=pokemon_name,
            pokemon_types=pokemon_types,
            pokemon_image=pokemon_image,
            pokemon_moves=pokemon_moves,
            base_experience=base_experience,
            pokemon_stats=pokemon_stats
        )

    except requests.exceptions.RequestException as e:
        # Retorna um erro em caso de falha na requisição
        return jsonify(error=str(e)), 500