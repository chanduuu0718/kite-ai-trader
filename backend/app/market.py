"""Mock Indian market data for local UI development. Replace with a licensed feed adapter.""" 
from datetime import datetime, timezone
from random import Random

SYMBOLS = [
    ("RELIANCE", "Reliance Industries", 1450.0),
    ("HDFCBANK", "HDFC Bank", 1680.0),
    ("ICICIBANK", "ICICI Bank", 1280.0),
    ("INFY", "Infosys", 1540.0),
    ("TCS", "Tata Consultancy Services", 3250.0),
    ("SBIN", "State Bank of India", 790.0),
    ("BHARTIARTL", "Bharti Airtel", 1880.0),
    ("ITC", "ITC", 410.0),
    ("LT", "Larsen & Toubro", 3550.0),
    ("AXISBANK", "Axis Bank", 1120.0),
]

def snapshot():
    rng = Random(20261102)
    rows = []
    for symbol, name, base in SYMBOLS:
        change = rng.uniform(-1.8, 1.8)
        price = round(base * (1 + change / 100), 2)
        rows.append({"symbol": symbol, "name": name, "price": price,
                     "change_pct": round(change, 2), "volume": rng.randint(800_000, 9_000_000),
                     "source": "MOCK", "timestamp": datetime.now(timezone.utc).isoformat()})
    return rows
