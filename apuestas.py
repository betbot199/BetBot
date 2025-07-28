import random
from api_odds import obtener_eventos_odds_api

# Cache en memoria para guardar selecciones
selecciones_cache = []

def cargar_selecciones():
    global selecciones_cache
    if not selecciones_cache:
        selecciones_cache = obtener_eventos_odds_api()
        print(f"📦 Cache cargada con {len(selecciones_cache)} selecciones.")

def generar_recomendacion(seguras=True):
    selecciones = obtener_eventos_odds_api()

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
        texto += f"🎯 *{sel['deporte']} – {sel['evento']}*\n"
        texto += f"• Apuesta: _{sel['equipo']}_ @ {sel['cuota']} ({sel['casa']})  \n"
        texto += f"📅 {sel['hora']} | 🎲 Prob: {sel['probabilidad']}% | 💡 VE: {sel['ve']}\n\n"

    ve_total = round(total_cuota * prob_total, 2)
    texto += f"📊 *Cuota total:* {round(total_cuota, 2)}\n"
    texto += f"📈 *Probabilidad combinada:* {round(prob_total * 100, 2)}%\n"
    texto += f"💰 *Valor esperado total:* {ve_total}\n"

    return texto

def generar_varias_recomendaciones(cantidad=3):
    return "\n" + "\n— — — — — —\n".join(
        [generar_recomendacion(seguras=True) for _ in range(cantidad)]
    )
