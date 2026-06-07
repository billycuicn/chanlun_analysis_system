const state = {
  klines: [],
  pens: [],
  segments: [],
  zhongshu: [],
  signals: [],
  summary: {},
  config: {},
  drawing: false,
  draftStart: null,
  overlays: [],
  chartReady: false,
};

const chartNode = document.getElementById("chart");
const statusText = document.getElementById("statusText");
const drawPanel = document.getElementById("drawPanel");
const summaryPanel = document.getElementById("summaryPanel");
const analysisPanel = document.getElementById("analysisPanel");
const penList = document.getElementById("penList");
const obsidianInput = document.getElementById("obsidianInput");

let tvChart = null;
let candleSeries = null;

function setStatus(text) {
  statusText.textContent = text;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

function initChart() {
  if (tvChart || !window.LightweightCharts) return;
  tvChart = LightweightCharts.createChart(chartNode, {
    layout: { background: { color: "#ffffff" }, textColor: "#172026" },
    grid: { vertLines: { color: "#edf1f5" }, horzLines: { color: "#edf1f5" } },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: "#dce3ea" },
    timeScale: { borderColor: "#dce3ea", timeVisible: true },
  });
  candleSeries = tvChart.addCandlestickSeries({
    upColor: "#cf3f3f",
    downColor: "#138a63",
    borderUpColor: "#cf3f3f",
    borderDownColor: "#138a63",
    wickUpColor: "#cf3f3f",
    wickDownColor: "#138a63",
  });
  tvChart.subscribeClick(handleChartClick);
  window.addEventListener("resize", resizeChart);
  resizeChart();
  state.chartReady = true;
}

function resizeChart() {
  if (!tvChart) return;
  const rect = chartNode.getBoundingClientRect();
  tvChart.applyOptions({ width: Math.floor(rect.width), height: Math.floor(rect.height) });
}

function toChartTime(dt) {
  return Math.floor(new Date(String(dt).replace(" ", "T")).getTime() / 1000);
}

function timeKey(time) {
  return String(time);
}

function klineByTime(time) {
  const key = timeKey(time);
  return state.klines.find((item) => timeKey(item.chartTime) === key);
}

function clearOverlays() {
  state.overlays.forEach((series) => tvChart.removeSeries(series));
  state.overlays = [];
  if (candleSeries && candleSeries.setMarkers) candleSeries.setMarkers([]);
}

function addLine(points, color, width = 2, style = LightweightCharts.LineStyle.Solid) {
  const series = tvChart.addLineSeries({
    color,
    lineWidth: width,
    lineStyle: style,
    lastValueVisible: false,
    priceLineVisible: false,
  });
  series.setData(points);
  state.overlays.push(series);
}

function renderChart() {
  initChart();
  if (!tvChart || !candleSeries) return;
  clearOverlays();
  state.klines.forEach((item, index) => {
    item.chartTime = toChartTime(item.dt);
    item.index = index;
  });
  candleSeries.setData(state.klines.map((item) => ({
    time: item.chartTime,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  })));
  drawPens();
  drawSegments();
  drawZhongshu();
  drawSignals();
  tvChart.timeScale().fitContent();
}

function drawPens() {
  state.pens.forEach((pen) => {
    const start = state.klines.find((item) => item.dt === pen.start_dt);
    const end = state.klines.find((item) => item.dt === pen.end_dt);
    if (!start || !end) return;
    addLine(
      [
        { time: start.chartTime, value: pen.start_price },
        { time: end.chartTime, value: pen.end_price },
      ],
      pen.direction === "上" ? "#cf3f3f" : "#138a63",
      2
    );
  });
}

function drawSegments() {
  state.segments.forEach((segment) => {
    const start = state.klines.find((item) => item.dt === segment["起点时间"]);
    const end = state.klines.find((item) => item.dt === segment["终点时间"]);
    if (!start || !end) return;
    addLine(
      [
        { time: start.chartTime, value: segment["起点价"] },
        { time: end.chartTime, value: segment["终点价"] },
      ],
      "#245fc8",
      3
    );
  });
}

