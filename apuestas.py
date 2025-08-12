# apuestas.py
import os, json, time
from utils_valor import esc_md, fmt_hora, kelly_fraction
from selector_valor import build_two_way_candidates, build_three_way_candidates, detect_surebets_two_way, detect_surebets_three_way
from api_odds_ext import scan_all_markets

EDGE_MIN = float(os.getenv("EDGE_MIN","0.02"))
MIN_BOOKS = int(os.getenv("MIN_BOOKS","3"))
STAKE_MIN = float(os.getenv("STAKE_MIN","0.002"))  # 0.2% bank
STAKE_MAX = float(os.getenv("STAKE_MAX","0.02"))   # 2% bank
KELLY_CAP = float(os.getenv("KELLY_CAP","0.25"))   # 25% Kelly

_bank_file = "bank.json"
_cache = {"t":0, "value":[], "surebets":[], "middles":[]}

def get_bank():
    if os.path.exists(_bank_file):
        try:
            with open(_bank_file,"r") as f: return float(json.load(f).get("bank",1000.0))
        except: pass
    return 1000.0

def set_bank(amount: float):
    with open(_bank_file,"w") as f: json.dump({"bank": float(amount)}, f)

def scan():
    payload = scan_all_markets()
    g2 = payload["groups_2way"]
    g3 = payload["groups_3way"]
    value = build_two_way_candidates(g2, MIN_BOOKS, EDGE_MIN) + build_three_way_candidates(g3, MIN_BOOKS, EDGE_MIN)
    sbs = detect_surebets_two_way(g2) + detect_surebets_three_way(g3)
    _cache.update(t=time.time(), value=value, surebets=sbs)
    return len(value), len(sbs)

def _stake(bank, p_fair, cuota):
    f = kelly_fraction(p_fair, float(cuota)-1.0, KELLY_CAP)
    s = max(STAKE_MIN*bank, min(STAKE_MAX*bank, f*bank))
    return round(s, 2), round(f*100,2)

def format_values(n=5):
    bank = get_bank()
    vals = _cache.get("value",[])[:max(1,int(n))]
    if not vals: return "🤷 No hay value bets en caché. Usa /scan primero."
    parts = ["🔎 Value bets encontradas (top):\n"]
    for v in vals:
        stake, f_k = _stake(bank, v["p_fair"], v["cuota"])
        linea = f" {v.get('linea')}" if v.get("linea") is not None else ""
        parts.append(
            f"🎯 {esc_md(v['deporte'])} – {esc_md(v['evento'])}\n"
            f"• Mercado: {esc_md(v.get('mercado',''))}{esc_md(linea)}\n"
            f"• Selección: {esc_md(v['nombre'])} @ {v['cuota']} ({esc_md(v['casa'])})\n"
            f"📅 {fmt_hora(v['hora'])} | p_fair: {round(v['p_fair']*100,2)}% | edge: {round(v['edge']*100,2)}%\n"
            f"💸 Stake sugerido: {stake} (Kelly {f_k}%)\n"
        )
    return "\n".join(parts)

def format_surebets(n=5):
    sbs = _cache.get("surebets",[])[:max(1,int(n))]
    if not sbs: return "🤷 No hay arbitrajes en caché. Usa /scan primero."
    parts = ["🟢 Arbitrajes (surebets) detectados:\n"]
    for s in sbs:
        linea = f" {s.get('linea')}" if s.get("linea") is not None else ""
        parts.append(
            f"🎯 {esc_md(s['deporte'])} – {esc_md(s['evento'])}\n"
            f"• Mercado: {esc_md(s.get('mercado',''))}{esc_md(linea)}\n"
            f"📅 {fmt_hora(s['hora'])} | margen: {round(s['arb_margin']*100,2)}%\n"
            f"• Precios: {s['precios']}\n"
        )
    return "\n".join(parts)

# opcional: detección simple de middles (totals/spreads) – heurística
def _find_middles():
    # Por simplicidad, reusa el último scan y busca en g2 (no expuesto aquí para mantenerlo corto)
    return []

def format_middles(n=5):
    mids = _cache.get("middles",[])[:max(1,int(n))]
    if not mids: return "🤷 No hay middles detectados ahora mismo."
    parts = ["🟨 Posibles middles: \n"]
    for m in mids:
        parts.append(str(m))
    return "\n".join(parts)