import { useEffect, useState } from 'react';
import { Bitcoin, RefreshCw, ExternalLink, Newspaper } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
type Coin = { id: string; symbol: string; name: string; price: number; change: number };
type News = { title: string; link: string; published: string; source: string };

export default function CryptoSection() {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [news, setNews] = useState<News[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function refresh() {
    setLoading(true); setError('');
    try {
      const [priceResponse, newsResponse] = await Promise.all([
        fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=inr&include_24hr_change=true'),
        fetch(API + '/api/crypto/news'),
      ]);
      if (!priceResponse.ok) throw new Error('CoinGecko price feed unavailable');
      const prices = await priceResponse.json();
      setCoins([
        { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', price: prices.bitcoin.inr, change: prices.bitcoin.inr_24h_change },
        { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', price: prices.ethereum.inr, change: prices.ethereum.inr_24h_change },
      ]);
      if (newsResponse.ok) setNews(await newsResponse.json());
      else setNews([]);
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
    <div className="cryptoCards">
      {coins.map(coin => <article className="cryptoCard" key={coin.id}>
        <div className="coinIdentity"><span className={'coinIcon ' + coin.symbol.toLowerCase()}><Bitcoin/></span><div><b>{coin.name}</b><small>{coin.symbol} · INR</small></div></div>
        <strong>₹{coin.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong>
        <span className={coin.change >= 0 ? 'positive' : 'negative'}>{coin.change >= 0 ? '+' : ''}{coin.change.toFixed(2)}% <small>24h</small></span>
        <p>Market price from CoinGecko. Crypto trades 24/7; values refresh about every minute.</p>
      </article>)}
      {!coins.length && !error && <div className="empty">Loading BTC and ETH market data…</div>}
    </div>
    <div className="cryptoNews">
      <div className="sectionHead"><div><h2><Newspaper/> Crypto news & context</h2><p>Latest headlines with source links; use news as context, not a trade signal by itself.</p></div><span className="liveTag">COINDESK RSS</span></div>
      {news.map((item, i) => <a className="cryptoNewsItem" href={item.link} target="_blank" rel="noreferrer" key={item.link}>
        <span className="newsNumber">{String(i + 1).padStart(2, '0')}</span><div><b>{item.title}</b><small>{item.source} · {item.published}</small></div><ExternalLink/>
      </a>)}
      {!news.length && <div className="chartMessage">News feed is loading or temporarily unavailable. Headlines will appear here when the backend RSS endpoint is reachable.</div>}
      <div className="cryptoDisclaimer">Prices/news are external feeds and can be delayed or unavailable. AI trade analysis is not connected yet; no automatic orders are placed.</div>
    </div>
  </section>;
}
