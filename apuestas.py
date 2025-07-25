import random
from api_odds import obtener_eventos_odds_api

# Cache global en memoria
eventos_cache = []

def cargar_eventos_en_memoria():
    global eventos_cache
    if not eventos_cache:
        print("📥 Cargando eventos desde API...")
        eventos_cache = obtener_eventos_odds_api()
    else:
        print("🧠 Usando eventos desde memoria (RAM).")
    return eventos_cache

def generar_recomendacion(seguras=True):
    selecciones = cargar_eventos_en_memoria()

    if seguras:
        buenas = [
            s for s in selecciones
            if 1.2 <= s["cuota"] <= 1.6 and s["ve"] >= 0.95
        ]
    else:
        buenas = [s for s in selecciones if s["ve"] >= 1.0]

    if len(buenas) < 2:
        return "🤷 No se encontraron suficientes selecciones fiables."

    n = random.choice([2, 3, 4])
    combinada = random.sample(buenas, k=min(n, len(buenas)))

    total_cuota = 1
    prob_total = 1
    texto = "🛡️ *Combinada segura sugerida:*\n\n"

    for sel in combinada:
        total_cuota *= sel["cuota"]
        prob_total *= (sel["probabilidad"] / 100)
        texto += f"• *{sel['deporte']}* – {sel['equipo']} @ {sel['cuota']} ({sel['casa']})\n"
        texto += f"  Prob. estimada: {sel['probabilidad']}% | VE: {sel['ve']}\n\n"

    ve_total = round(total_cuota * prob_total, 2)
    texto += f"🎯 *Cuota total:* {round(total_cuota, 2)}\n"
    texto += f"📈 *Probabilidad combinada:* {round(prob_total * 100, 2)}%\n"
    texto += f"💰 *Valor esperado total:* {ve_total}\n"

    return texto

def generar_varias_recomendaciones(cantidad=3):
    return "\n".join([generar_recomendacion(seguras=True) for _ in range(cantidad)])
