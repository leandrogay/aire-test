'use client';

import { useEffect, useState } from 'react';

const METRICS = [
  { value: 'value', label: 'Sales Value' },
  { value: 'volume', label: 'Sales Volume' },
];

const ORDER_OPTIONS = [
  { value: 'desc', label: 'Highest first' },
  { value: 'asc', label: 'Lowest first' },
];

function toggleButtonClass(isActive) {
  return `px-3 py-1 text-xs rounded-full border transition-colors ${
    isActive
      ? 'bg-blue-500 text-white border-blue-500'
      : 'bg-white text-gray-600 border-gray-300'
  }`;
}

export default function skuRanking() {
  const [metric, setMetric] = useState('value');
  const [order, setOrder] = useState('desc');
  const [skus, setSkus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchRanking() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/sales/skus?metric=${metric}&order=${order}`
        );
        if (!res.ok) throw new Error('Failed to load SKU ranking');
        const data = await res.json();
        if (!cancelled) setSkus(data.skus);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchRanking();
    return () => {
      cancelled = true;
    };
  }, [metric, order]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 mb-8">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p className="text-sm font-medium text-gray-700">SKU Performance Ranking</p>

        <div className="flex flex-wrap gap-2">
          {METRICS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => setMetric(m.value)}
              className={toggleButtonClass(metric === m.value)}
            >
              {m.label}
            </button>
          ))}

          {ORDER_OPTIONS.map((o) => (
            <button
              key={o.value}
              type="button"
              onClick={() => setOrder(o.value)}
              className={toggleButtonClass(order === o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-gray-500 text-sm">Loading SKU ranking...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && skus.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-6">No SKU data available yet.</p>
      )}

      {!loading && !error && skus.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-t border-gray-100">
              <th className="px-3 py-2">Rank</th>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Product</th>
              <th className="px-3 py-2">Volume</th>
              <th className="px-3 py-2">Value</th>
            </tr>
          </thead>
          <tbody>
            {skus.map((s) => (
              <tr key={s.sku} className="border-t border-gray-100 text-gray-700">
                <td className="px-3 py-2">{s.rank}</td>
                <td className="px-3 py-2">{s.sku}</td>
                <td className="px-3 py-2">{s.product_name}</td>
                <td className="px-3 py-2">{s.volume}</td>
                <td className="px-3 py-2">${s.value.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
