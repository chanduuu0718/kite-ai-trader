import pandas as pd
import numpy as np
def calculate_indicators(symbol,candles):
 if len(candles)<25: raise ValueError("At least 25 candles required")
 f=pd.DataFrame([c.model_dump() for c in candles]); c=f.close.astype(float); v=f.volume.astype(float); d=c.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean().replace(0,np.nan); rs=gain/loss; rv=100-(100/(1+rs)); rsi=float(rv.iloc[-1]) if pd.notna(rv.iloc[-1]) else 50
 ef=float(c.ewm(span=9,adjust=False).mean().iloc[-1]); es=float(c.ewm(span=21,adjust=False).mean().iloc[-1]); typ=(f.high+f.low+c)/3; vwap=float((typ*v).sum()/v.sum()) if v.sum() else float(c.iloc[-1]); av=float(v.tail(20).mean()) or 1
 return {"symbol":symbol,"ltp":round(float(c.iloc[-1]),2),"change_pct":round((float(c.iloc[-1])/float(c.iloc[-2])-1)*100,2),"rsi":round(rsi,2),"ema_fast":round(ef,2),"ema_slow":round(es,2),"vwap":round(vwap,2),"volume_ratio":round(float(v.iloc[-1])/av,2)}
def generate_signal(m):
 score=0; why=[]
 if m["ema_fast"]>m["ema_slow"]: score+=1; why.append("9 EMA above 21 EMA")
 else: score-=1; why.append("9 EMA below 21 EMA")
 if m["ltp"]>m["vwap"]: score+=1; why.append("Price above VWAP proxy")
 else: score-=1; why.append("Price below VWAP proxy")
 if 50<=m["rsi"]<=68: score+=1; why.append("RSI positive momentum zone")
 elif m["rsi"]<35: score-=1; why.append("RSI weak; oversold is not a reversal")
 elif m["rsi"]>75: score-=1; why.append("RSI extended")
 if m["volume_ratio"]>=1.5: score+=1 if m["change_pct"]>0 else -1; why.append("Volume >= 1.5x recent average")
 return {"symbol":m["symbol"],"action":"BUY" if score>=3 else "SELL" if score<=-3 else "WAIT","score":score,"rationale":why}
