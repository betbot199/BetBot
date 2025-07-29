import requests
import time
import datetime
import os
import json
from mercados_validos import obtener_mercados_validos

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
VALID_REGIONS = ['us', 'uk', 'eu', 'au']
MARKETS = 'h2h,spreads,totals,draw_no_bet'

# Ruta de caché
CACHE_FILE = "selecciones_cache.json"

# Variables de caché en memoria
selecciones_cache = []
ultima_actualizacion = None
MAX_DIAS_EVENTO = 7

def cargar_cache_local():
    global selecciones_cache, ultima_actualizacion
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            selecciones_cache = data.get("selecciones", [])
            ts = data.get("timestamp")
            if ts:
                ultima_actualizacion = datetime.datetime.fromisoformat(ts)
            print(f"📥 Caché cargada desde archivo con {len(selecciones_cache)} selecciones.")

def guardar_cache_local():
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            "selecciones": selecciones_cache,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }, f)

def get_sports():
    url = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_odds_for_sport(sport_key, region):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': region,
        'markets': MARKETS,
        'oddsFormat': 'decimal'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def obtener_eventos_odds_api():
    global selecciones_cache, ultima_actualizacion

    ahora = datetime.datetime.utcnow()

    if not ultima_actualizacion:
        cargar_cache_local()

    if ultima_actualizacion and (ahora - ultima_actualizacion).total_seconds() < 86400:
        print("📥 Usando datos en caché.")
        return selecciones_cache

    deportes = get_sports()
    selecciones = []
    hoy = datetime.datetime.now(datetime.timezone.utc)
    
    mercados_validos = obtener_mercados_validos()

    for deporte in deportes:
        if not deporte.get('active') or deporte.get('has_outrights'):
            continue

        sport_key = deporte['key']
        sport_title = deporte['title']
        
        if "btts" not in mercados_validos.get(sport_key, []):
        print(f"⛔️ {sport_key} no tiene mercado BTTS disponible. Saltando...")
        continue

    for region in VALID_REGIONS:
        for region in VALID_REGIONS:
            try:
                eventos = get_odds_for_sport(sport_key, region)

                for evento in eventos:
                    try:
                        inicio = datetime.datetime.fromisoformat(evento['commence_time'].replace("Z", "+00:00"))
                        if (inicio - hoy).days > MAX_DIAS_EVENTO:
                            continue

                        equipos = evento.get("teams", [])
                        local = evento.get("home_team", "")
                        visitante = [e for e in equipos if e != local]
                        nombre_evento = f"{local} vs {visitante[0]}" if visitante else "Partido"

                        for casa in evento.get("bookmakers", []):
                            for mercado in casa.get("markets", []):
                                mercado_key = mercado.get("key", "h2h")
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
                    except Exception:
                        continue

                time.sleep(0.4)
            except Exception as e:
                print(f"⚠️ {sport_key} [{region}] → {e}")

    print(f"📦 Total de selecciones con cuotas procesadas: {len(selecciones)}")
    selecciones_cache = selecciones
    ultima_actualizacion = ahora
    guardar_cache_local()
    return selecciones_cache
