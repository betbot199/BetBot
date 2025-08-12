# utils_valor.py
from statistics import mean
import datetime

# ========= Utilidades de formato (Markdown + fechas) =========
MD_ESC_CHARS = ("\\","","*","[","]","(",")","~","`",">","#","+","-","=","|","{","}","",".","!")

def esc_md(s: str) -> str:
    s = str(s)
    for ch in _MD_ESC_CHARS:
        s = s.replace(ch, f"\\{ch}")
    return s

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

def fmt_hora(h, tz_name: str = "Europe/Madrid") -> str:
    """
    Convierte ISO '2025-08-16T22:00:00+00:00' (o con 'Z') a '16 Ago 2025 · 00:00'
    en la zona indicada. Si falla, devuelve el valor tal cual.
    """
    try:
        if not isinstance(h, str):
            return str(h)
        iso = h.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(iso)
        if ZoneInfo:
            dt = dt.astimezone(ZoneInfo(tz_name))
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        mes_txt = meses[dt.month - 1]
        return f"{dt.day:02d} {mes_txt} {dt.year} · {dt:%H:%M}"
    except Exception:
        return str(h)

# ========= Cálculo de probabilidades justas y edge =========
def implied_prob(odds: float) -> float:
    """Probabilidad implícita a partir de cuota decimal."""
    return 1.0 / float(odds)

def fair_probs_two_way(prices_a, prices_b):
    """
    Quita vigorish en mercados de 2 vías (A/B) normalizando la media de
    probabilidades implícitas de ambos lados.
    """
    if not prices_a or not prices_b:
        return None, None
    pa = mean(implied_prob(p) for p in prices_a)
    pb = mean(implied_prob(p) for p in prices_b)
    s = pa + pb
    if s <= 0:
        return None, None
    return pa/s, pb/s

def fair_probs_three_way(prices_a, prices_b, prices_c):
    """Quita vigorish en 3 vías (1X2) normalizando las medias."""
    if not prices_a or not prices_b or not prices_c:
        return None, None, None
    pa = mean(implied_prob(p) for p in prices_a)
    pb = mean(implied_prob(p) for p in prices_b)
    pc = mean(implied_prob(p) for p in prices_c)
    s = pa + pb + pc
    if s <= 0:
        return None, None, None
    return pa/s, pb/s, pc/s

def value_edge(best_price: float, p_fair: float) -> float:
    """
    Edge = EV - 1 = cuota_mejor * p_fair - 1.
    Si > 0, hay valor esperado positivo.
    """
    return float(best_price) * float(p_fair) - 1.0

# ========= Gestión de stake (Kelly fraccional) =========
def kelly_fraction(p: float, b: float | None = None, kelly_cap: float = 0.25) -> float:
    """
    Fracción de Kelly para cuota decimal.
    - p: prob. justa (0..1)
    - b: beneficio sobre la apuesta (cuota-1). Si por error pasas la cuota (>=1), se convierte a (cuota-1).
    - kelly_cap: límite superior (p.ej. 0.25 = 25% de Kelly).
    Devuelve fracción del bank a apostar (0..kelly_cap).
    """
    if b is None:
        return 0.0
    # Si te pasan la cuota en vez de (cuota-1), conviértela
    if b >= 1.0:
        b = b - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - float(p)
    f = (b * float(p) - q) / b
    if f < 0:
        return 0.0
    return min(float(kelly_cap), f)