from fastapi.testclient import TestClient
from app.main import app
from app.market import candles_for
from app.indicators import calculate_indicators,generate_signal
client=TestClient(app)
def test_health(): assert client.get('/health').json()['status']=='ok'
def test_indicators():
 m=calculate_indicators('RELIANCE',candles_for('RELIANCE')); assert 0<=m['rsi']<=100; assert generate_signal(m)['action'] in {'BUY','SELL','WAIT'}
def test_signals(): assert len(client.get('/api/analysis/signals').json())>=10
def test_paper():
 r=client.post('/api/paper/trades',json={'symbol':'RELIANCE','side':'BUY','quantity':1,'reference_price':1450}); assert r.status_code==200; assert r.json()['status']=='SIMULATED'
