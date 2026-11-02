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
        <div className="nav active"><Activity /> Market overview</div>
        <div className="nav"><BrainCircuit /> AI signals</div>
        <div className="nav"><CircleDollarSign /> Crypto (BTC / ETH)</div>
        <div className="nav"><Wallet /> Paper portfolio</div>
        <div className="nav"><ShieldCheck /> Risk controls</div>
        <div className="sideNote">
          <span className="pulse" /> READ-ONLY RESEARCH
          <small>Delayed chart data · Manual trading only</small>
        </div>
      </aside>

      <section className="content">
        <header>
          <div>
            <div className="eyebrow">INDIAN EQUITY MARKETS / INTRADAY</div>
            <h1>Market overview</h1>
            <p>Independent charts and explainable market research</p>
          </div>
        </header>

        <LiveMarketSection />

        <CryptoSection />

        <div className="sectionHead">
          <div><h2>Recent paper trades</h2><p>In-memory demo ledger resets when backend restarts.</p></div>
        </div>
        <div className="tradeList">
          {trades.slice(0, 5).map((trade) => (
            <div className="trade" key={trade.id}>
              <b>{trade.symbol}</b>
              <span>{trade.side} · {trade.quantity} qty</span>
              <span>₹{trade.entry_price.toFixed(2)}</span>
              <em>SIMULATED</em>
            </div>
          ))}
          {!trades.length && <div className="empty">No simulated trades yet.</div>}
        </div>
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
