"""
Macro Deployment Gate — aggregates 6 signals into a composite score 0-100.
Returns deployment mode: AGGRESSIVE / NORMAL / REDUCED / DEFENSIVE
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from signals import vix_level, vix_term_structure, breadth, credit_spreads, put_call, tech_momentum


SIGNAL_WEIGHTS = {
    "vix_level": 0.20,
    "vix_term_structure": 0.15,
    "breadth": 0.20,
    "credit_spreads": 0.20,
    "put_call": 0.10,
    "tech_momentum": 0.15,
}

SIGNAL_MODULES = {
    "vix_level": vix_level,
    "vix_term_structure": vix_term_structure,
    "breadth": breadth,
    "credit_spreads": credit_spreads,
    "put_call": put_call,
    "tech_momentum": tech_momentum,
}


def deployment_mode(composite: float) -> tuple[str, str]:
    if composite >= 65:
        return "AGGRESSIVE", "#00ff88"
    elif composite >= 45:
        return "NORMAL", "#88ccff"
    elif composite >= 30:
        return "REDUCED", "#ffaa00"
    else:
        return "DEFENSIVE", "#ff4444"


def run() -> dict:
    results = {}

    def fetch(name, module):
        try:
            return name, module.score()
        except Exception as e:
            return name, {"score": 50, "value": None, "note": f"Error: {e}"}

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch, name, mod): name for name, mod in SIGNAL_MODULES.items()}
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result

    composite = sum(
        results[name]["score"] * weight
        for name, weight in SIGNAL_WEIGHTS.items()
        if name in results
    )

    mode, color = deployment_mode(composite)

    return {
        "composite": round(composite, 1),
        "mode": mode,
        "color": color,
        "signals": results,
    }


if __name__ == "__main__":
    import json
    data = run()
    print(f"\n{'='*50}")
    print(f"MACRO GATE: {data['composite']}/100 — {data['mode']}")
    print(f"{'='*50}")
    for name, sig in data["signals"].items():
        print(f"  {name:25s} {sig['score']:5.1f}  {sig['note']}")
