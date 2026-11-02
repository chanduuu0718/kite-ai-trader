from datetime import datetime,timezone
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .market import WATCHLIST,candles_for
from .indicators import calculate_indicators,generate_signal
from .schemas import PaperTradeRequest
from .paper import create_trade,list_trades
app=FastAPI(title=settings.app_name,version="0.1.0",description="Indian intraday research API; demo data is synthetic")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.get("/health")
def health(): return {"status":"ok","mode":"DEMO_SYNTHETIC","time":datetime.now(timezone.utc)}
@app.get("/api/market/overview")
def overview(): return {"market":"INDIA","data_mode":"SYNTHETIC_DEMO","indices":[{"symbol":x,"value":0,"change_pct":0,"status":"DEMO"} for x in ["NIFTY 50","SENSEX","BANK NIFTY"]]}
@app.get("/api/market/watchlist")
def watchlist(): return WATCHLIST
@app.get("/api/market/{symbol}/candles")
def get_candles(symbol:str,count:int=90):
 try: return [x.model_dump() for x in candles_for(symbol.upper(),max(25,min(count,300)))]
 except KeyError: raise HTTPException(404,"Symbol not in demo watchlist")
@app.get("/api/analysis/signals")
def signals():
 out=[]
 for x in WATCHLIST:
  m=calculate_indicators(x["symbol"],candles_for(x["symbol"])); out.append({**m,**generate_signal(m),"name":x["name"]})
 return out
@app.get("/api/paper/trades")
def trades(): return list_trades()
@app.post("/api/paper/trades")
def new_trade(req:PaperTradeRequest):
 if req.symbol.upper() not in {x["symbol"] for x in WATCHLIST}: raise HTTPException(404,"Symbol not in watchlist")
 try: return create_trade(req.symbol,req.side,req.quantity,req.reference_price)
 except ValueError as e: raise HTTPException(422,str(e))
