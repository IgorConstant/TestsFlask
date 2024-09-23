from flask import Blueprint, jsonify
import requests
import psutil

# Cria o blueprint para o healthcheck
healthcheck_bp = Blueprint("healthcheck", __name__)


@healthcheck_bp.route("/healthcheck")
def healthcheck():
    health_data = {
        "status": "ok",
        "api_status": "unknown",
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "version": "1.0.0",
    }

    # Verifica se a PokeAPI está acessível
    try:
        response = requests.get("https://pokeapi.co/api/v2/")
        if response.status_code == 200:
            health_data["api_status"] = "available"
        else:
            health_data["api_status"] = "unavailable"
    except requests.exceptions.RequestException:
        health_data["api_status"] = "unavailable"

    return jsonify(health_data), (
        200 if health_data["api_status"] == "available" else 503
    )
