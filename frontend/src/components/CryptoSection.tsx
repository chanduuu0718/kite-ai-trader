import { useEffect, useRef, useState } from 'react';
import { Bitcoin, RefreshCw, ExternalLink, Newspaper } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
type Coin = { id: string; symbol: string; name: string; price: number; change_24h: number; market_cap: number; volume_24h: number; high_24h: number; low_24h: number; last_updated: string };
type News = { title: string; link: string; published: string; source: string };

export default function CryptoSection() {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [alerts, setAlerts] = useState<string[]>([]);
  const previousPrices = useRef<Record<string, number>>({});
  const knownNews = useRef<Set<string>>(new Set());

  async function refresh() {
    setLoading(true); setError('');
    try {
      const [priceResponse, newsResponse] = await Promise.all([
        fetch(API + '/api/crypto/market'),
        fetch(API + '/api/crypto/news'),
      ]);
      if (!priceResponse.ok) throw new Error('CoinGecko price feed unavailable');
      const market = await priceResponse.json();
      const nextAlerts: string[] = [];
      for (const coin of market as Coin[]) {
        const previous = previousPrices.current[coin.id];
        if (previous && coin.price) {
          const move = ((coin.price - previous) / previous) * 100;
          if (Math.abs(move) >= 0.5) nextAlerts.push(coin.symbol + ': ' + (move >= 0 ? '+' : '') + move.toFixed(2) + '% since last refresh');
        }
        previousPrices.current[coin.id] = coin.price;
      }
      setCoins(market);
      if (newsResponse.ok) {
        const headlines = await newsResponse.json() as News[];
        const fresh = headlines.filter(item => !knownNews.current.has(item.link));
        if (knownNews.current.size && fresh.length) nextAlerts.push(fresh.length + ' new crypto headline(s) from CoinDesk');
        headlines.forEach(item => knownNews.current.add(item.link));
        setNews(headlines);
      } else setNews([]);
      if (nextAlerts.length) setAlerts(prev => [...nextAlerts, ...prev].slice(0, 8));
    } catch (e) { setError(e instanceof Error ? e.message : 'Crypto data unavailable'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 60_000); return () => window.clearInterval(timer); }, []);

  return <section className="cryptoSection">
    <div className="cryptoHeading">
      <div><div className="chartEyebrow">DIGITAL ASSETS / 24×7</div><h2>Crypto market</h2><p>Separate research area for Bitcoin and Ethereum · INR prices</p></div>
      <button className="refresh" onClick={() => void refresh()}><RefreshCw className={loading ? 'spin' : ''}/> Refresh crypto</button>
    </div>
    {error && <div className="error">{error}</div>}
    <div className="cryptoLayout">
    <div className="cryptoCards">
      {coins.map(coin => <article className="cryptoCard" key={coin.id}>
        <div className="coinIdentity"><span className={'coinIcon ' + coin.symbol.toLowerCase()}><Bitcoin/></span><div><b>{coin.name}</b><small>{coin.symbol} · INR</small></div></div>
        <strong>₹{coin.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>
        <span className={coin.change_24h >= 0 ? 'positive' : 'negative'}>{coin.change_24h >= 0 ? '+' : ''}{coin.change_24h.toFixed(2)}% <small>24h</small></span>
        <div className="coinStats"><span>24h High <b>₹{coin.high_24h.toLocaleString('en-IN',{maximumFractionDigits:2})}</b></span><span>24h Low <b>₹{coin.low_24h.toLocaleString('en-IN',{maximumFractionDigits:2})}</b></span><span>24h Volume <b>₹{(coin.volume_24h/1e7).toFixed(2)} Cr</b></span><span>Market Cap <b>₹{(coin.market_cap/1e7).toFixed(0)} Cr</b></span></div><small className="coinUpdated">Provider updated: {coin.last_updated ? new Date(coin.last_updated).toLocaleTimeString('en-IN') : '—'}</small>
      </article>)}
      {!coins.length && !error && <div className="empty">Loading BTC and ETH market data…</div>}
    </div>
    <aside className="cryptoAlertBox">
      <div className="alertBoxHead"><span className="alertPulse"/> <div><b>Crypto alerts</b><small>Updates detected by KITE</small></div><span className="liveTag">AUTO</span></div>
      {alerts.map((alert, i) => <div className="cryptoAlert" key={alert + i}><span>●</span>{alert}</div>)}
      {!alerts.length && <p className="alertEmpty">No notable price moves or new headlines detected yet. Alerts appear after refresh.</p>}
      <button className="clearAlerts" onClick={() => setAlerts([])}>Clear alerts</button>
    </aside>
    </div>
    <div className="cryptoNews">
      <div className="sectionHead"><div><h2><Newspaper/> Crypto news & context</h2><p>Latest headlines with source links; use news as context, not a trade signal by itself.</p></div><span className="liveTag">COINDESK RSS</span></div>
      {news.map((item, i) => <a className="cryptoNewsItem" href={item.link} target="_blank" rel="noreferrer" key={item.link}>
        <span className="newsNumber">{String(i + 1).padStart(2, '0')}</span><div><b>{item.title}</b><small>{item.source} · {item.published}</small></div><ExternalLink/>
      </a>)}
      {!news.length && <div className="chartMessage">News feed is loading or temporarily unavailable. Headlines will appear here when the backend RSS endpoint is reachable.</div>}
      <div className="cryptoDisclaimer">Prices refresh about every 60 seconds (near-live, not exchange tick streaming); news refreshes on the same cycle and may be delayed. AI trade analysis is not connected yet; no automatic orders are placed.</div>
    </div>
  </section>;
}
