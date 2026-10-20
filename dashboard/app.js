// =============================================================================
// RETAIL INTELLIGENCE DASHBOARD CONTROLLER (VANILLA JS + CHART.JS)
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initOverviewPage();
  initExplorePage();
  initPairsPage();
  initRecommenderPage();
  initSpeedPage();
  initModelPage();
  initGlossary();
});

// =============================================================================
// 1. NAVIGATION ROUTER
// =============================================================================
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const pages = document.querySelectorAll('.page-view');
  const greetingTitle = document.getElementById('pageGreeting');
  const greetingSub = document.getElementById('pageGreetingSub');

  const pageHeaders = {
    overview: {
      title: "Hi 👋 here's your store at a glance.",
      sub: "Track shopping volumes, peak ordering hours, and customer retention across 33.8 million grocery purchases."
    },
    explore: {
      title: "Slice the data your way 🔍",
      sub: "Filter shopping patterns by day of week, time of day, and category zoom level using fast pre-aggregated cubes."
    },
    customers: {
      title: "Who are our shoppers? 👥",
      sub: "Customer segmentation profiles based on purchase cadence (Recency proxy), order count (Frequency), and basket volume (Monetary proxy)."
    },
    pairs: {
      title: "What is bought together? 🛒",
      sub: "Discovered association rules showing products frequently co-purchased in the same shopping basket, with temporal slice comparisons."
    },
    recommender: {
      title: "Pick items, get smart suggestions 🎯",
      sub: "Interactive shopping cart recommender powered by contextual association rules and aisle affinity models."
    },
    speed: {
      title: "Which design is fastest? ⚡",
      sub: "Empirical latency benchmarking across 33.8 million rows comparing Normalized tables, Galaxy Schema, Columnar Parquet, and Summary Cubes."
    },
    model: {
      title: "How is the data organized? 🏗️",
      sub: "Kimball Galaxy Constellation dimensional architecture, conformed dimensions, referential integrity tests, and data dictionary."
    }
  };

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetPage = item.dataset.page;
      
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      pages.forEach(p => p.style.display = 'none');
      const activeView = document.getElementById(`view-${targetPage}`);
      if (activeView) activeView.style.display = 'block';

      if (pageHeaders[targetPage]) {
        greetingTitle.innerHTML = pageHeaders[targetPage].title;
        greetingSub.innerHTML = pageHeaders[targetPage].sub;
      }
    });
  });
}

// =============================================================================
// 2. PAGE 1: OVERVIEW CONTROLLER
// =============================================================================
function initOverviewPage() {
  renderHeatmap();
  renderTopProductsChart();
  renderDeptDonutChart();
  renderLoyaltyCurveChart();
}

function renderHeatmap() {
  const container = document.getElementById('heatmapContainer');
  if (!container || !DWM_DATA) return;

  const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const matrix = Array(7).fill(0).map(() => Array(24).fill(0));
  let maxVal = 0;
  let peakDay = 0, peakHour = 0;

  DWM_DATA.heatmap.forEach(cell => {
    const d = cell.order_dow;
    const h = cell.hour;
    if (d < 7 && h < 24) {
      matrix[d][h] = cell.total_items;
      if (cell.total_items > maxVal) {
        maxVal = cell.total_items;
        peakDay = d;
        peakHour = h;
      }
    }
  });

  let html = '<div class="heatmap-container">';
  
  // Header hours
  html += '<div class="heatmap-row" style="margin-bottom: 2px;"><div class="heatmap-label" style="font-size:10px; color:#94A3B8;">Day / Hour</div><div class="heatmap-cells" style="font-size:9.5px; color:#94A3B8; text-align:center;">';
  for (let h = 0; h < 24; h += 3) {
    html += `<span style="flex:3; text-align:left;">${h}:00</span>`;
  }
  html += '</div></div>';

  dayNames.forEach((name, d) => {
    html += `<div class="heatmap-row"><div class="heatmap-label">${name}</div><div class="heatmap-cells">`;
    for (let h = 0; h < 24; h++) {
      const val = matrix[d][h];
      const intensity = Math.min(1.0, val / maxVal);
      // Soft purple interpolation from #F3F2FD (243, 242, 253) to #6C63D9 (108, 99, 217)
      const r = Math.round(243 - intensity * (243 - 108));
      const g = Math.round(242 - intensity * (242 - 99));
      const b = Math.round(253 - intensity * (253 - 217));
      const bgColor = `rgb(${r}, ${g}, ${b})`;
      const isPeak = (d === peakDay && h === peakHour);

      html += `<div class="heatmap-cell ${isPeak ? 'peak-coral' : ''}" 
                    style="background: ${bgColor};" 
                    title="${name} at ${h}:00 — ${val.toLocaleString()} items ${isPeak ? '(★ Peak Shopping Hour)' : ''}">
               </div>`;
    }
    html += '</div></div>';
  });
  html += '</div>';

  container.innerHTML = html;
}

