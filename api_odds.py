# api_odds.py
import os, json, datetime, requests
from collections import defaultdict

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
REGIONS = (os.getenv("REGIONS") or "eu,uk").split(",")
MARKETS = ["h2h", "spreads", "totals", "btts", "draw_no_bet"]  # secund/clave
CACHE_FILE = "cache_grupos.json"
SCAN_TTL_SEC = int(os.getenv("SCAN_TTL_SEC", "1800"))  # 30 min
MAX_DIAS_EVENTO = 7

SPORTS_WHITELIST = set(filter(None, (os.getenv("SPORTS_WHITELIST") or "").split(",")))

def _utcnow(): return datetime.datetime.utcnow()

def _cache_load():
    if not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        ts = datetime.datetime.fromisoformat(data.get("_ts"))
        if (_utcnow() - ts).total_seconds() <= SCAN_TTL_SEC:
            return data.get("grupos", [])
    except: pass
    return None

def _cache_save(grupos):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"_ts": _utcnow().isoformat(), "grupos": grupos}, f)
    except: pass

def _get_sports():
    url = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    return requests.get(url, timeout=25).json()

def _get_odds(sport_key, region, markets_csv):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {"apiKey": API_KEY, "regions": region, "markets": markets_csv, "oddsFormat": "decimal"}
    return requests.get(url, params=params, timeout=30).json()

def _normalize_two_way_names(name: str):
    n = (name or "").strip().lower()
    if n in ("over","o"): return "Over"
    if n in ("under","u"): return "Under"
    if n in ("yes","si","sí"): return "Yes"
    if n in ("no"): return "No"
    return name  # equipos o nombres tal cual

def scan_and_group():
    """Devuelve lista de grupos. Cada grupo contiene TODAS las cuotas por outcome."""
    cached = _cache_load()
    if cached is not None:
        return cached

    deportes = _get_sports()
    hoy = datetime.datetime.now(datetime.timezone.utc)

    grupos = []  # lista de dicts listos para selector
    # agrupador temporal por (event_id, market, line)
    tmp = defaultdict(lambda: {
        "meta": None,              # deporte, sport_key, evento, hora, market, line, event_id
        "outcomes": defaultdict(list),  # nombre_outcome -> [(cuota, casa)]
    })

    for dep in deportes:
        if not dep.get("active") or dep.get("has_outrights"):  # fuera outrights
            continue
        sport_key = dep["key"]
        sport_title = dep["title"]

        if SPORTS_WHITELIST and sport_key not in SPORTS_WHITELIST:
            continue

        markets_csv = ",".join(MARKETS)
        for region in REGIONS:
            try:
                eventos = _get_odds(sport_key, region, markets_csv)
            except Exception:
                continue

            for ev in eventos:
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
                nombre_evento = f"{local} vs {visitante[0]}" if visitante else (ev.get("title") or "Partido")

                for bm in ev.get("bookmakers", []):
                    casa_title = bm.get("title", "Casa")
                    for m in bm.get("markets", []):
                        mk = m.get("key")  # h2h, spreads, totals, btts, draw_no_bet
                        if mk not in MARKETS:
                            continue
                        for oc in m.get("outcomes", []):
                            price = oc.get("price")
                            if not price or price <= 1.01:
                                continue
                            point = oc.get("point")  # puede ser None (btts, dnb, h2h)
                            name  = oc.get("name")
                            name  = _normalize_two_way_names(name)

                            key = (event_id, mk, float(point) if point is not None else None)

                            if tmp[key]["meta"] is None:
                                tmp[key]["meta"] = dict(
                                    deporte=sport_title,
                                    sport_key=sport_key,
                                    evento=nombre_evento,
                                    hora=inicio.isoformat(),
                                    mercado=mk,
                                    linea=(float(point) if point is not None else None),
                                    event_id=event_id
                                )
                            tmp[key]["outcomes"][name].append((float(price), casa_title))

    for key, pack in tmp.items():
        if not pack["outcomes"]:
            continue
        grupos.append(dict(meta=pack["meta"], outcomes=pack["outcomes"]))

    _cache_save(grupos)
    return grupos