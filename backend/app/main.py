from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .market import snapshot
from .engine import scan

app = FastAPI(title="KITE AI TRADER API", version="0.1.0",
              description="Indian market dashboard MVP — mock data and paper trading only.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class PaperOrder(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    side: str
    quantity: int = Field(gt=0, le=100000)
    price: float = Field(gt=0)

paper_orders = []

@app.get("/api/health")
def health(): return {"status": "ok", "mode": "paper", "data": "mock"}

@app.get("/api/market")
def market(): return {"index": {"nifty": 0, "sensex": 0, "source": "mock placeholder"}, "stocks": snapshot()}

@app.get("/api/scanner")
def scanner(): return {"mode": "DEMO RULES", "results": scan()}

@app.get("/api/paper/orders")
def orders(): return paper_orders

@app.post("/api/paper/orders")
def create_order(order: PaperOrder):
    if order.side.upper() not in ("BUY", "SELL"):
        return {"error": "side must be BUY or SELL"}
    record = {**order.model_dump(), "side": order.side.upper(),
              "id": len(paper_orders)+1, "status": "SIMULATED"}
    paper_orders.append(record)
    return record
