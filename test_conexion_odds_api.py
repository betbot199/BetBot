from api_odds import obtener_eventos_odds_api

def test_api_odds():
    print("🔌 Probando conexión con The Odds API...\n")
    eventos = obtener_eventos_odds_api(deporte="upcoming", region="eu", mercados="h2h,totals")

    if not eventos:
        print("❌ No se pudieron obtener eventos. Revisa tu API Key o conexión.")
        return

    print(f"✅ Conexión exitosa. Eventos encontrados: {len(eventos)}\n")
    print("📋 Ejemplos de eventos disponibles:\n")

    for e in eventos[:5]:
        print(f"- {e['deporte']} | {e['mercado']} | {e['evento']} @ {e['cuota']} (VE: {e['valor_esperado']})")

if __name__ == "__main__":
    test_api_odds()
