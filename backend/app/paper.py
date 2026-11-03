from datetime import datetime,timezone
from uuid import uuid4
from .schemas import PaperTrade
_trades=[]
def create_trade(symbol,side,quantity,price):
 side=side.upper()
 if side not in {"BUY","SELL"}: raise ValueError("side must be BUY or SELL")
 t=PaperTrade(id=str(uuid4()),symbol=symbol.upper(),side=side,quantity=quantity,entry_price=round(price,2),status="SIMULATED",created_at=datetime.now(timezone.utc)); _trades.insert(0,t); return t
def list_trades(): return list(_trades)
