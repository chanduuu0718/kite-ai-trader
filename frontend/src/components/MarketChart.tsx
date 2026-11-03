import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ColorType,
  CrosshairMode,
  createChart,
  LineSeries,
  type UTCTimestamp,
} from 'lightweight-charts';
import { RefreshCw } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type PricePoint = { time: number; timestamp_ist: string; price: number };
type IntradayResponse = {
  symbol: string;
  source: string;
  data_mode: string;
  interval: string;
  delay_note: string;
  latest_timestamp_ist: string;
  latest_price: number;
  points: PricePoint[];
  fetched_at_ist: string;
  refresh_interval_seconds: number;
};
type ProviderStatus = {
  configured: boolean;
  message: string;
  provider: string;
  data_mode: string;
};

type Props = {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  symbols: string[];
};

export default function MarketChart({ symbol, onSymbolChange, symbols }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const seriesRef = useRef<any>(null);
  const [provider, setProvider] = useState<ProviderStatus | null>(null);
  const [chartData, setChartData] = useState<IntradayResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      height: 340,
      layout: {
        attributionLogo: true,
        background: { type: ColorType.Solid, color: '#101827' },
        textColor: '#94a3b8',
        fontFamily: 'DM Mono, monospace',
      },
      grid: {
        vertLines: { color: '#1d2a3d' },
        horzLines: { color: '#1d2a3d' },
      },
      rightPriceScale: { borderColor: '#2a3b55' },
      timeScale: {
        borderColor: '#2a3b55',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        priceFormatter: (price: number) => '₹' + price.toLocaleString('en-IN', { maximumFractionDigits: 2 }),
      },
    });
    const line = chart.addSeries(LineSeries, {
      color: '#55d6b3',
      lineWidth: 2,
      priceLineVisible: true,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
    });
    seriesRef.current = line;
    return () => {
      seriesRef.current = null;
      chart.remove();
    };
  }, []);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError('');
      setChartData(null);
      try {
        const statusResponse = await fetch(API + '/api/data/status');
        if (!statusResponse.ok) throw new Error('Could not read the data-provider status.');
        const status = (await statusResponse.json()) as ProviderStatus;
        if (!active) return;
        setProvider(status);
        if (!status.configured) {
          setChartData(null);
          return;
        }
        const response = await fetch(API + '/api/market/' + encodeURIComponent(symbol) + '/intraday');
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'The delayed market-data request failed.');
        if (!active) return;
        setChartData(payload as IntradayResponse);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Could not load chart data.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; };
  }, [symbol, refreshKey]);

  useEffect(() => {
    if (!seriesRef.current || !chartData?.points?.length) return;
    const points = chartData.points.map((point) => ({
      time: point.time as UTCTimestamp,
      value: point.price,
    }));
    seriesRef.current.setData(points);
  }, [chartData]);

  useEffect(() => {
    if (!provider?.configured) return;
    const timer = window.setInterval(() => setRefreshKey((value) => value + 1), 60_000);
    return () => window.clearInterval(timer);
  }, [provider?.configured]);

  const latestTime = useMemo(() => {
    if (!chartData?.latest_timestamp_ist) return '—';
    const parsed = new Date(chartData.latest_timestamp_ist);
    return Number.isNaN(parsed.getTime())
      ? chartData.latest_timestamp_ist
      : new Intl.DateTimeFormat('en-IN', {
          timeZone: 'Asia/Kolkata',
          dateStyle: 'medium',
          timeStyle: 'short',
        }).format(parsed);
  }, [chartData]);

  return (
    <section className="chartPanel">
      <div className="chartHeader">
        <div>
          <div className="chartEyebrow">NSE CASH · DELAYED INTRADAY</div>
          <h2>Market chart</h2>
          <p>Provider-stamped 5-minute price observations · India time</p>
        </div>
        <div className="chartControls">
          <select aria-label="Chart symbol" value={symbol} onChange={(event) => onSymbolChange(event.target.value)}>
            {symbols.map((item) => <option value={item} key={item}>{item}</option>)}
          </select>
          <button className="refresh" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading}>
            <RefreshCw className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </div>
      <div className="chartMeta">
        <span className="delayedBadge">DELAYED DATA</span>
        <span>{chartData ? chartData.source : (provider?.provider || 'Indian API')}</span>
        <span>Latest observation: {latestTime}</span>
        {chartData && <strong>₹{chartData.latest_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>}
      </div>
      <div className="chartCanvas" ref={containerRef} />
      {error && <div className="chartMessage chartError">{error}</div>}
      {!error && !provider?.configured && (
        <div className="chartMessage">
          <strong>Connect the free delayed-data source</strong>
          <p>{provider?.message || 'Checking provider configuration…'}</p>
          <p>1. Create a free developer key at <a href="https://indianapi.in/indian-stock-market" target="_blank" rel="noreferrer">Indian API</a> (this is not a broker account).</p>
          <p>2. Add it to backend/.env as <code>INDIAN_API_KEY=your_key</code>, restart the backend, then refresh this chart.</p>
        </div>
      )}
      {!error && provider?.configured && !chartData && (
        <div className="chartMessage">{loading ? 'Loading delayed observations…' : 'No intraday observations returned for this symbol today.'}</div>
      )}
      {chartData && <div className="chartFootnote">{chartData.delay_note} Data is a price line, not OHLC candles. The chart does not fabricate open/high/low values.</div>}
    </section>
  );
}