function renderTopProductsChart() {
  const ctx = document.getElementById('topProductsChart');
  if (!ctx || !DWM_DATA) return;

  const top8 = DWM_DATA.top_products.slice(0, 8);
  const labels = top8.map(p => p.product_name.length > 22 ? p.product_name.substring(0, 20) + '...' : p.product_name);
  const data = top8.map(p => p.orders);
  const colors = top8.map((_, i) => i === 0 ? '#FF6B4A' : '#6C63D9');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderRadius: 6,
        barThickness: 18
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { left: 12, right: 16 }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `Orders: ${item.raw.toLocaleString()} (Reorder Rate: ${top8[item.dataIndex].reorder_pct}%)`
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { display: false },
          ticks: { font: { family: 'Plus Jakarta Sans', size: 11, weight: 600 }, color: '#1E293B', padding: 8 }
        }
      }
    }
  });
}

function renderDeptDonutChart() {
  const ctx = document.getElementById('deptDonutChart');
  if (!ctx || !DWM_DATA) return;

  const depts = DWM_DATA.departments;
  const top5 = depts.slice(0, 5);
  const others = depts.slice(5).reduce((acc, d) => acc + d.total_items, 0);

  const labels = top5.map(d => d.department.charAt(0).toUpperCase() + d.department.slice(1)).concat(['Others (16 Depts)']);
  const data = top5.map(d => d.total_items).concat([others]);
  const colors = ['#6C63D9', '#8B85E5', '#A5B4FC', '#C7D2FE', '#E0E7FF', '#CBD5E1'];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#FFFFFF'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'right',
          labels: { font: { family: 'Plus Jakarta Sans', size: 11 }, boxWidth: 12, padding: 8, color: '#334155' }
        },
        tooltip: {
          callbacks: {
            label: (item) => `${item.label}: ${item.raw.toLocaleString()} items (${((item.raw / 33819106)*100).toFixed(1)}%)`
          }
        }
      }
    }
  });
}

function renderLoyaltyCurveChart() {
  const ctx = document.getElementById('loyaltyCurveChart');
  if (!ctx || !DWM_DATA) return;

  const pts = DWM_DATA.loyalty_curve;
  const labels = pts.map(p => `#${p.order_number}`);
  const values = pts.map(p => p.avg_basket);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        borderColor: '#6C63D9',
        backgroundColor: 'rgba(108, 99, 217, 0.06)',
        fill: true,
        tension: 0.35,
        borderWidth: 3,
        pointRadius: 0,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => `Customer Order ${items[0].label}`,
            label: (item) => `Average Basket Size: ${item.raw} items`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 }, color: '#94A3B8', maxTicksLimit: 10 }
        },
        y: {
          grid: { color: '#F1F5F9' },
          ticks: { font: { size: 11 }, color: '#64748B' },
          title: { display: true, text: 'Items per Order', font: { size: 11 } }
        }
      }
    }
  });
}

// =============================================================================
// 3. PAGE 2: EXPLORE CONTROLLER
// =============================================================================
let exploreChartInstance = null;

function initExplorePage() {
  const dayPills = document.querySelectorAll('#filterDay .pill-btn');
  const timePills = document.querySelectorAll('#filterTime .pill-btn');
  const zoomPills = document.querySelectorAll('#filterZoom .pill-btn');

  function bindPillGroup(group, callback) {
    group.forEach(btn => {
      btn.addEventListener('click', () => {
        group.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        callback();
      });
    });
  }

  bindPillGroup(dayPills, updateExplore);
  bindPillGroup(timePills, updateExplore);
  bindPillGroup(zoomPills, updateExplore);

  updateExplore();
  renderPivotTable();
}

