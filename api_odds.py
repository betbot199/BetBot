import os
import requests
from time import sleep

API_KEY = os.getenv("ODDS_API_KEY")

# 🔍 Regiones que queremos incluir (agregadas Asia y Oceanía)
REGIONES = ["eu", "uk", "us", "au", "cn", "jp"]

# 🏟️ Deportes seleccionados (puedes expandirlo)
DEPORTES = [
    "soccer_epl",
    "soccer_uefa_champs_league",
    "mma_mixed_martial_arts",
    "basketball_nba",
    "tennis_atp",
    "cricket_international_t20",
    "baseball_mlb",
    "americanfootball_nfl",
]

def obtener_eventos_odds_api():
    if not API_KEY:
        raise ValueError("❌ API_KEY no encontrada en variables de entorno.")

    selecciones = []

    for deporte in DEPORTES:
        for region in REGIONES:
            print(f"🔍 Consultando {deporte} en región '{region}'...")

            url = (
                f"https://api.the-odds-api.com/v4/sports/{deporte}/odds/"
                f"?apiKey={API_KEY}&regions={region}&markets=h2h,totals,spreads&oddsFormat=decimal"
            )

            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    eventos = response.json()
                    print(f"✅ {deporte} [{region}] → {len(eventos)} eventos")

                    for evento in eventos:
                        nombre_evento = evento.get("home_team", "") + " vs " + evento.get("away_team", "")
                        for bookie in evento.get("bookmakers", []):
                            casa = bookie["title"]
                            for market in bookie.get("markets", []):
                                tipo = market["key"]
                                for outcome in market.get("outcomes", []):
                                    equipo = outcome["name"]
                                    cuota = outcome["price"]
                                    prob = 1 / cuota if cuota > 0 else 0
                                    ve = round(cuota * prob, 2)

                                    selecciones.append({
                                        "deporte": deporte,
                                        "mercado": tipo,
                                        "equipo": equipo,
                                        "cuota": cuota,
                                        "probabilidad": round(prob * 100, 2),
                                        "ve": ve,
                                        "evento": nombre_evento,
                                        "casa": casa,
                                    })

                        # 👇 Progreso cada 1000 selecciones
                        if len(selecciones) % 1000 == 0:
                            print(f"📈 {len(selecciones)} selecciones acumuladas...")

                else:
                    print(f"⚠️ {deporte} [{region}] → Error {response.status_code}: {response.text}")

            except Exception as e:
                print(f"❌ Error al consultar {deporte} [{region}]: {e}")

            sleep(0.3)  # evitar golpear demasiado la API

    print(f"📦 Total de selecciones con cuotas procesadas: {len(selecciones)}")
    return selecciones
