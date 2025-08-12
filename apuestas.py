import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

# Escapado Markdown
_MD_ESC_CHARS = ("\\", "_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!")
def _esc_md(s: str) -> str:
    s = str(s)
    for ch in _MD_ESC_CHARS:
        s = s.replace(ch, f"\\{ch}")
    return s

# Nueva función para formatear hora
def _fmt_hora(h, tz_name: str = "Europe/Madrid") -> str:
    """
    Acepta ISO (ej: '2025-08-16T22:00:00+00:00' o con 'Z') o cualquier string.
    Devuelve '16 Ago 2025 · 00:00' en la zona indicada (por defecto Europe/Madrid).
    Si no puede parsear, devuelve el valor original tal cual.
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

# Función para deduplicar selecciones por evento/mercado/línea
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

# Nueva versión de _arma_texto con fecha limpia
def _arma_texto(combinada, titulo):
    total_cuota = 1.0
    prob_total = 1.0
    partes = [f"{titulo}\n"]
    for s in combinada:
        cuota = float(s["cuota"])
        prob_pct = float(s["probabilidad"])  # en %
        total_cuota *= cuota
        prob_total  *= (prob_pct / 100.0)

        mercado = s.get("mercado", "h2h")
        linea = s.get("linea")
        linea_txt = f" {linea}" if linea is not None else ""

        # Fecha limpia (sin escapar Markdown)
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
