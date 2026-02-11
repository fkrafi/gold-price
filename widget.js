(function () {
  const DEFAULTS = {
    historyUrl: "api/history.json",
  };

  async function fetchJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
    return res.json();
  }

  function $(root, selector) {
    return typeof selector === "string" ? root.querySelector(selector) : selector;
  }

  function format(n) {
    const num = typeof n === "string" ? parseFloat(n) : n;
    if (!isFinite(num)) return "-";
    return new Intl.NumberFormat(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  }

  // Floating history button (bottom-right) that navigates to /history.html
  function ensureFloatingHistoryButton() {
    if (document.getElementById('gold-history-fab')) return;
    const btn = document.createElement('button');
    btn.id = 'gold-history-fab';
    btn.type = 'button';
    btn.textContent = '📊 History';
    btn.style.position = 'fixed';
    btn.style.right = '16px';
    btn.style.bottom = '16px';
    btn.style.zIndex = '9999';
    btn.style.padding = '10px 14px';
    btn.style.borderRadius = '999px';
    btn.style.border = 'none';
    btn.style.cursor = 'pointer';
    btn.style.boxShadow = '0 6px 18px rgba(0,0,0,0.15)';
    btn.style.background = '#1e88e5';
    btn.style.color = '#fff';
    btn.style.fontWeight = '600';
    btn.style.fontSize = '14px';
    btn.addEventListener('click', () => {
      // Navigate to history page
      window.location.href = 'history.html';
    });
    document.body.appendChild(btn);
  }

  function render(container, today, prev, dateLabel, allHistory) {
    function delta(curr, prevVal) {
      if (curr == null || prevVal == null) return null;
      const d = parseFloat(curr) - parseFloat(prevVal);
      const sign = d > 0 ? "+" : d < 0 ? "" : "";
      return `${sign}${format(d)}`;
    }

    container.innerHTML = `
      <div class="header">
        <div class="badge"><span class="dot"></span> ${dateLabel}</div>
      </div>
      <div class="grid">
        <div class="panel">
          <h3>24K</h3>
          <p class="price">${format(today.gold_24kt)}
          </p>
          <div class="delta">${prev ? `Δ ${delta(today.gold_24kt, prev.gold_24kt)}` : ""}</div>
        </div>
        <div class="panel">
          <h3>22K</h3>
          <p class="price">${format(today.gold_22kt)}</p>
          <div class="delta">${prev ? `Δ ${delta(today.gold_22kt, prev.gold_22kt)}` : ""}</div>
        </div>
        <div class="panel">
          <h3>18K</h3>
          <p class="price">${format(today.gold_18kt)}</p>
          <div class="delta">${prev ? `Δ ${delta(today.gold_18kt, prev.gold_18kt)}` : ""}</div>
        </div>
      </div>
      <div class="footer"></div>
    `;
    // Ensure global floating button exists outside container
    ensureFloatingHistoryButton();
  }

  async function mount(target, opts = {}) {
    const el = typeof target === "string" ? document.querySelector(target) : target;
    if (!el) throw new Error("GoldPriceWidget: target not found");

    const historyUrl = el.getAttribute("data-source-history") || opts.historyUrl || DEFAULTS.historyUrl;

    try {
      const historyData = await fetchJson(historyUrl);
      
      // Convert history object to array and sort by date descending
      const sortedHistory = Object.entries(historyData)
        .map(([date, data]) => ({ date, ...data }))
        .sort((a, b) => new Date(b.date) - new Date(a.date));

      if (sortedHistory.length === 0) {
        throw new Error("No data available in history");
      }

      // First item is latest, second is previous day
      const today = sortedHistory[0];
      const prev = sortedHistory.length > 1 ? sortedHistory[1] : null;
      const dateLabel = today.date;

      render(el, today, prev, dateLabel, sortedHistory);
      ensureFloatingHistoryButton();
    } catch (err) {
      const dateLabel = new Date().toISOString().slice(0, 10);
      el.innerHTML = `
        <div class="header">
          <div class="badge"><span class="dot"></span> ${dateLabel}</div>
        </div>
        <div class="panel" style="margin-top:12px;">
          <h3>Unable to load data</h3>
          <p class="delta">${String(err)}</p>
        </div>
      `;
      console.error("GoldPriceWidget error:", err);
    }
  }

  window.GoldPriceWidget = { mount };
})();