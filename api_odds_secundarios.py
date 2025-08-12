# api_odds_secundarios.py
import os, json, datetime, requests
from collections import defaultdict

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
VALID_REGIONS = ['eu', 'uk']  
# Todos los mercados secundarios disponibles
MARKETS = ["spreads", "totals", "btts", "draw_no_bet", "alternate_spreads", "alternate_totals"]

CACHE_FILE = "selecciones_secundarias_cache.json"
CACHE_TTL_SEC = int(os.getenv("SECUNDARIOS_TTL", "1800"))  
MAX_DIAS_EVENTO = 7

def _utcnow(): return datetime.datetime.utcnow()

def _cache_load():
    if not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        ts = datetime.datetime.fromisoformat(data.get("_ts"))
        if (_utcnow() - ts).total_seconds() <= CACHE_TTL_SEC:
            return data.get("selecciones", [])
    except: pass
    return None

def _cache_save(selecciones):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"_ts": _utcnow().isoformat(), "selecciones": selecciones}, f)
    except: pass

def _get_sports():
    url = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    return requests.get(url, timeout=20).json()

def _get_odds(sport_key, region, markets_csv):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": region,
        "markets": markets_csv,
        "oddsFormat": "decimal"
    }
    return requests.get(url, params=params, timeout=25).json()

def obtener_eventos_secundarios():
    cached = _cache_load()
    if cached is not None:
        return cached

    deportes = _get_sports()
    hoy = datetime.datetime.now(datetime.timezone.utc)
    selecciones = []

    agrupador = defaultdict(lambda: {
        "prices": [],
        "best": None,
        "meta": None,
    })

    for dep in deportes:
        if not dep.get("active") or dep.get("has_outrights"):
            continue
        sport_key = dep["key"]
        sport_title = dep["title"]

        markets_csv = ",".join(MARKETS)
        for region in VALID_REGIONS:
            try:
                eventos = _get_odds(sport_key, region, markets_csv)
            except:
                continue

            for ev in eventos:
                try:
                    inicio = datetime.datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00"))
                except:
                    continue
                if (inicio - hoy).days > MAX_DIAS_EVENTO:
                    continue

                event_id = ev.get("id") or f"{ev.get('home_team')}-{ev.get('commence_time')}"
                equipos = ev.get("teams", [])
                local = ev.get("home_team", "")
                visitante = [e for e in equipos if e != local]
                nombre_evento = f"{local} vs {visitante[0]}" if visitante else "Partido"

                for bm in ev.get("bookmakers", []):
                    casa_title = bm.get("title", "Casa")
                    for m in bm.get("markets", []):
                        mk = m.get("key")
                        if mk not in MARKETS:
                            continue
                        for oc in m.get("outcomes", []):
                            price = oc.get("price")
                            point = oc.get("point")  # Puede ser None en btts/draw_no_bet
                            name  = oc.get("name")
                            if not price or price <= 1.01 or name is None:
                                continue
                            k = (event_id, mk, name, float(point) if point is not None else None)

                            if agrupador[k]["meta"] is None:
                                agrupador[k]["meta"] = (
                                    sport_title, nombre_evento, inicio.isoformat(),
                                    mk, point, name
                                )
                            agrupador[k]["prices"].append((price, casa_title))
                            if not agrupador[k]["best"] or price > agrupador[k]["best"][0]:
                                agrupador[k]["best"] = (price, casa_title)

    for k, bundle in agrupador.items():
        if not bundle["prices"]:
            continue
        inv_probs = [1/p for (p, _) in bundle["prices"] if p and p > 1.0]
        if not inv_probs:
            continue
        p_consenso = sum(inv_probs)/len(inv_probs)
        best_price, best_casa = bundle["best"]
        ve = round(best_price * p_consenso, 3)

        sport_title, nombre_evento, inicio_iso, mk, point, name = bundle["meta"]
        selecciones.append({
            "deporte": sport_title,
            "evento": nombre_evento,
            "equipo": name,
            "mercado": mk,
            "linea": point,
            "cuota": round(best_price, 3),
            "casa": best_casa,
            "probabilidad": round(p_consenso * 100, 2),
            "ve": ve,
            "hora": inicio_iso
        })

    _cache_save(selecciones)
    return selecciones
