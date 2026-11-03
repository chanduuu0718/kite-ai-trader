from datetime import datetime, timedelta, timezone
import math, random
from .schemas import Candle
WATCHLIST = [
 {"symbol":"RELIANCE","name":"Reliance Industries","exchange":"NSE"},{"symbol":"HDFCBANK","name":"HDFC Bank","exchange":"NSE"},{"symbol":"ICICIBANK","name":"ICICI Bank","exchange":"NSE"},{"symbol":"INFY","name":"Infosys","exchange":"NSE"},{"symbol":"TCS","name":"Tata Consultancy Services","exchange":"NSE"},{"symbol":"SBIN","name":"State Bank of India","exchange":"NSE"},{"symbol":"BHARTIARTL","name":"Bharti Airtel","exchange":"NSE"},{"symbol":"LT","name":"Larsen & Toubro","exchange":"NSE"},{"symbol":"ITC","name":"ITC","exchange":"NSE"},{"symbol":"AXISBANK","name":"Axis Bank","exchange":"NSE"},{"symbol":"TATAMOTORS","name":"Tata Motors","exchange":"NSE"},{"symbol":"MARUTI","name":"Maruti Suzuki","exchange":"NSE"}]
BASE={"RELIANCE":1450,"HDFCBANK":980,"ICICIBANK":1380,"INFY":1520,"TCS":3200,"SBIN":910,"BHARTIARTL":1900,"LT":3650,"ITC":410,"AXISBANK":1180,"TATAMOTORS":690,"MARUTI":12800}
def candles_for(symbol,count=90):
 if symbol not in BASE: raise KeyError(symbol)
 rng=random.Random(symbol); price=BASE[symbol]; now=datetime.now(timezone.utc).replace(second=0,microsecond=0); out=[]
 for i in range(count,0,-1):
  drift=math.sin(i/8)*.001+rng.uniform(-.004,.004); op=price; close=max(1,op*(1+drift)); hi=max(op,close)*(1+rng.uniform(.0002,.002)); lo=min(op,close)*(1-rng.uniform(.0002,.002)); vol=rng.randint(50000,500000)
  out.append(Candle(timestamp=now-timedelta(minutes=5*i),open=round(op,2),high=round(hi,2),low=round(lo,2),close=round(close,2),volume=vol)); price=close
 return out