function drawZhongshu() {
  state.zhongshu.forEach((zone) => {
    const start = state.klines.find((item) => item.dt === zone["起点时间"]);
    const end = state.klines.find((item) => item.dt === zone["终点时间"]);
    if (!start || !end) return;
    addLine([{ time: start.chartTime, value: zone.ZG }, { time: end.chartTime, value: zone.ZG }], "#9a620f", 1, LightweightCharts.LineStyle.Dashed);
    addLine([{ time: start.chartTime, value: zone.ZD }, { time: end.chartTime, value: zone.ZD }], "#9a620f", 1, LightweightCharts.LineStyle.Dashed);
  });
}

function drawSignals() {
  if (!candleSeries.setMarkers) return;
  const markers = state.signals
    .filter((item) => item["类型"] !== "三买/三卖")
    .map((item) => ({
      time: toChartTime(item["时间"]),
      position: item["类型"].includes("买") ? "belowBar" : "aboveBar",
      color: item["类型"].includes("买") ? "#cf3f3f" : "#138a63",
      shape: item["类型"].includes("买") ? "arrowUp" : "arrowDown",
      text: item["类型"],
    }));
  candleSeries.setMarkers(markers);
}

async function refresh() {
  const data = await api("/api/v2/state");
  state.klines = data.klines;
  state.pens = data.pens;
  state.segments = data.segments;
  state.zhongshu = data.zhongshu;
  state.signals = data.signals;
  state.summary = data.summary || {};
  state.config = data.config || {};
  obsidianInput.value = state.config.obsidian_vault || "";
  renderChart();
  renderPanels();
  setStatus(`K线 ${state.klines.length} 根，手工笔 ${state.pens.length} 条，线段 ${state.segments.length} 条`);
}

function renderPanels() {
  renderDrawPanel();
  renderSummary();
  renderAnalysis();
  renderPens();
}

function renderDrawPanel() {
  if (!state.drawing) {
    drawPanel.textContent = "点击“画笔”进入画笔模式。第一笔点起点和终点，后续默认从上一笔终点开始。";
    return;
  }
  if (state.draftStart) {
    drawPanel.textContent = `起点：${state.draftStart.dt} @ ${state.draftStart.price.toFixed(2)}。请点击终点。`;
  } else {
    drawPanel.textContent = state.pens.length
      ? `已自动使用上一笔终点作为起点：${state.pens[state.pens.length - 1].end_dt}。请点击终点。`
      : "请点击第一笔起点。";
  }
}

function renderSummary() {
  const high = state.summary["最近高点"];
  const low = state.summary["最近低点"];
  summaryPanel.innerHTML = `
    <div class="item"><strong>结构定位</strong>${state.summary["结构定位"] || "暂无"}</div>
    <div class="item"><strong>最近线段</strong>${state.summary["最近线段方向"] || "暂无"}</div>
    <div class="item"><strong>最近高低点</strong>
      高点：${high ? `${Number(high["价格"]).toFixed(2)} @ ${high["时间"]}` : "暂无"}<br>
      低点：${low ? `${Number(low["价格"]).toFixed(2)} @ ${low["时间"]}` : "暂无"}
    </div>
  `;
}

function renderAnalysis() {
  const latestZone = state.zhongshu[state.zhongshu.length - 1];
  const latestSignal = state.signals[state.signals.length - 1];
  analysisPanel.innerHTML = `
    <div class="item"><strong>线段</strong>${state.segments.length ? state.segments.map((item) => `${item.id}${item["方向"]}`).join("，") : "暂无"}</div>
    <div class="item"><strong>中枢</strong>${latestZone ? `${latestZone.id} ${latestZone["类型"]} [${latestZone.ZD.toFixed(2)}, ${latestZone.ZG.toFixed(2)}]` : "暂无"}</div>
    <div class="item"><strong>最新买卖点</strong>${latestSignal ? `${latestSignal["类型"]} @ ${Number(latestSignal["价格"]).toFixed(2)}，${latestSignal["状态"]}` : "暂无"}</div>
  `;
}

