# utils_valor.py
def implied_prob(odds: float) -> float:
    return 1.0 / float(odds)

def fair_probs_two_way(prices_a, prices_b):
    pa = sum(implied_prob(p) for p in prices_a) / len(prices_a)
    pb = sum(implied_prob(p) for p in prices_b) / len(prices_b)
    s = pa + pb
    if s <= 0:
        return None, None
    return pa/s, pb/s

def fair_probs_three_way(prices_a, prices_b, prices_c):
    pa = sum(implied_prob(p) for p in prices_a) / len(prices_a)
    pb = sum(implied_prob(p) for p in prices_b) / len(prices_b)
    pc = sum(implied_prob(p) for p in prices_c) / len(prices_c)
    s = pa+pb+pc
    if s <= 0:
        return None, None, None
    return pa/s, pb/s, pc/s

def consensus_prob(prices):
    return sum(implied_prob(p) for p in prices) / len(prices)

def value_edge(best_price: float, p_fair: float) -> float:
    return best_price * p_fair - 1.0

def kelly_fraction(p: float, b: float, kelly_cap=0.25):
    q = 1 - p
    f = max(0.0, (b*p - q)/b) if b > 0 else 0.0
    return min(f, kelly_cap)