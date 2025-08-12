import os
import time
import random
import datetime

# Import H2H (mercado principal)
try:
    from api_odds import obtener_eventos_odds_api
except ImportError:
    from api_odds_basico import obtener_eventos_odds_api

# Import mercados secundarios
from api_odds_secundarios import obtener_eventos_secundarios

# Zona horaria
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# ---------- Caché ligera para H2H ----------
H2H_TTL_SEG = int(os.getenv("SELECCIONES_TTL_SEG", "90"))
_h2h_cache = {"t": 0.0, "data": []}

def _now():
    return time.monotonic()

def _get_h2h():
    if _now() - _h2h_cache["t"] > H2H_TTL_SEG or not _h2h_cache["data"]:
        data = obtener_eventos_odds_api() or []
        _h2h_cache.update(t=_now(), data=data)
    return list(_h2h_cache["data"])

# ---------- Utilidades ----------
_MD_ESC_CHARS = ("\\", "_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!")

def _esc_md(s: str) -> str:
    s = str(s)
    for ch in _MD_ESC_CHARS:
        s = s.replace(ch, f"\\{ch}")
    return s

def _fmt_hora(h, tz_name: str = "Europe/Madrid") -> str:
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

def _dedup_por_evento_mercado(selecciones):
    vistos = set()
    out = []
    for s in selecciones:
        key = (s.get("evento"), s.get("mercado") or "h2h", s.get("linea"))
        if key in vistos:
            continue
        vistos.add(key)
        out.append(s)
    return out

def _arma_texto(combinada, titulo):
    total_cuota = 1.0
    prob_total = 1.0
    partes = [f"{titulo}\n"]
    for s in combinada:
        cuota = float(s["cuota"])
        prob_pct = float(s["probabilidad"])
        total_cuota *= cuota
        prob_total  *= (prob_pct / 100.0)

        mercado = s.get("mercado", "h2h")
        linea = s.get("linea")
        linea_txt = f" {linea}" if linea is not None else ""

        fecha_limpia = _fmt_hora(s.get("hora"))

        partes.append(
            f"🎯 *{_esc_md(s['deporte'])} – {_esc_md(s['evento'])}*\n"
            f"• Mercado: _{_esc_md(mercado)}{_esc_md(linea_txt)}_\n"
            f"• Apuesta: _{_esc_md(s['equipo'])}_ @ {cuota} ({_esc_md(s['casa'])})\n"
            f"📅 {fecha_limpia} | 🎲 Prob: {round(prob_pct,2)}% | 💡 VE: {round(float(s['ve']),3)}\n"
        )

    ve_total = round(total_cuota * prob_total, 3)
    partes.append(
        f"\n📊 *Cuota total:* {round(total_cuota, 3)}\n"
        f"📈 *Probabilidad combinada:* {round(prob_total*100, 2)}%\n"
        f"💰 *Valor esperado total:* {ve_total}\n"
        f"🔎 Nota: la VE asume independencia entre selecciones."
    )
    return "\n".join(partes)

# ---------- Funciones H2H ----------
def generar_recomendacion(seguras=True, max_picks=3):
    selecciones = _get_h2h()

    if seguras:
        candidatas = [
            s for s in selecciones
            if s.get("cuota") and 1.20 <= float(s["cuota"]) <= 1.60
            and s.get("ve") is not None and float(s["ve"]) >= 0.95
        ]
    else:
        candidatas = [
            s for s in selecciones
            if s.get("ve") is not None and float(s["ve"]) >= 1.0
        ]

    if len(candidatas) < 2:
        return "🤷 No se encontraron suficientes selecciones fiables."

    candidatas = sorted(
        candidatas,
        key=lambda x: (float(x.get("ve", 0)), float(x.get("probabilidad", 0))),
        reverse=True
    )
    candidatas = _dedup_por_evento_mercado(candidatas)

    k = max(2, min(max_picks, len(candidatas)))
    combinada = candidatas[:k]

    return _arma_texto(combinada, "🛡️ *Combinada segura sugerida:*")

def generar_varias_recomendaciones(cantidad=3):
    textos = []
    for _ in range(max(1, int(cantidad))):
        textos.append(generar_recomendacion(seguras=True))
    return "\n— — — — — —\n".join(textos)

# ---------- Función Profesional (todos mercados secundarios) ----------
def generar_combinada_rentable():
    eventos = obtener_eventos_secundarios() or []

    filtradas = [
        s for s in eventos
        if s.get("cuota") and 1.20 <= float(s["cuota"]) <= 6.0
        and s.get("probabilidad") and 20 <= float(s["probabilidad"]) <= 80
        and s.get("ve") and float(s["ve"]) > 1.02
    ]

    if len(filtradas) < 2:
        return "❌ No se encontraron suficientes selecciones rentables en mercados secundarios."

    filtradas = sorted(
        filtradas,
        key=lambda x: (float(x.get("ve", 0)), float(x.get("probabilidad", 0))),
        reverse=True
    )
    filtradas = _dedup_por_evento_mercado(filtradas)

    if len(filtradas) < 2:
        return "❌ No se encontraron suficientes selecciones tras eliminar duplicados."

    combinada = filtradas[:3]
    return _arma_texto(combinada, "💼 *Combinada profesional (mercados secundarios):*")