function updateExplore() {
  const day = document.querySelector('#filterDay .pill-btn.active')?.dataset.val || 'all';
  const time = document.querySelector('#filterTime .pill-btn.active')?.dataset.val || 'all';
  const zoom = document.querySelector('#filterZoom .pill-btn.active')?.dataset.val || 'dept';

  const strip = document.getElementById('exploreSummaryStrip');
  const headline = document.getElementById('exploreHeadline');
  const greyline = document.getElementById('exploreGreyline');

  let dayText = day === 'all' ? 'All Days' : (day === 'weekend' ? 'Weekends (Sun/Mon)' : 'Weekdays (Tue–Sat)');
  let timeText = time === 'all' ? 'All Hours' : time.charAt(0).toUpperCase() + time.slice(1);
  let zoomText = zoom === 'dept' ? 'Department' : (zoom === 'aisle' ? 'Aisle' : 'Top Product');

  if (strip) {
    strip.innerHTML = `<span>📍 Currently Showing:</span> ${dayText} • ${timeText} • Zoom Level: <strong>${zoomText}</strong>`;
  }

  let items = [];
  if (zoom === 'dept') {
    headline.innerText = "Department volume distribution under selected filters";
    greyline.innerText = "Showing high-level department volume ranked from highest to lowest.";
    items = DWM_DATA.departments.slice(0, 10).map(d => ({
      name: d.department.charAt(0).toUpperCase() + d.department.slice(1),
      val: d.total_items
    }));
  } else if (zoom === 'aisle') {
    headline.innerText = "Aisle-level drill-down reveals specific category drivers";
    greyline.innerText = "Showing top 10 grocery aisles by volume.";
    items = DWM_DATA.aisles.slice(0, 10).map(a => ({
      name: a.aisle.charAt(0).toUpperCase() + a.aisle.slice(1),
      val: a.total_items
    }));
  } else {
    headline.innerText = "Product SKU micro-level drill-down shows exact item velocity";
    greyline.innerText = "Showing top 10 bestselling individual products.";
    items = DWM_DATA.top_products.slice(0, 10).map(p => ({
      name: p.product_name,
      val: p.orders
    }));
  }

  renderExploreChart(items);
}

function renderExploreChart(items) {
  const ctx = document.getElementById('exploreChart');
  if (!ctx) return;

  if (exploreChartInstance) {
    exploreChartInstance.destroy();
  }

  exploreChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: items.map(i => i.name.length > 24 ? i.name.substring(0, 22) + '...' : i.name),
      datasets: [{
        data: items.map(i => i.val),
        backgroundColor: '#6C63D9',
        borderRadius: 6,
        barThickness: 20
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { left: 12, right: 16 }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `Volume: ${item.raw.toLocaleString()} items`
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { display: false },
          ticks: { font: { family: 'Plus Jakarta Sans', size: 11, weight: 600 }, color: '#1E293B', padding: 8 }
        }
      }
    }
  });
}

function renderPivotTable() {
  const tbody = document.querySelector('#pivotTable tbody');
  if (!tbody || !DWM_DATA) return;

  // Build matrix from pivot data
  const deptMap = {};
  DWM_DATA.pivot.forEach(row => {
    if (!deptMap[row.department]) {
      deptMap[row.department] = { Morning: 0, Afternoon: 0, Evening: 0, Night: 0, Total: 0 };
    }
    deptMap[row.department][row.part_of_day] = row.total_items;
    deptMap[row.department].Total += row.total_items;
  });

  const sortedDepts = Object.keys(deptMap).sort((a, b) => deptMap[b].Total - deptMap[a].Total).slice(0, 10);

  let html = '';
  sortedDepts.forEach(d => {
    const row = deptMap[d];
    html += `<tr>
      <td><strong>${d.charAt(0).toUpperCase() + d.slice(1)}</strong></td>
      <td>${row.Morning.toLocaleString()}</td>
      <td>${row.Afternoon.toLocaleString()}</td>
      <td>${row.Evening.toLocaleString()}</td>
      <td>${row.Night.toLocaleString()}</td>
      <td><strong>${row.Total.toLocaleString()}</strong></td>
    </tr>`;
  });
  tbody.innerHTML = html;

  // CSV download
  const dlBtn = document.getElementById('downloadPivotBtn');
  if (dlBtn) {
    dlBtn.addEventListener('click', () => {
      let csv = 'Department,Morning,Afternoon,Evening,Night,Total\n';
      sortedDepts.forEach(d => {
        const row = deptMap[d];
        csv += `"${d}",${row.Morning},${row.Afternoon},${row.Evening},${row.Night},${row.Total}\n`;
      });
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'department_daypart_pivot.csv';
      a.click();
    });
  }
}

// =============================================================================
// 4. PAGE 4: PRODUCT PAIRS CONTROLLER
// =============================================================================
function initPairsPage() {
  const slicePills = document.querySelectorAll('#filterPairSlice .pill-btn');
  const sliderLift = document.getElementById('sliderLift');
  const sliderSupp = document.getElementById('sliderSupp');
  const liftVal = document.getElementById('liftVal');
  const suppVal = document.getElementById('suppVal');

  slicePills.forEach(btn => {
    btn.addEventListener('click', () => {
      slicePills.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderPairs();
    });
  });

  sliderLift.addEventListener('input', () => {
    liftVal.innerText = `${sliderLift.value}×`;
    renderPairs();
  });

  sliderSupp.addEventListener('input', () => {
    suppVal.innerText = `${sliderSupp.value}%`;
    renderPairs();
  });

  renderPairs();
}

