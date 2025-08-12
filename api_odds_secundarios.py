# api_odds_secundarios.py
import os, json, datetime, requests
from collections import defaultdict

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
VALID_REGIONS = ['eu', 'uk']  # foco en mercados europeos
MARKETS = ["spreads", "totals"]  # secundarios
CACHE_FILE = "selecciones_secundarias_cache.json"
CACHE_TTL_SEC = int(os.getenv("SECUNDARIOS_TTL", "1800"))  # 30 min
MAX_DIAS_EVENTO = 7

_cache = {"t": None, "data": []}

def _utcnow():
    return datetime.datetime.utcnow()

def _cache_load():
    if not os.path.exists(CACHE_FILE): 
        return None
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        ts = datetime.datetime.fromisoformat(data.get("_ts"))
        if (_utcnow() - ts).total_seconds() <= CACHE_TTL_SEC:
            return data.get("selecciones", [])
    except Exception:
        pass
    return None

def _cache_save(selecciones):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"_ts": _utcnow().isoformat(), "selecciones": selecciones}, f)
    except Exception:
        pass

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
    # 1) cache
    cached = _cache_load()
    if cached is not None:
        return cached

    # 2) deportes activos (no outrights)
    deportes = _get_sports()
    hoy = datetime.datetime.now(datetime.timezone.utc)
    selecciones = []

    # para agrupar líneas idénticas y calcular consenso vs mejor precio
    # clave: (event_id, market_key, outcome_name, point)
    agrupador = defaultdict(lambda: {
        "prices": [],  # todas las cuotas de todas las casas en esa línea exacta
        "best": None,  # (price, casa_title)
        "meta": None,  # (deporte, evento, hora, market_key, point, equipo_name)
    })

    for dep in deportes:
        if not dep.get("active") or dep.get("has_outrights"):
            continue
        sport_key = dep["key"]
        sport_title = dep["title"]

        # 3) una sola llamada por region con markets="spreads,totals"
        markets_csv = ",".join(MARKETS)
        for region in VALID_REGIONS:
            try:
                eventos = _get_odds(sport_key, region, markets_csv)
            except Exception:
                continue

            for ev in eventos:
                # filtra por fecha
                try:
                    inicio = datetime.datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00"))
                except Exception:
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
                        mk = m.get("key")  # "spreads" o "totals"
                        if mk not in MARKETS:
                            continue
                        for oc in m.get("outcomes", []):
                            price = oc.get("price")
                            point = oc.get("point")
                            name  = oc.get("name")  # "Over"/"Under" para totals, equipo para spreads
                            if not price or price <= 1.01 or point is None or name is None:
                                continue
                            k = (event_id, mk, name, float(point))

                            # guarda meta una vez
                            if agrupador[k]["meta"] is None:
                                agrupador[k]["meta"] = (
                                    sport_title, nombre_evento, inicio.isoformat(),
                                    mk, float(point), name
                                )
                            # añade cuota
                            agrupador[k]["prices"].append((price, casa_title))
                            # best price
                            if not agrupador[k]["best"] or price > agrupador[k]["best"][0]:
                                agrupador[k]["best"] = (price, casa_title)

    # 4) para cada grupo, calcula probabilidad de consenso (media de 1/price) y VE contra mejor cuota
    for k, bundle in agrupador.items():
        if not bundle["prices"]:
            continue
        inv_probs = [1/p for (p, _) in bundle["prices"] if p and p > 1.0]
        if not inv_probs:
            continue
        p_consenso = sum(inv_probs)/len(inv_probs)  # fracción 0..1
        best_price, best_casa = bundle["best"]
        ve = round(best_price * p_consenso, 3)

        sport_title, nombre_evento, inicio_iso, mk, point, name = bundle["meta"]
        selecciones.append({
            "deporte": sport_title,
            "evento": nombre_evento,
            "equipo": name,                # para totals será "Over"/"Under"; para spreads, nombre de equipo
            "mercado": mk,                 # "spreads" | "totals"
            "linea": point,                # handicap o total
            "cuota": round(best_price, 3),
            "casa": best_casa,
            "probabilidad": round(p_consenso * 100, 2),  # en %
            "ve": ve,
            "hora": inicio_iso
        })

    _cache_save(selecciones)
    return selecciones
