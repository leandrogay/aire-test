'use client';

import { useEffect, useState } from 'react';

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sales?limit=50`);
        if (!res.ok) throw new Error('Failed to load dashboard data');
        setData(await res.json());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <main className="p-8 text-gray-500">Loading dashboard...</main>;
  if (error) return <main className="p-8 text-red-600">{error}</main>;

  const { stats, records } = data;

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Sales Dashboard</h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Total Orders</p>
            <p className="text-2xl font-semibold text-gray-900">{stats.total_orders}</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <p className="text-sm text-gray-500">Total Revenue</p>
            <p className="text-2xl font-semibold text-gray-900">${stats.total_revenue.toLocaleString()}</p>
          </div>
        </div>

        {stats.by_platform?.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-5 mb-8">
            <p className="text-sm font-medium text-gray-700 mb-3">Revenue by Platform</p>
            <div className="space-y-2">
              {stats.by_platform.map((p) => {
                const maxRevenue = Math.max(...stats.by_platform.map((x) => x.revenue));
                const width = maxRevenue ? (p.revenue / maxRevenue) * 100 : 0;
                return (
                  <div key={p.platform}>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>{p.platform}</span>
                      <span>${p.revenue.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded h-2">
                      <div className="bg-blue-500 h-2 rounded" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
          <p className="text-sm font-medium text-gray-700 p-5 pb-0">Recently Ingested Records</p>
          <table className="w-full text-sm mt-3">
            <thead>
              <tr className="text-left text-gray-500 border-t border-gray-100">
                <th className="px-5 py-2">Order ID</th>
                <th className="px-5 py-2">Date</th>
                <th className="px-5 py-2">Platform</th>
                <th className="px-5 py-2">Product</th>
                <th className="px-5 py-2">Qty</th>
                <th className="px-5 py-2">Total</th>
                <th className="px-5 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="px-5 py-2">{r.order_id}</td>
                  <td className="px-5 py-2">{r.order_date}</td>
                  <td className="px-5 py-2">{r.platform}</td>
                  <td className="px-5 py-2">{r.product_name}</td>
                  <td className="px-5 py-2">{r.quantity}</td>
                  <td className="px-5 py-2">{r.currency} {r.total_amount}</td>
                  <td className="px-5 py-2">{r.status}</td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-6 text-center text-gray-400">No records ingested yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}