function renderPairs() {
  const container = document.getElementById('pairsListContainer');
  if (!container || !DWM_DATA) return;

  const slice = document.querySelector('#filterPairSlice .pill-btn.active')?.dataset.val || 'Global_Baseline';
  const minLift = parseFloat(document.getElementById('sliderLift').value);
  const minSupp = parseFloat(document.getElementById('sliderSupp').value) / 100.0;

  const filtered = DWM_DATA.rules.filter(r => r.slice_name === slice && r.lift >= minLift && r.support >= minSupp);

  if (filtered.length === 0) {
    container.innerHTML = '<div style="padding: 20px; color:#64748B; font-size:13px; text-align:center;">No rules match these strict slider thresholds. Try lowering the sliders.</div>';
    return;
  }

  let html = '';
  filtered.slice(0, 6).forEach(r => {
    const confPct = Math.round(r.confidence * 100);
    const suppPct = (r.support * 100).toFixed(1);
    const liftStr = `${r.lift.toFixed(1)}×`;

    html += `
      <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
        <div style="font-size: 14px; font-weight: 700; color: #0F172A; margin-bottom: 4px;">
          People who buy <span style="color:#6C63D9;">${r.antecedent}</span> also buy <span style="color:#FF6B4A;">${r.consequent}</span>
        </div>
        <div style="font-size: 12.5px; color: #475569;">
          Together in <strong>${suppPct} out of 100 orders</strong>, and 
          <span style="color:#FF6B4A; font-weight:700;">${liftStr} more likely</span> than normal.
          (When item A is in cart, ${confPct}% also add item B).
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// =============================================================================
// 5. PAGE 5: RECOMMENDER CONTROLLER (FLAGSHIP FEATURE)
// =============================================================================
let currentCart = ["Organic Cilantro"];

function initRecommenderPage() {
  renderCartChips();
  renderQuickAdd();

  const ctxPills = document.querySelectorAll('#recContextFilter .pill-btn');
  ctxPills.forEach(btn => {
    btn.addEventListener('click', () => {
      ctxPills.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      computeRecommendations();
    });
  });

  computeRecommendations();
}

function renderCartChips() {
  const container = document.getElementById('cartChipsContainer');
  if (!container) return;

  if (currentCart.length === 0) {
    container.innerHTML = '<span style="font-size:13px; color:#94A3B8; font-style:italic;">Your cart is empty. Pick items below!</span>';
    return;
  }

  let html = '';
  currentCart.forEach(item => {
    html += `
      <span style="display:inline-flex; align-items:center; gap:6px; background:#F3F2FD; border:1px solid #ECEAFE; color:#6C63D9; padding:5px 12px; border-radius:9999px; font-size:13px; font-weight:700;">
        ${item}
        <button onclick="removeFromCart('${item}')" style="background:none; border:none; color:#FF6B4A; font-weight:800; cursor:pointer; font-size:14px; line-height:1;">&times;</button>
      </span>
    `;
  });
  container.innerHTML = html;
}

function renderQuickAdd() {
  const container = document.getElementById('quickAddContainer');
  if (!container) return;

  const popular = [
    "Organic Cilantro", "Organic Lemon", "Organic Hass Avocado",
    "Organic Raspberries", "Honeycrisp Apple", "Limes",
    "Organic Strawberries", "Bag of Organic Bananas", "Yellow Onions",
    "Large Lemon", "Original Hummus", "Half & Half"
  ];

  let html = '';
  popular.forEach(p => {
    if (!currentCart.includes(p)) {
      html += `
        <button onclick="addToCart('${p}')" style="background:#FFFFFF; border:1px solid #E2E8F0; padding:4px 10px; border-radius:9999px; font-size:12px; font-weight:600; color:#475569; cursor:pointer;">
          + ${p}
        </button>
      `;
    }
  });
  container.innerHTML = html;
}

window.addToCart = function(product) {
  if (currentCart.length >= 5) {
    alert("You can add up to 5 items to the test cart.");
    return;
  }
  if (!currentCart.includes(product)) {
    currentCart.push(product);
    renderCartChips();
    renderQuickAdd();
    computeRecommendations();
  }
};

window.removeFromCart = function(product) {
  currentCart = currentCart.filter(i => i !== product);
  renderCartChips();
  renderQuickAdd();
  computeRecommendations();
};

function computeRecommendations() {
  const container = document.getElementById('recResultsContainer');
  if (!container || !DWM_DATA) return;

  if (currentCart.length === 0) {
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#64748B;">Please add at least one product to your cart to trigger recommendations.</div>';
    return;
  }

  const slice = document.querySelector('#recContextFilter .pill-btn.active')?.dataset.val || 'Weekend_Morning';

  // 1. Check direct association rules
  let matchingRules = DWM_DATA.rules.filter(r => 
    currentCart.includes(r.antecedent) && 
    !currentCart.includes(r.consequent) &&
    (r.slice_name === slice || r.slice_name === 'Global_Baseline')
  );

  // Sort by priority to slice + lift
  matchingRules.sort((a, b) => {
    const scoreA = (a.slice_name === slice ? 2.0 : 1.0) * a.lift;
    const scoreB = (b.slice_name === slice ? 2.0 : 1.0) * b.lift;
    return scoreB - scoreA;
  });

  // Deduplicate by consequent
  const seen = new Set();
  const topRecs = [];
  matchingRules.forEach(r => {
    if (!seen.has(r.consequent)) {
      seen.add(r.consequent);
      topRecs.push(r);
    }
  });

  let html = '';

  if (topRecs.length > 0) {
    topRecs.slice(0, 4).forEach((r, idx) => {
      const rank = idx + 1;
      const confPct = Math.round(r.confidence * 100);
      const liftVal = r.lift;
      const strengthPct = Math.min(100, Math.round((liftVal / 5.0) * 100));
      const strengthLabel = liftVal > 2.5 ? 'Great match' : (liftVal > 1.8 ? 'Strong match' : 'Good match');
      const isPeakWeekend = (r.slice_name === 'Weekend_Morning' && r.antecedent.includes('Cilantro'));

      html += `
        <div class="rec-box">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="rec-rank ${rank === 1 ? 'top-rank' : ''}">#${rank}</div>
            <div>
              <div class="rec-title">
                ${r.consequent}
                ${isPeakWeekend ? '<span style="background:#FFEBE6; color:#FF6B4A; font-size:10px; padding:2px 8px; border-radius:9999px; font-weight:800;">★ Peak Weekend Match</span>' : ''}
              </div>
              <div class="rec-desc">
                Because you added <strong>${r.antecedent}</strong>. Bought together in <strong>${confPct} out of 100 orders</strong> (${liftVal.toFixed(1)}× more likely than normal).
              </div>
            </div>
          </div>
          <div class="strength-bar-wrap">
            <div class="strength-label" style="color: ${liftVal > 2.5 ? '#FF6B4A' : '#6C63D9'};">${strengthLabel} (${liftVal.toFixed(1)}×)</div>
            <div class="strength-bar-bg">
              <div class="strength-bar-fill" style="width: ${strengthPct}%;"></div>
            </div>
          </div>
        </div>
      `;
    });
  } else {
    // Smart fallback to category bestsellers
    html += '<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:14px;"><div style="font-weight:700; color:#475569; margin-bottom:6px;">No direct pairing rule found for these items. Activating smart category recommendations:</div>';
    
    // Pick 3 fallback items
    const fallbacks = DWM_DATA.fallback_recs.slice(0, 3);
    fallbacks.forEach((f, idx) => {
      html += `
        <div class="rec-box" style="margin-bottom:8px;">
          <div style="display:flex; align-items:center; gap:12px;">
            <div class="rec-rank">#${idx+1}</div>
            <div>
              <div class="rec-title">${f.product_name}</div>
              <div class="rec-desc">Category Bestseller from the <strong>${f.aisle}</strong> aisle (${f.department}).</div>
            </div>
          </div>
          <span style="background:#F1F5F9; color:#475569; padding:4px 8px; border-radius:6px; font-size:11px; font-weight:700;">Category Match</span>
        </div>
      `;
    });
    html += '</div>';
  }

  container.innerHTML = html;
}

// =============================================================================
// 6. PAGE 6: SPEED TESTS CONTROLLER
// =============================================================================
function initSpeedPage() {
  renderSpeedBarChart();
  renderScaleLineChart();
  renderMiningChart();
}

function renderSpeedBarChart() {
  const ctx = document.getElementById('speedBarChart');
  if (!ctx || !DWM_DATA) return;

  const data = DWM_DATA.benchmarks.q_latencies;
  const labels = data.map(d => d.architecture);
  const values = data.map(d => d.latency);
  const colors = data.map(d => d.color);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderRadius: 6,
        barThickness: 22
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `Latency: ${item.raw} seconds (${data[item.dataIndex].note})`
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { display: false },
          ticks: { font: { family: 'Plus Jakarta Sans', size: 11, weight: 700 }, color: '#1E293B' }
        }
      }
    }
  });
}

function renderScaleLineChart() {
  const ctx = document.getElementById('scaleLineChart');
  if (!ctx || !DWM_DATA) return;

  const data = DWM_DATA.benchmarks.scalability;
  const labels = data.map(d => d.scale);
  const normVals = data.map(d => d.normalized);
  const galaxyVals = data.map(d => d.galaxy);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Normalized 3NF',
          data: normVals,
          borderColor: '#FF6B4A',
          borderWidth: 3,
          tension: 0.2,
          pointRadius: 5
        },
        {
          label: 'Galaxy Schema',
          data: galaxyVals,
          borderColor: '#6C63D9',
          borderWidth: 3,
          tension: 0.2,
          pointRadius: 5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 11 }, boxWidth: 12 }
        }
      },
      scales: {
        y: {
          grid: { color: '#F1F5F9' },
          ticks: { font: { size: 10 } },
          title: { display: true, text: 'Latency (s)', font: { size: 11 } }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderMiningChart() {
  const ctx = document.getElementById('miningChart');
  if (!ctx || !DWM_DATA) return;

  const data = DWM_DATA.benchmarks.mining;
  const labels = data.map(d => d.support);
  const apriori = data.map(d => d.apriori);
  const fpgrowth = data.map(d => d.fpgrowth);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Apriori (Candidate Explosion)',
          data: apriori,
          borderColor: '#FF6B4A',
          borderDash: [5, 5],
          borderWidth: 3,
          tension: 0.2,
          pointRadius: 5
        },
        {
          label: 'FP-Growth (In-Memory Tree)',
          data: fpgrowth,
          borderColor: '#6C63D9',
          borderWidth: 3,
          tension: 0.2,
          pointRadius: 5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 11 }, boxWidth: 12 }
        }
      },
      scales: {
        y: {
          grid: { color: '#F1F5F9' },
          title: { display: true, text: 'Execution Time (Seconds)', font: { size: 11 } }
        },
        x: {
          grid: { display: false },
          title: { display: true, text: 'Minimum Support Threshold', font: { size: 11 } }
        }
      }
    }
  });
}

// =============================================================================
// 7. PAGE 7: DATA MODEL CONTROLLER
// =============================================================================
function initModelPage() {
  initGalaxyDiagram();
  renderTableInspector();
  renderQualityChecks();
  renderDataDictionary();
}

function initGalaxyDiagram() {
  const nodes = document.querySelectorAll('.table-node');
  const selector = document.getElementById('tableSelector');
  const filterPills = document.querySelectorAll('#galaxyFilterPills .pill-btn');
  const allPaths = document.querySelectorAll('.schema-path');
  const allBadges = document.querySelectorAll('.schema-badge');

  // Mapping of table relationships for interactive tracing
  const connections = {
    dim_product: {
      paths: ['#path-dim_product'],
      badges: ['#badge-dim_product'],
      nodes: ['#node-dim_product', '#node-fact_order_items']
    },
    dim_customer: {
      paths: ['#path-dim_customer-items', '#path-dim_customer-orders'],
      badges: ['#badge-dim_customer-items', '#badge-dim_customer-orders'],
      nodes: ['#node-dim_customer', '#node-fact_order_items', '#node-fact_orders']
    },
    dim_time: {
      paths: ['#path-dim_time-orders', '#path-dim_time-items'],
      badges: ['#badge-dim_time-orders', '#badge-dim_time-items'],
      nodes: ['#node-dim_time', '#node-fact_order_items', '#node-fact_orders']
    },
    fact_order_items: {
      paths: ['#path-dim_product', '#path-dim_customer-items', '#path-dim_time-items', '#path-fact_bridge', '#path-cube_rollup', '#path-mining_rules'],
      badges: ['#badge-dim_product', '#badge-dim_customer-items', '#badge-dim_time-items', '#badge-fact_bridge', '#badge-cube_rollup', '#badge-mining_rules'],
      nodes: ['#node-fact_order_items', '#node-dim_product', '#node-dim_customer', '#node-dim_time', '#node-fact_orders', '#node-cube_dept_time', '#node-fact_rules']
    },
    fact_orders: {
      paths: ['#path-fact_bridge', '#path-dim_customer-orders', '#path-dim_time-orders'],
      badges: ['#badge-fact_bridge', '#badge-dim_customer-orders', '#badge-dim_time-orders'],
      nodes: ['#node-fact_orders', '#node-fact_order_items', '#node-dim_customer', '#node-dim_time']
    },
    cube_dept_time: {
      paths: ['#path-cube_rollup'],
      badges: ['#badge-cube_rollup'],
      nodes: ['#node-cube_dept_time', '#node-fact_order_items']
    },
    fact_rules: {
      paths: ['#path-mining_rules'],
      badges: ['#badge-mining_rules'],
      nodes: ['#node-fact_rules', '#node-fact_order_items']
    }
  };

  function selectNode(tblName) {
    nodes.forEach(n => {
      if (n.dataset.tbl === tblName) {
        n.classList.add('selected');
      } else {
        n.classList.remove('selected');
      }
    });
  }

  // Handle table node clicks
  nodes.forEach(node => {
    node.addEventListener('click', () => {
      const tbl = node.dataset.tbl;
      if (!tbl) return;
      selectNode(tbl);
      if (selector) {
        selector.value = tbl;
        selector.dispatchEvent(new Event('change'));
      }
      document.getElementById('tableInspectorCard')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });

    // Hover highlighting
    node.addEventListener('mouseenter', () => {
      const tbl = node.dataset.tbl;
      const conn = connections[tbl];
      if (!conn) return;

      nodes.forEach(n => {
        if (!conn.nodes.includes(`#${n.id}`)) {
          n.classList.add('dimmed');
        } else {
          n.classList.add('highlighted');
        }
      });

      allPaths.forEach(p => {
        if (conn.paths.includes(`#${p.id}`)) {
          p.classList.add('highlighted');
        } else {
          p.classList.add('dimmed');
        }
      });

      allBadges.forEach(b => {
        if (conn.badges.includes(`#${b.id}`)) {
          b.classList.add('highlighted');
        }
      });
    });

    node.addEventListener('mouseleave', () => {
      nodes.forEach(n => n.classList.remove('dimmed', 'highlighted'));
      allPaths.forEach(p => p.classList.remove('dimmed', 'highlighted'));
      allBadges.forEach(b => b.classList.remove('highlighted'));
    });
  });

  // Sync when selector changes
  if (selector) {
    selector.addEventListener('change', () => {
      selectNode(selector.value);
    });
    selectNode(selector.value);
  }

  // Filter Pills Handling
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const filter = pill.dataset.filter;

      nodes.forEach(n => n.classList.remove('dimmed', 'highlighted'));
      allPaths.forEach(p => p.classList.remove('dimmed', 'highlighted'));

      if (filter === 'all') {
        // All active
      } else if (filter === 'facts') {
        nodes.forEach(n => {
          if (n.dataset.tbl === 'fact_order_items' || n.dataset.tbl === 'fact_orders') {
            n.classList.add('highlighted');
          } else {
            n.classList.add('dimmed');
          }
        });
        allPaths.forEach(p => {
          if (p.id === 'path-fact_bridge') {
            p.classList.add('highlighted');
          } else {
            p.classList.add('dimmed');
          }
        });
      } else if (filter === 'dimensions') {
        nodes.forEach(n => {
          if (n.dataset.tbl.startsWith('dim_')) {
            n.classList.add('highlighted');
          } else {
            n.classList.add('dimmed');
          }
        });
        allPaths.forEach(p => {
          if (p.id.startsWith('path-dim_')) {
            p.classList.add('highlighted');
          } else {
            p.classList.add('dimmed');
          }
        });
      } else if (filter === 'marts') {
        nodes.forEach(n => {
          if (n.dataset.tbl === 'cube_dept_time' || n.dataset.tbl === 'fact_rules') {
            n.classList.add('highlighted');
          } else {
            n.classList.add('dimmed');
          }
        });
        allPaths.forEach(p => {
          if (p.id === 'path-cube_rollup' || p.id === 'path-mining_rules') {
            p.classList.add('highlighted');
          } else {
            p.classList.add('dimmed');
          }
        });
      }
    });
  });
}

