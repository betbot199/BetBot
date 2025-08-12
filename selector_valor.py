# selector_valor.py
from utils_valor import (
    implied_prob,
    fair_probs_two_way,
    fair_probs_three_way,
    value_edge,
)

# --------- Helpers de entrada ---------
def _iter_two_way(groups):
    """
    Itera grupos de 2 vías en dos formatos posibles:
      1) dict key -> {"A":[(odds, casa)...], "B":[...], "meta":{...}, "names":{A:...,B:...}}
      2) list de grupos -> {"meta":{...}, "outcomes": {name:[(odds,casa)...], name2:[...]}}
    Genera tuplas: (meta, nombreA, preciosA, nombreB, preciosB)
    """
    if isinstance(groups, dict):
        for _, g in groups.items():
            A = g.get("A", [])
            B = g.get("B", [])
            if not A or not B:
                continue
            names = g.get("names", {})
            nameA = names.get("A", "A")
            nameB = names.get("B", "B")
            yield g["meta"], nameA, A, nameB, B
    else:
        # lista de grupos con outcomes
        for g in groups:
            outs = g.get("outcomes", {})
            if len(outs) != 2:
                continue
            (nameA, pricesA), (nameB, pricesB) = list(outs.items())
            yield g["meta"], nameA, pricesA, nameB, pricesB


def _iter_three_way(groups):
    """
    Igual que _iter_two_way pero para 3 vías (1X2).
    Genera: (meta, nameA, pricesA, nameB, pricesB, nameC, pricesC)
    """
    if isinstance(groups, dict):
        for _, g in groups.items():
            A = g.get("A", [])
            B = g.get("B", [])
            C = g.get("C", [])
            if not A or not B or not C:
                continue
            names = g.get("names", {})
            nameA = names.get("A", "A")
            nameB = names.get("B", "B")
            nameC = names.get("C", "C")
            yield g["meta"], nameA, A, nameB, B, nameC, C
    else:
        for g in groups:
            outs = g.get("outcomes", {})
            if len(outs) != 3:
                continue
            items = list(outs.items())
            (nameA, pricesA), (nameB, pricesB), (nameC, pricesC) = items[0], items[1], items[2]
            yield g["meta"], nameA, pricesA, nameB, pricesB, nameC, pricesC


# --------- Value bets ---------
def build_two_way_candidates(groups_2way, min_books=3, edge_min=0.02):
    """
    Devuelve lista ordenada de picks con valor para mercados 2 vías.
    Cada item: {meta, nombre, cuota, casa, p_fair, edge}
    """
    picks = []
    for meta, nameA, A, nameB, B in _iter_two_way(groups_2way):
        if min(len(A), len(B)) < min_books:
            continue
        pricesA = [p for p, _ in A]
        pricesB = [p for p, _ in B]
        pA, pB = fair_probs_two_way(pricesA, pricesB)
        if pA is None:
            continue
        bestA = max(A, key=lambda x: x[0])
        bestB = max(B, key=lambda x: x[0])
        eA = value_edge(bestA[0], pA)
        eB = value_edge(bestB[0], pB)
        if eA >= edge_min:
            picks.append({
                "meta": meta, "nombre": nameA, "cuota": round(bestA[0], 3),
                "casa": bestA[1], "p_fair": round(pA, 4), "edge": round(eA, 4)
            })
        if eB >= edge_min:
            picks.append({
                "meta": meta, "nombre": nameB, "cuota": round(bestB[0], 3),
                "casa": bestB[1], "p_fair": round(pB, 4), "edge": round(eB, 4)
            })
    picks.sort(key=lambda x: (x["edge"], x["p_fair"]), reverse=True)
    return picks


def build_three_way_candidates(groups_3way, min_books=3, edge_min=0.02):
    """
    Devuelve lista ordenada de picks con valor para 3 vías (1X2).
    """
    picks = []
    for meta, nameA, A, nameB, B, nameC, C in _iter_three_way(groups_3way):
        if min(len(A), len(B), len(C)) < min_books:
            continue
        pricesA = [p for p, _ in A]
        pricesB = [p for p, _ in B]
        pricesC = [p for p, _ in C]
        pA, pB, pC = fair_probs_three_way(pricesA, pricesB, pricesC)
        if pA is None:
            continue
        bestA = max(A, key=lambda x: x[0]); eA = value_edge(bestA[0], pA)
        bestB = max(B, key=lambda x: x[0]); eB = value_edge(bestB[0], pB)
        bestC = max(C, key=lambda x: x[0]); eC = value_edge(bestC[0], pC)

        if eA >= edge_min:
            picks.append({"meta": meta, "nombre": nameA, "cuota": round(bestA[0],3),
                          "casa": bestA[1], "p_fair": round(pA,4), "edge": round(eA,4)})
        if eB >= edge_min:
            picks.append({"meta": meta, "nombre": nameB, "cuota": round(bestB[0],3),
                          "casa": bestB[1], "p_fair": round(pB,4), "edge": round(eB,4)})
        if eC >= edge_min:
            picks.append({"meta": meta, "nombre": nameC, "cuota": round(bestC[0],3),
                          "casa": bestC[1], "p_fair": round(pC,4), "edge": round(eC,4)})
    picks.sort(key=lambda x: (x["edge"], x["p_fair"]), reverse=True)
    return picks


# --------- Surebets (arbitraje) ---------
def detect_surebets_two_way(groups_2way):
    """
    Busca arbitrajes en 2 vías: 1/oddsA + 1/oddsB < 1.
    Devuelve lista ordenada por margen descendente.
    """
    sbs = []
    for meta, nameA, A, nameB, B in _iter_two_way(groups_2way):
        if not A or not B:
            continue
        bestA = max(A, key=lambda x: x[0])[0]
        bestB = max(B, key=lambda x: x[0])[0]
        inv_sum = implied_prob(bestA) + implied_prob(bestB)
        if inv_sum < 1.0:
            sbs.append({
                "meta": meta,
                "mercado": meta.get("mercado"),
                "linea": meta.get("linea"),
                "precios": {nameA: round(bestA,3), nameB: round(bestB,3)},
                "arb_margin": round(1.0 - inv_sum, 4),
            })
    sbs.sort(key=lambda x: x["arb_margin"], reverse=True)
    return sbs


def detect_surebets_three_way(groups_3way):
    """
    Arbitraje 3 vías (1X2): sum(1/odds_i) < 1.
    """
    sbs = []
    for meta, nameA, A, nameB, B, nameC, C in _iter_three_way(groups_3way):
        if not A or not B or not C:
            continue
        bestA = max(A, key=lambda x: x[0])[0]
        bestB = max(B, key=lambda x: x[0])[0]
        bestC = max(C, key=lambda x: x[0])[0]
        inv_sum = implied_prob(bestA) + implied_prob(bestB) + implied_prob(bestC)
        if inv_sum < 1.0:
            sbs.append({
                "meta": meta,
                "mercado": "h2h",
                "precios": {nameA: round(bestA,3), nameB: round(bestB,3), nameC: round(bestC,3)},
                "arb_margin": round(1.0 - inv_sum, 4),
            })
    sbs.sort(key=lambda x: x["arb_margin"], reverse=True)
    return sbs