function renderPens() {
  if (!state.pens.length) {
    penList.innerHTML = '<div class="hint">暂无手工笔。</div>';
    return;
  }
  penList.innerHTML = state.pens.map((pen) => `
    <div class="item">
      <span class="tag ${pen.direction === "上" ? "up" : "down"}">B${pen.index}${pen.direction}</span>
      ${pen.start_dt} → ${pen.end_dt}<br>
      ${pen.start_price.toFixed(2)} → ${pen.end_price.toFixed(2)}，${pen.kline_count}根K线
      <div class="note-row">
        <input id="note-${pen.index}" value="${escapeHtml(pen.note || "")}" placeholder="标注，如 一卖/低点1/待确认">
        <div class="button-row">
          <button class="secondary" data-save-note="${pen.index}">保存标注</button>
          <button class="danger" data-delete-pen="${pen.index}">删除</button>
        </div>
      </div>
    </div>
  `).join("");
  document.querySelectorAll("[data-save-note]").forEach((node) => {
    node.addEventListener("click", () => saveNote(Number(node.dataset.saveNote)));
  });
  document.querySelectorAll("[data-delete-pen]").forEach((node) => {
    node.addEventListener("click", () => deletePen(Number(node.dataset.deletePen)));
  });
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function pointFromClick(param) {
  const kline = klineByTime(param.time);
  if (!kline || !param.point) return null;
  const highCoord = candleSeries.priceToCoordinate(kline.high);
  const lowCoord = candleSeries.priceToCoordinate(kline.low);
  const useHigh = Math.abs(param.point.y - highCoord) <= Math.abs(param.point.y - lowCoord);
  return {
    dt: kline.dt,
    index: kline.index,
    price: useHigh ? kline.high : kline.low,
  };
}

async function handleChartClick(param) {
  if (!state.drawing) return;
  const point = pointFromClick(param);
  if (!point) return;
  if (!state.draftStart) {
    const lastPen = state.pens[state.pens.length - 1];
    if (lastPen) {
      state.draftStart = {
        dt: lastPen.end_dt,
        price: lastPen.end_price,
        index: state.klines.findIndex((item) => item.dt === lastPen.end_dt),
      };
    } else {
      state.draftStart = point;
      renderDrawPanel();
      return;
    }
  }
  try {
    await api("/api/v2/pens", {
      method: "POST",
      body: JSON.stringify({
        start_dt: state.draftStart.dt,
        start_price: state.draftStart.price,
        end_dt: point.dt,
        end_price: point.price,
      }),
    });
    state.draftStart = null;
    await refresh();
  } catch (error) {
    setStatus(error.message);
  }
}

async function saveNote(index) {
  const note = document.getElementById(`note-${index}`).value;
  await api(`/api/v2/pens/${index}`, { method: "PATCH", body: JSON.stringify({ note }) });
  await refresh();
}

async function deletePen(index) {
  await api(`/api/v2/pens/${index}`, { method: "DELETE" });
  await refresh();
}

document.getElementById("fetchBtn").addEventListener("click", async () => {
  try {
    setStatus("正在补齐中证1000 30分钟K线...");
    const result = await api("/api/v2/fetch", { method: "POST" });
    setStatus(`已采集 ${result.count} 根K线，最新一根：${result.latest_dt} @ ${result.latest_close}`);
    await refresh();
  } catch (error) {
    setStatus(error.message);
  }
});

document.getElementById("drawBtn").addEventListener("click", () => {
  state.drawing = !state.drawing;
  state.draftStart = null;
  document.getElementById("drawBtn").textContent = state.drawing ? "退出画笔" : "画笔";
  renderDrawPanel();
});

document.getElementById("undoBtn").addEventListener("click", async () => {
  const result = await api("/api/v2/undo", { method: "POST" });
  setStatus(result.message);
  await refresh();
});

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  await api("/api/v2/analyze", { method: "POST" });
  await refresh();
});

document.getElementById("reportBtn").addEventListener("click", async () => {
  try {
    const result = await api("/api/v2/report", { method: "POST" });
    setStatus(result.obsidian_path ? `报告已生成并推送：${result.obsidian_path}` : `报告已生成：${result.local_path}`);
  } catch (error) {
    setStatus(error.message);
  }
});

document.getElementById("saveConfigBtn").addEventListener("click", async () => {
  await api("/api/v2/config", { method: "POST", body: JSON.stringify({ obsidian_vault: obsidianInput.value.trim() }) });
  await refresh();
});

async function boot() {
  initChart();
  try {
    await api("/api/v2/fetch", { method: "POST" });
  } catch (error) {
    setStatus(error.message);
  }
  await refresh();
}

boot().catch((error) => setStatus(error.message));