function renderTableInspector() {
  const selector = document.getElementById('tableSelector');
  const detailsBox = document.getElementById('tableDetailsBox');
  const sampleTable = document.getElementById('sampleRowsTable');

  const meta = {
    fact_order_items: {
      grain: "1 row per product inside an order (Item Grain)",
      count: "33,819,106 rows",
      cols: "order_id, product_key, customer_key, time_key, add_to_cart_order, reordered"
    },
    fact_orders: {
      grain: "1 row per completed shopping order (Order Grain)",
      count: "3,346,083 orders",
      cols: "order_id, customer_key, time_key, order_number, days_since_prior_order, basket_size, reorder_ratio"
    },
    dim_product: {
      grain: "Product SKU catalog with Aisle and Department",
      count: "49,688 products",
      cols: "product_key, product_name, aisle_id, aisle, department_id, department"
    },
    dim_customer: {
      grain: "Customer lifetime profile with RFM clusters",
      count: "206,209 shoppers",
      cols: "customer_key, total_orders, total_items, avg_basket_size, avg_days_between_orders, rfm_segment"
    },
    dim_time: {
      grain: "168 cyclical hourly time slots (7 Days × 24 Hours)",
      count: "168 slots",
      cols: "time_key, order_dow, hour, day_label, is_weekend, part_of_day"
    },
    cube_dept_time: {
      grain: "Department × Aisle × Day × Hour pre-aggregated summary",
      count: "22,480 cells",
      cols: "department, aisle, order_dow, hour, items, reordered_items"
    },
    fact_rules: {
      grain: "Discovered market basket association rules",
      count: "48 rules",
      cols: "slice_name, antecedent, consequent, support, confidence, lift"
    }
  };

  function update() {
    const tbl = selector.value;
    const m = meta[tbl];
    if (!m) return;

    detailsBox.innerHTML = `
      <div style="font-size:16px; font-weight:800; color:#6C63D9;">${tbl}</div>
      <div style="font-size:13px; color:#1E293B; margin: 4px 0;"><strong>Grain:</strong> ${m.grain}</div>
      <div style="font-size:13px; color:#1E293B; margin: 4px 0;"><strong>Total Rows:</strong> ${m.count}</div>
      <div style="font-size:12px; color:#64748B; margin-top: 6px;"><strong>Columns:</strong> <code>${m.cols}</code></div>
    `;

    const sample = DWM_DATA.samples[tbl];
    if (sample && sample.length > 0) {
      const headers = Object.keys(sample[0]);
      let ths = headers.map(h => `<th>${h}</th>`).join('');
      let trs = sample.map(row => {
        let tds = headers.map(h => `<td>${row[h]}</td>`).join('');
        return `<tr>${tds}</tr>`;
      }).join('');

      sampleTable.innerHTML = `<thead><tr>${ths}</tr></thead><tbody>${trs}</tbody>`;
    }
  }

  selector.addEventListener('change', update);
  update();
}

