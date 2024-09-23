from flask import Blueprint, render_template, jsonify # type: ignore
import requests # type: ignore
from concurrent.futures import ThreadPoolExecutor

# Cria o blueprint para as rotas principais
main_bp = Blueprint("main", __name__)


def fetch_pokemon_data(pokemon):
    pokemon_data = requests.get(pokemon["url"]).json()
    pokemon_id = pokemon["url"].split("/")[-2]
    pokemon_types = [type_info["type"]["name"] for type_info in pokemon_data["types"]]
    return {
        "id": pokemon_id,
        "name": pokemon["name"],
        "image": pokemon_data["sprites"]["front_default"],
        "types": pokemon_types,
    }


@main_bp.route("/")
def index():
    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=250")
        response.raise_for_status()
        pokemons = response.json()["results"]

        with ThreadPoolExecutor() as executor:
            pokemons_with_images = list(executor.map(fetch_pokemon_data, pokemons))

        return render_template("index.html", pokemons=pokemons_with_images)

    except requests.exceptions.RequestException as e:
        return jsonify(error=str(e)), 500
