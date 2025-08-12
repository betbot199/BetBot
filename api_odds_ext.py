# api_odds_ext.py
import os, json, datetime, requests
from collections import defaultdict

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
VALID_REGIONS = os.getenv("ODDS_REGIONS","eu,uk").split(",")  # ajustable
MARKETS = os.getenv("ODDS_MARKETS","spreads,totals,btts,draw_no_bet,alternate_spreads,alternate_totals,h2h").split(",")
CACHE_FILE = "scan_cache.json"
CACHE_TTL_SEC = int(os.getenv("SCAN_TTL","900"))  # 15 min
MAX_DIAS_EVENTO = int(os.getenv("MAX_DIAS_EVENTO","7"))

def _utcnow(): return datetime.datetime.utcnow()

def _cache_load():
    if not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE,"r") as f: data = json.load(f)
        ts = datetime.datetime.fromisoformat(data.get("_ts"))
        if (_utcnow()-ts).total_seconds() <= CACHE_TTL_SEC:
            return data.get("payload")
    except: pass
    return None

def _cache_save(payload):
    try:
        with open(CACHE_FILE,"w") as f:
            json.dump({"_ts":_utcnow().isoformat(),"payload":payload}, f)
    except: pass

def _get_sports():
    url = f"{BASE_URL}/sports/?apiKey={API_KEY}"
    return requests.get(url, timeout=25).json()

def _get_odds(sport_key, region, markets_csv):
    url = f"{BASE_URL}/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY, "regions": region,
        "markets": markets_csv, "oddsFormat": "decimal"
    }
    return requests.get(url, params=params, timeout=35).json()

def scan_all_markets():
    cached = _cache_load()
    if cached is not None:
        return cached

    deportes = _get_sports()
    hoy = datetime.datetime.now(datetime.timezone.utc)

    # grupos 2-vías: (event_id, market_key, point) -> dict with A/B lists
    groups_2way = {}
    # grupos 3-vías (h2h 1X2): (event_id, "h2h") -> dict with A/B/C lists
    groups_3way = {}

    def ensure_2way(key, meta, names=None):
        if key not in groups_2way:
            groups_2way[key] = {"A":[], "B":[], "names": names or {}, "meta": meta}

    def ensure_3way(key, meta, names=None):
        if key not in groups_3way:
            groups_3way[key] = {"A":[], "B":[], "C":[], "names": names or {}, "meta": meta}

    markets_csv = ",".join(MARKETS)

    for dep in deportes:
        if not dep.get("active") or dep.get("has_outrights"):  # sin outrights
            continue
        sport_key = dep["key"]
        sport_title = dep["title"]

        for region in VALID_REGIONS:
            try:
                eventos = _get_odds(sport_key, region, markets_csv)
            except Exception:
                continue

            for ev in eventos:
                try:
                    inicio = datetime.datetime.fromisoformat(ev["commence_time"].replace("Z","+00:00"))
                except Exception:
                    continue
                if (inicio - hoy).days > MAX_DIAS_EVENTO:
                    continue

                event_id = ev.get("id") or f"{ev.get('home_team')}-{ev.get('commence_time')}"
                equipos = ev.get("teams", [])
                home = ev.get("home_team", "")
                away = [e for e in equipos if e != home]
                evento = f"{home} vs {away[0]}" if away else "Partido"

                for bm in ev.get("bookmakers", []):
                    casa = bm.get("title","Casa")
                    for m in bm.get("markets", []):
                        mk = m.get("key")  # spreads, totals, btts, draw_no_bet, alternate_*, h2h
                        if mk not in MARKETS: continue
                        for oc in m.get("outcomes", []):
                            price = oc.get("price")
                            point = oc.get("point")  # puede ser None
                            name  = oc.get("name")
                            if not price or price <= 1.01 or name is None:
                                continue

                            meta = {
                                "deporte": sport_title,
                                "sport_key": sport_key,
                                "evento": evento,
                                "hora": inicio.isoformat(),
                                "event_id": event_id
                            }

                            if mk == "h2h":
                                key = (event_id, "h2h")
                                ensure_3way(key, {**meta, "mercado":"h2h"})
                                # map a/b/c por nombre
                                # intentamos home/away/draw, si no, por orden alfabético estable
                                nm = name.strip()
                                if nm.lower() in ("draw","empate","tie","x"):
                                    groups_3way[key]["C"].append((price, casa))
                                    groups_3way[key]["names"]["C"] = nm
                                elif nm == home:
                                    groups_3way[key]["A"].append((price, casa))
                                    groups_3way[key]["names"]["A"] = nm
                                else:
                                    groups_3way[key]["B"].append((price, casa))
                                    groups_3way[key]["names"]["B"] = nm
                                continue

                            # 2-vías
                            key = (event_id, mk, float(point) if point is not None else None)
                            ensure_2way(key, {**meta, "mercado": mk, "linea": point}, names={})
                            nm = name.strip()
                            # estandariza names para totals y btts
                            if mk.startswith("totals") or mk == "totals" or mk == "alternate_totals":
                                # Over/Under
                                if nm.lower() in ("over","o","más","mas"):
                                    groups_2way[key]["A"].append((price, casa))
                                    groups_2way[key]["names"]["A"] = "Over"
                                else:
                                    groups_2way[key]["B"].append((price, casa))
                                    groups_2way[key]["names"]["B"] = "Under"
                            elif mk in ("btts","draw_no_bet"):
                                # Yes/No o EquipoA/EquipoB
                                if nm.lower() in ("yes","sí","si"):
                                    groups_2way[key]["A"].append((price, casa))
                                    groups_2way[key]["names"]["A"] = "Yes"
                                elif nm.lower() in ("no"):
                                    groups_2way[key]["B"].append((price, casa))
                                    groups_2way[key]["names"]["B"] = "No"
                                else:
                                    # equipo A/B (DNB)
                                    # mapeo estable por orden alfabético
                                    side = "A" if nm < (groups_2way[key]["names"].get("A") or "Ω") else "B"
                                    groups_2way[key][side].append((price, casa))
                                    groups_2way[key]["names"][side] = nm
                            else:
                                # spreads/alternate_spreads -> equipo A/B
                                side = "A" if nm < (groups_2way[key]["names"].get("A") or "Ω") else "B"
                                groups_2way[key][side].append((price, casa))
                                groups_2way[key]["names"][side] = nm

    payload = {"groups_2way": groups_2way, "groups_3way": groups_3way}
    _cache_save(payload)
    return payload