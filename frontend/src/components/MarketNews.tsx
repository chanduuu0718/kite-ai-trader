import { useEffect,useState } from 'react';
import { RefreshCw,ExternalLink,Newspaper,Bitcoin,Activity } from 'lucide-react';
const API=import.meta.env.VITE_API_URL||'http://localhost:8000';
type News={title:string;link:string;published:string;source:string};
type Tab='stocks'|'crypto';\ntype Mood='ALL'|'BULLISH'|'BEARISH'|'NEUTRAL';\nfunction classify(title:string):Mood{const t=title.toLowerCase();if(/surge|rally|jump|gain|record high|upgrade|profit rises|beats estimates|buyback|dividend|inflow|bullish|breakout/.test(t))return 'BULLISH';if(/crash|fall|drop|plunge|decline|selloff|loss widens|misses estimates|downgrade|outflow|bearish|probe|fraud|ban/.test(t))return 'BEARISH';return 'NEUTRAL'}
export default function MarketNews(){
 const [tab,setTab]=useState<Tab>('stocks');const [mood,setMood]=useState<Mood>('ALL');const [stocks,setStocks]=useState<News[]>([]);const [coins,setCoins]=useState<News[]>([]);
 const [error,setError]=useState('');const [loading,setLoading]=useState(false);const [updated,setUpdated]=useState('');
 async function refresh(){setLoading(true);setError('');try{
  const [s,c]=await Promise.all([fetch(API+'/api/market/news'),fetch(API+'/api/crypto/news')]);
  if(!s.ok&&!c.ok)throw new Error('Both news feeds are unavailable. Check backend and internet connection.');
  if(s.ok){const d=await s.json();setStocks(d.items||[])}else setStocks([]);
  if(c.ok)setCoins(await c.json());else setCoins([]);
  setUpdated(new Date().toLocaleTimeString('en-IN'));
 }catch(e){setError(e instanceof Error?e.message:'News feed unavailable')}finally{setLoading(false)}}
 useEffect(()=>{void refresh();const t=window.setInterval(()=>void refresh(),300000);return()=>window.clearInterval(t)},[]);
 const items=(tab==='stocks'?stocks:coins).filter(n=>mood==='ALL'||classify(n.title)===mood);
 return <section className="pagePanel marketNews">
 <div className="sectionHead"><div><div className="eyebrow">NEWS DESK · INDIA + GLOBAL CRYPTO</div><h2><Newspaper/> Market News</h2><p>Latest headlines · auto-refresh 5 min {updated&&'· updated '+updated}</p></div><button className="refresh" onClick={()=>void refresh()}><RefreshCw className={loading?'spin':''}/> Refresh all</button></div>
 <div className="newsTabs"><button className={tab==='stocks'?'selected':''} onClick={()=>setTab('stocks')}><Activity/> NSE / BSE Stocks <span>{stocks.length}</span></button><button className={tab==='crypto'?'selected':''} onClick={()=>setTab('crypto')}><Bitcoin/> Crypto <span>{coins.length}</span></button></div>
 <div className="newsMoodFilters">{(['ALL','BULLISH','BEARISH','NEUTRAL'] as Mood[]).map(m=><button key={m} className={mood===m?'selected':''} onClick={()=>setMood(m)}>{m==='ALL'?'All headlines':m==='BULLISH'?'Potentially positive':m==='BEARISH'?'Potentially negative':'Neutral / unclear'}</button>)}</div>\n <div className="newsFeedInfo">{tab==='stocks'?'India equities · NSE, BSE, NIFTY, SENSEX':'Digital assets · Bitcoin, Ethereum and crypto markets'} · {tab==='stocks'?'Google News RSS':'CoinDesk RSS'}</div>
 {error&&<div className="error">{error}</div>}
 {items.map((n,i)=><article className="marketNewsItem" key={n.link||i}><div className="newsNum">{String(i+1).padStart(2,'0')}</div><div className="newsBody"><a href={n.link} target="_blank" rel="noreferrer">{n.title}</a><small>{n.source} · {n.published} · <span className={'headlineMood '+classify(n.title).toLowerCase()}>{classify(n.title)==='BULLISH'?'Potentially positive':classify(n.title)==='BEARISH'?'Potentially negative':'Neutral / unclear'}</span></small></div><a className="newsOpen" href={n.link} target="_blank" rel="noreferrer" aria-label="Open news"><ExternalLink/></a></article>)}
 {!items.length&&!error&&<div className="empty">{loading?'Loading headlines…':'No headlines returned by provider.'}</div>}
 </section>}
