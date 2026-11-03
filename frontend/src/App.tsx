import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  CandlestickChart,
  CircleDollarSign,
  Gauge,
  RefreshCw,
  ShieldCheck,
  Wallet,
} from 'lucide-react';
import LiveMarketSection from './components/LiveMarketSection';
import CryptoSection from './components/CryptoSection';
import MarketNews from './components/MarketNews';

const DEFAULT_SYMBOLS = [
  'RELIANCE', 'HDFCBANK', 'ICICIBANK', 'INFY', 'TCS', 'SBIN',
  'BHARTIARTL', 'LT', 'ITC', 'AXISBANK', 'TATAMOTORS', 'MARUTI',
];
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type Row = {
  symbol: string;
  name: string;
  ltp: number;
  change_pct: number;
  rsi: number;
  ema_fast: number;
  ema_slow: number;
  vwap: number;
  volume_ratio: number;
  action: string;
  score: number;
  rationale: string[];
};
type Trade = {
  id: string;
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  status: string;
  created_at: string;
};

export default function App() {
  const [rows, setRows] = useState<Row[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState('RELIANCE');
  const [qty, setQty] = useState(1);
  const [side, setSide] = useState('BUY');
  const [activeNav, setActiveNav] = useState('market');
  function navigate(target: string) { setActiveNav(target); window.scrollTo({ top: 0, behavior: 'smooth' }); }

  async function refresh() {
    setBusy(true);
    setError('');
    try {
      const [signalsResponse, tradesResponse] = await Promise.all([
        fetch(API + '/api/analysis/signals'),
        fetch(API + '/api/paper/trades'),
      ]);
      if (!signalsResponse.ok || !tradesResponse.ok) {
        throw new Error('API failed. Is the backend running on port 8000?');
      }
      setRows(await signalsResponse.json());
      setTrades(await tradesResponse.json());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not connect');
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 15_000);
    return () => window.clearInterval(id);
  }, []);

  const counts = useMemo(() => ({
    buy: rows.filter((row) => row.action === 'BUY').length,
    sell: rows.filter((row) => row.action === 'SELL').length,
    wait: rows.filter((row) => row.action === 'WAIT').length,
  }), [rows]);

  const symbols = rows.length ? rows.map((row) => row.symbol) : DEFAULT_SYMBOLS;

  async function paper() {
    const row = rows.find((item) => item.symbol === selected);
    if (!row) return;
    const response = await fetch(API + '/api/paper/trades', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: selected,
        side,
        quantity: qty,
        reference_price: row.ltp,
      }),
    });
    if (!response.ok) {
      setError('Paper trade failed');
      return;
    }
    await refresh();
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandIcon"><CandlestickChart /></div>
          <div><b>KITE AI</b><small>TRADER TERMINAL</small></div>
        </div>
        <button className={'nav '+(activeNav==='market'?'active':'')} onClick={()=>navigate('market')}><Activity /> India Market</button>
        <button className={'nav '+(activeNav==='news'?'active':'')} onClick={()=>navigate('news')}><Activity /> Market News</button>
        <button className={'nav '+(activeNav==='signals'?'active':'')} onClick={()=>navigate('signals')}><BrainCircuit /> AI Signals</button>
        <button className={'nav '+(activeNav==='crypto'?'active':'')} onClick={()=>navigate('crypto')}><CircleDollarSign /> Crypto (BTC / ETH)</button>
        <button className={'nav '+(activeNav==='portfolio'?'active':'')} onClick={()=>navigate('portfolio')}><Wallet /> Paper Portfolio</button>
        <button className={'nav '+(activeNav==='risk'?'active':'')} onClick={()=>navigate('risk')}><ShieldCheck /> Risk Controls</button>
        <div className="sideNote">
          <span className="pulse" /> READ-ONLY RESEARCH
          <small>Delayed chart data · Manual trading only</small>
        </div>
      </aside>

      <section className="content">
        <header>
          <div>
            <div className="eyebrow">INDIAN EQUITY MARKETS / INTRADAY</div>
            <h1>{activeNav === 'market' ? 'Indian Market Dashboard' : activeNav === 'crypto' ? 'Crypto Dashboard' : activeNav === 'news' ? 'NSE / BSE Market News' : activeNav === 'signals' ? 'AI Signals' : activeNav === 'portfolio' ? 'Paper Portfolio' : 'Risk Controls'}</h1>
            <p>Current price cards · Market information · Manual research</p>
          </div>
        </header>

        {activeNav === 'market' && <div><div className="marketIntro"><div className="eyebrow">NSE / BSE · INDIA</div><h2>Indian market dashboard</h2><p>Stocks and delayed quote cards. No charts unless an AI setup is triggered.</p><div className="marketQuick"><span>NSE · National Stock Exchange</span><span>BSE · Bombay Stock Exchange</span><span>Cash market · Intraday research</span></div><LiveMarketSection /></div>}
        {activeNav === 'news' && <MarketNews />}
        {activeNav === 'signals' && <section className="pagePanel"><div className="eyebrow">KITE INTELLIGENCE</div><h2>AI signals</h2><p>Signals will appear here after verified intraday candle data and technical strategy are connected. No demo BUY/SELL advice is shown.</p><div className="empty">No verified signal available.</div></section>}
        {activeNav === 'crypto' && <CryptoSection />}
        {activeNav === 'portfolio' && <section className="pagePanel"><div className="sectionHead"><div><h2>Paper portfolio</h2><p>Simulated trades only · resets on backend restart</p></div></div><div className="tradeList">{trades.slice(0,5).map(trade=><div className="trade" key={trade.id}><b>{trade.symbol}</b><span>{trade.side} · {trade.quantity} qty</span><span>₹{trade.entry_price.toFixed(2)}</span><em>SIMULATED</em></div>)}{!trades.length&&<div className="empty">No simulated trades yet.</div>}</div></section>}
        {activeNav === 'risk' && <section className="pagePanel"><div className="eyebrow">SAFETY</div><h2>Risk controls</h2><p>KITE is read-only research. No broker orders are sent.</p><ul><li>Use a predefined stop-loss for every trade.</li><li>Limit risk per trade and daily loss.</li><li>Confirm all signals manually; data may be delayed.</li></ul></section>}
        <footer>KITE AI TRADER · MVP 0.2.0 <span>Research software · Not investment advice</span></footer>
      </section>
    </main>
  );
}

function Stat({ icon, label, value, tone }: {
  icon: React.ReactNode;
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className="stat">
      <div className={'statIcon ' + tone}>{icon}</div>
      <div><small>{label}</small><b>{value}</b></div>
    </div>
  );
}
