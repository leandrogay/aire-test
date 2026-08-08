// analytics.js
// Computes summary metrics for a parsed sheet. Runs over the FULL row set
// (not the display-capped slice), so totals are correct for large files.

// Find the first column whose header matches any of the given keywords.
// Returns the column index, or -1 if none match.
function findColumn(headers, keywords) {
  const lower = headers.map((h) => String(h).toLowerCase());
  for (let i = 0; i < lower.length; i++) {
    if (keywords.some((k) => lower[i].includes(k))) return i;
  }
  return -1;
}

// Coerce a cell to a number. Strips currency symbols, commas, spaces, %.
function toNumber(v) {
  if (typeof v === "number") return v;
  if (v == null || v === "") return null;
  const n = parseFloat(String(v).replace(/[^0-9.\-]/g, ""));
  return Number.isFinite(n) ? n : null;
}

// Parse a value into a YYYY-MM month key, or null if it isn't a date.
function monthKey(v) {
  if (v == null || v === "") return null;
  const d = new Date(v);
  if (isNaN(d.getTime())) return null;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function computeAnalytics(headers, rows) {
  const revenueCol = findColumn(headers, ["net total", "net revenue", "revenue", "amount", "net", "total"]);
  const costCol = findColumn(headers, ["cost", "cogs"]);
  const dateCol = findColumn(headers, ["order date", "date", "timestamp"]);
  const qtyCol = findColumn(headers, ["qty", "quantity", "units"]);
  const categoryCol = findColumn(headers, ["category", "type", "segment"]);
  const productCol = findColumn(headers, ["product", "item", "sku name", "name"]);
  const statusCol = findColumn(headers, ["status", "state"]);

  const detected = {
    revenue: revenueCol >= 0 ? headers[revenueCol] : null,
    cost: costCol >= 0 ? headers[costCol] : null,
    date: dateCol >= 0 ? headers[dateCol] : null,
    quantity: qtyCol >= 0 ? headers[qtyCol] : null,
    category: categoryCol >= 0 ? headers[categoryCol] : null,
    product: productCol >= 0 ? headers[productCol] : null,
    status: statusCol >= 0 ? headers[statusCol] : null,
  };

  let totalRevenue = 0;
  let totalCost = 0;
  let totalUnits = 0;
  let revenueRows = 0;

  const byMonth = {};     // "2026-01" -> { revenue, cost, orders, units }
  const byCategory = {};  // category -> { revenue, orders, units }
  const byStatus = {};    // status -> count
  const byProduct = {};   // product -> { revenue, units }

  for (const row of rows) {
    const rev = revenueCol >= 0 ? toNumber(row[revenueCol]) : null;
    const cost = costCol >= 0 ? toNumber(row[costCol]) : null;
    const qty = qtyCol >= 0 ? toNumber(row[qtyCol]) : null;

    if (rev != null) { totalRevenue += rev; revenueRows++; }
    if (cost != null) totalCost += cost;
    if (qty != null) totalUnits += qty;

    if (dateCol >= 0) {
      const mk = monthKey(row[dateCol]);
      if (mk) {
        const m = (byMonth[mk] ||= { revenue: 0, cost: 0, orders: 0, units: 0 });
        m.orders++;
        if (rev != null) m.revenue += rev;
        if (cost != null) m.cost += cost;
        if (qty != null) m.units += qty;
      }
    }

    if (categoryCol >= 0) {
      const key = String(row[categoryCol] || "—");
      const c = (byCategory[key] ||= { revenue: 0, orders: 0, units: 0 });
      c.orders++;
      if (rev != null) c.revenue += rev;
      if (qty != null) c.units += qty;
    }

    if (statusCol >= 0) {
      const key = String(row[statusCol] || "—");
      byStatus[key] = (byStatus[key] || 0) + 1;
    }

    if (productCol >= 0) {
      const key = String(row[productCol] || "—");
      const p = (byProduct[key] ||= { revenue: 0, units: 0 });
      if (rev != null) p.revenue += rev;
      if (qty != null) p.units += qty;
    }
  }

  const totalOrders = rows.length;
  const round2 = (n) => Math.round(n * 100) / 100;

  // Profit only if we actually have cost data. Otherwise the frontend
  // applies an assumed margin to revenue.
  const hasCost = costCol >= 0 && totalCost > 0;
  const profit = hasCost ? round2(totalRevenue - totalCost) : null;

  const monthly = Object.entries(byMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, v]) => ({
      month,
      revenue: round2(v.revenue),
      cost: round2(v.cost),
      profit: hasCost ? round2(v.revenue - v.cost) : null,
      orders: v.orders,
      units: v.units,
    }));

  const categories = Object.entries(byCategory)
    .map(([name, v]) => ({ name, revenue: round2(v.revenue), orders: v.orders, units: v.units }))
    .sort((a, b) => b.revenue - a.revenue);

  const topProducts = Object.entries(byProduct)
    .map(([name, v]) => ({ name, revenue: round2(v.revenue), units: v.units }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10);

  const statuses = Object.entries(byStatus)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  return {
    detected,
    totals: {
      orders: totalOrders,
      revenue: round2(totalRevenue),
      cost: hasCost ? round2(totalCost) : null,
      profit,               // null when no cost column
      hasCost,
      units: totalUnits,
      avgOrderValue: revenueRows ? round2(totalRevenue / revenueRows) : null,
    },
    monthly,
    categories,
    topProducts,
    statuses,
  };
}

module.exports = { computeAnalytics };
