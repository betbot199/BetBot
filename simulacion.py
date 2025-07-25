import random

def simular_eventos(num_eventos=30):
    deportes = [
        "Fútbol", "Tenis", "NBA", "NFL", "eSports", "Boxeo", 
        "MMA", "Hockey", "Béisbol", "Balonmano", "Ciclismo"
    ]

    mercados = [
        "Gana", "Over 2.5 goles", "Ambos marcan", "Hándicap -1.5", "Under 3.5 goles",
        "Más de 5 tarjetas", "Menos de 10 córners", "Gana 2-0 sets", "Over 215.5 puntos", 
        "1er tiempo - Empate", "Gana por decisión", "Más de 3 knockdowns"
    ]

    eventos = []
    for _ in range(num_eventos):
        evento = {
            "deporte": random.choice(deportes),
            "mercado": random.choice(mercados),
            "evento": f"Equipo{random.randint(1, 100)} vs Equipo{random.randint(101, 200)}",
            "cuota": round(random.uniform(1.50, 3.00), 2),
            "probabilidad_estim": round(random.uniform(0.40, 0.65), 2)
        }
        evento["valor_esperado"] = round(evento["cuota"] * evento["probabilidad_estim"], 2)
        eventos.append(evento)

    return eventos