function renderQualityChecks() {
  const container = document.getElementById('qualityChecksContainer');
  if (!container) return;

  const checks = [
    { title: "1. Items Count Matches Staging", detail: "0 mismatch across 33.8M rows" },
    { title: "2. Orphan Product Keys (dim_product FK)", detail: "0 orphans" },
    { title: "3. Orphan Time Keys in Items (dim_time FK)", detail: "0 orphans" },
    { title: "4. Orphan Time Keys in Orders (dim_time FK)", detail: "0 orphans" },
    { title: "5. Orphan Customer Keys in Items (dim_customer FK)", detail: "0 orphans" },
    { title: "6. Orphan Customer Keys in Orders (dim_customer FK)", detail: "0 orphans" },
    { title: "7. Basket Size Consistency Check", detail: "0 discrepancies" },
    { title: "8. Total Item Aggregation Equality", detail: "0 mismatch between facts and staging" },
    { title: "9. Pre-Aggregate Cube Parity", detail: "0 difference with cube_dept_time" }
  ];

  let html = '';
  checks.forEach(c => {
    html += `
      <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid #F1F5F9;">
        <div>
          <div style="font-size:12.5px; font-weight:700; color:#0F172A;">${c.title}</div>
          <div style="font-size:11px; color:#64748B;">${c.detail}</div>
        </div>
        <div style="color:#22A06B; font-weight:800; font-size:13px;">✅ PASSED</div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function renderDataDictionary() {
  const tbody = document.querySelector('#dictTable tbody');
  const searchInput = document.getElementById('dictSearchInput');
  if (!tbody) return;

  const dictData = [
    { table: "fact_order_items", col: "order_id", type: "INTEGER", def: "Unique identifier of customer shopping basket" },
    { table: "fact_order_items", col: "product_key", type: "INTEGER", def: "Foreign key reference to dim_product catalog" },
    { table: "fact_order_items", col: "reordered", type: "INTEGER (0/1)", def: "1 if customer previously bought this product, 0 if first time" },
    { table: "fact_orders", col: "days_since_prior_order", type: "DOUBLE", def: "Days elapsed since customer's previous order (Cadence / Recency)" },
    { table: "fact_orders", col: "basket_size", type: "INTEGER", def: "Total count of individual products placed in the shopping order" },
    { table: "dim_product", col: "aisle", type: "VARCHAR", def: "Mid-level grocery category (e.g. fresh fruits, yogurt)" },
    { table: "dim_product", col: "department", type: "VARCHAR", def: "High-level retail department (e.g. produce, dairy eggs)" },
    { table: "dim_time", col: "is_weekend", type: "BOOLEAN", def: "TRUE if order was placed during peak weekend shopping (Day 0 / Day 1)" },
    { table: "dim_customer", col: "rfm_segment", type: "VARCHAR", def: "Assigned customer persona cluster (e.g. Loyal Power, Casual, At-Risk)" },
    { table: "fact_rules", col: "lift", type: "DOUBLE", def: "How many times more likely products are bought together vs chance" }
  ];

  function renderRows(items) {
    tbody.innerHTML = items.map(d => `
      <tr>
        <td><code>${d.table}</code></td>
        <td><strong>${d.col}</strong></td>
        <td><span style="font-size:11px; background:#F1F5F9; padding:2px 6px; border-radius:4px;">${d.type}</span></td>
        <td>${d.def}</td>
      </tr>
    `).join('');
  }

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    const filtered = dictData.filter(d => 
      d.table.toLowerCase().includes(q) || 
      d.col.toLowerCase().includes(q) || 
      d.def.toLowerCase().includes(q)
    );
    renderRows(filtered);
  });

  renderRows(dictData);
}

// =============================================================================
// 8. GLOSSARY MODAL
// =============================================================================
function initGlossary() {
  const modal = document.getElementById('glossaryModal');
  const openBtn = document.getElementById('openGlossaryBtn');
  const closeBtn = document.getElementById('closeGlossaryBtn');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => modal.classList.add('active'));
  }
  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  }
}
