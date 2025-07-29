# api_odds_profesional.py
import requests
import datetime
import os
import json
import time
from mercados_validos import obtener_mercados_validos

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
VALID_REGIONS = ['us', 'uk', 'eu', 'au']
MARKETS = 'h2h,spreads,totals,draw_no_bet,btts'
CACHE_FILE = "selecciones_profesional_cache.json"
MAX_DIAS_EVENTO = 7

selecciones_cache = []
ultima_actualizacion = None

def cargar_cache_local():
    global selecciones_cache, ultima_actualizacion
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            selecciones_cache = data.get("selecciones", [])
            ts = data.get("timestamp")
            if ts:
                ultima_actualizacion = datetime.datetime.fromisoformat(ts)

def guardar_cache_local():
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            "selecciones": selecciones_cache,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }, f)

def get_sports():
    url = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    return requests.get(url).json()

def get_odds(sport_key, region):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {'apiKey': API_KEY, 'regions': region, 'markets': MARKETS, 'oddsFormat': 'decimal'}
    return requests.get(url, params=params).json()

def obtener_eventos_odds_api():
    global selecciones_cache, ultima_actualizacion

    ahora = datetime.datetime.utcnow()
    if not ultima_actualizacion:
        cargar_cache_local()

    if ultima_actualizacion and (ahora - ultima_actualizacion).total_seconds() < 3600:
        return selecciones_cache

    deportes = get_sports()
    mercados_validos = obtener_mercados_validos()
    selecciones = []
    hoy = datetime.datetime.now(datetime.timezone.utc)

    for deporte in deportes:
        if not deporte.get("active") or deporte.get("has_outrights"):
            continue

        sport_key = deporte["key"]
        sport_title = deporte["title"]

        if not any(m in mercados_validos.get(sport_key, []) for m in ['btts', 'draw_no_bet', 'totals']):
            continue

        for region in VALID_REGIONS:
            try:
                eventos = get_odds(sport_key, region)
                for evento in eventos:
                    inicio = datetime.datetime.fromisoformat(evento["commence_time"].replace("Z", "+00:00"))
                    if (inicio - hoy).days > MAX_DIAS_EVENTO:
                        continue

                    equipos = evento.get("teams", [])
                    local = evento.get("home_team", "")
                    visitante = [e for e in equipos if e != local]
                    nombre_evento = f"{local} vs {visitante[0]}" if visitante else "Partido"

                    for casa in evento.get("bookmakers", []):
                        for mercado in casa.get("markets", []):
                            mercado_key = mercado.get("key", "")
                            for sel in mercado.get("outcomes", []):
                                cuota = sel.get("price")
                                if not cuota or cuota <= 1.01:
                                    continue
                                prob = round((1 / cuota) * 100, 2)
                                ve = round(cuota * (prob / 100), 2)

                                selecciones.append({
                                    "deporte": sport_title,
                                    "evento": nombre_evento,
                                    "equipo": sel.get("name", "Equipo"),
                                    "cuota": cuota,
                                    "casa": casa.get("title", "Casa"),
                                    "probabilidad": prob,
                                    "ve": ve,
                                    "hora": inicio.strftime("%a %d %b - %H:%M"),
                                    "mercado": mercado_key
                                })
            except:
                continue
            time.sleep(0.3)

    selecciones_cache = selecciones
    ultima_actualizacion = ahora
    guardar_cache_local()
    return selecciones_cache
