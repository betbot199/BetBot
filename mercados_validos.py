import os
import json
import datetime
import requests

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
CACHE_FILE = "mercados_validos_cache.json"

MAX_CACHE_AGE = 86400  # 24h

def cargar_cache_mercados():
    if not os.path.exists(CACHE_FILE):
        return {}, None
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
        timestamp = data.get("_timestamp")
        return {k: v for k, v in data.items() if k != "_timestamp"}, timestamp

def guardar_cache_mercados(data):
    data["_timestamp"] = datetime.datetime.utcnow().isoformat()
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_markets_for_sport(sport_key):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "us,uk,eu,au",
        "markets": "h2h,spreads,totals",  # quitado btts y draw_no_bet
        "oddsFormat": "decimal"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        eventos = response.json()
        mercados = set()

        for evento in eventos:
            for bookie in evento.get("bookmakers", []):
                for market in bookie.get("markets", []):
                    key = market.get("key")
                    if key:
                        mercados.add(key)

        return list(mercados)
    except Exception as e:
        print(f"⚠️ Error al consultar mercados para {sport_key}: {e}")
        return []

def obtener_mercados_validos():
    cache, timestamp = cargar_cache_mercados()

    if timestamp:
        try:
            ts = datetime.datetime.fromisoformat(timestamp)
            if (datetime.datetime.utcnow() - ts).total_seconds() < MAX_CACHE_AGE:
                print("📥 Usando caché de mercados válidos.")
                return cache
        except Exception:
            pass

    print("🔄 Actualizando caché de mercados válidos...")
    url_sports = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    response = requests.get(url_sports)
    response.raise_for_status()
    deportes = response.json()

    mercados_validos = {}
    for deporte in deportes:
        if not deporte.get("active") or deporte.get("has_outrights"):
            continue
        key = deporte["key"]
        mercados = get_markets_for_sport(key)
        if mercados:
            mercados_validos[key] = mercados

    guardar_cache_mercados(mercados_validos)
    return mercados_validos
