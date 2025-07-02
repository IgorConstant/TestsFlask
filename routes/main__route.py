from flask import Blueprint, render_template, jsonify, request
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

main_bp = Blueprint("main", __name__)

# Cache simples em memória (pode melhorar usando Redis ou arquivo)
cache_lock = threading.Lock()
pokemon_cache = {}  # chave: offset, valor: lista de pokemons com detalhes


def fetch_pokemon_data(pokemon):
    pokemon_data = requests.get(pokemon["url"], timeout=5).json()
    pokemon_id = pokemon["url"].split("/")[-2]
    pokemon_types = [type_info["type"]["name"] for type_info in pokemon_data["types"]]
    return {
        "id": pokemon_id,
        "name": pokemon["name"],
        "image": pokemon_data["sprites"]["front_default"],
        "types": pokemon_types,
    }


def get_pokemons_from_api(limit=50, offset=0):
    # Busca lista básica de pokemons do endpoint principal
    url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    pokemons = response.json()["results"]

    # Busca detalhes paralelamente
    with ThreadPoolExecutor(max_workers=10) as executor:
        pokemons_detailed = list(executor.map(fetch_pokemon_data, pokemons))
    return pokemons_detailed


@main_bp.route("/")
def index():
    search_term = request.args.get("search", "").lower()
    # Sempre começa da página 1 na renderização inicial
    limit = 48
    page = 1
    offset = (page - 1) * limit

    # Para simplicidade, na primeira renderização trazemos só os primeiros 48 pokemons sem filtro
    try:
        if search_term:
            # Busca todos os nomes de pokémons da API (só nome e url)
            url = "https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            all_basic = response.json()["results"]
            # Filtra pelo termo de busca
            filtered = [p for p in all_basic if search_term in p["name"].lower()]
            # Limita a quantidade de resultados detalhados
            filtered = filtered[:limit]
            # Busca detalhes dos pokémons filtrados
            with ThreadPoolExecutor(max_workers=10) as executor:
                pokemons = list(executor.map(fetch_pokemon_data, filtered))
        else:
            with cache_lock:
                if offset not in pokemon_cache:
                    pokemon_cache[offset] = get_pokemons_from_api(limit, offset)
                pokemons = pokemon_cache[offset]

        return render_template("index.html", pokemons=pokemons, search=search_term, page=page)

    except requests.exceptions.RequestException as e:
        return jsonify(error=str(e)), 500


@main_bp.route("/load_more")
def load_more():
    try:
        search_term = request.args.get("search", "").lower()
        page = int(request.args.get("page", 2))
        limit = 50
        offset = (page - 1) * limit

        with cache_lock:
            if offset not in pokemon_cache:
                pokemon_cache[offset] = get_pokemons_from_api(limit, offset)

            pokemons = pokemon_cache[offset]

        if search_term:
            pokemons = [p for p in pokemons if search_term in p["name"].lower()]

        has_more = (offset + limit) < 600

        # renderiza só os cards e retorna como HTML
        html = render_template("partials/_cards.html", pokemons=pokemons)

        return jsonify(html=html, has_more=has_more, next_page=page + 1)

    except Exception as e:
        return jsonify(error=str(e)), 500
