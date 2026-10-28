/* Private, browser-only draw history. No API key or AI response is saved. */
(() => {
  "use strict";
  const mount = document.getElementById("tarot-history-mount");
  if (!mount) return;
  const KEY = "tarot_reading_history_v2";
  const incoming = __DRAW_ENTRY__;

  const element = (tag, className, value) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  };
  const load = () => {
    const raw = localStorage.getItem(KEY);
    const result = raw === null ? [] : JSON.parse(raw);
    if (!Array.isArray(result)) throw Error("历史记录格式异常");
    return result;
  };
  const save = (items) => localStorage.setItem(KEY, JSON.stringify(items));
  const cardLabel = (item) => (item.name_zh || item.name || "未知卡牌") + "（" + (item.orientation || "？") + "）";
  const notice = element("div", "history-notice");
  const controls = element("div", "history-controls");
  const status = element("p", "history-status");
  const list = element("div", "history-list");
  const search = element("input", "history-search");
  search.type = "search";
  search.placeholder = "搜索问题或牌名";
  search.setAttribute("aria-label", "搜索历史记录");
  const exportButton = element("button", "history-action", "导出 JSON");
  const clearButton = element("button", "history-action history-danger", "清空记录");
  controls.append(search, exportButton, clearButton);
  mount.replaceChildren(notice, controls, status, list);

  let rows;
  try {
    rows = load();
    if (incoming && incoming.id && !rows.some(row => row.id === incoming.id)) {
      // Save exactly: time, optional question and drawn card names/orientations.
      const safeEntry = {
        id: String(incoming.id), created_at: String(incoming.created_at),
        question: String(incoming.question || ""),
        cards: Array.isArray(incoming.cards) ? incoming.cards.map(c => ({
          id: String(c.id), name: String(c.name), name_zh: String(c.name_zh),
          orientation: String(c.orientation)
        })) : []
      };
      rows.unshift(safeEntry);
      save(rows);
    }
  } catch (error) {
    mount.replaceChildren(element("p", "history-error", "浏览器存储不可用或记录损坏，无法保证历史记录持久保存。请检查浏览器设置。"));
    return;
  }

  function render() {
    const query = search.value.trim().toLowerCase();
    const filtered = rows.filter(row =>
      String(row.question || "").toLowerCase().includes(query) ||
      (row.cards || []).some(c => cardLabel(c).toLowerCase().includes(query) || String(c.name || "").toLowerCase().includes(query))
    );
    status.textContent = `本浏览器保存 ${rows.length} 次抽牌 · 当前显示 ${filtered.length} 条`;
    list.replaceChildren();
    if (!filtered.length) {
      list.append(element("p", "history-empty", rows.length ? "没有匹配的记录" : "尚无记录，抽牌后会自动保存在这里"));
      return;
    }
    for (const row of filtered) {
      const item = element("article", "history-item");
      const heading = element("div", "history-item-heading");
      const when = Number.isFinite(Date.parse(row.created_at)) ? new Date(row.created_at).toLocaleString("zh-CN", {hour12:false}) : "历史记录";
      heading.append(element("span", "history-time", when));
      const remove = element("button", "history-remove", "删除");
      remove.setAttribute("aria-label", "删除此条历史记录");
      remove.onclick = () => {
        rows = rows.filter(r => r.id !== row.id);
        save(rows);
        render();
      };
      heading.append(remove);
      item.append(heading);
      item.append(element("div", "history-question", row.question || "（未填写问题）"));
      item.append(element("div", "history-cards", (row.cards || []).map(cardLabel).join(" · ")));
      list.append(item);
    }
  }

  search.oninput = render;
  exportButton.onclick = () => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], {type: "application/json;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const anchor = element("a");
    anchor.href = url;
    anchor.download = "tarot_history.json";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  clearButton.onclick = () => {
    if (!rows.length || !window.confirm("确定清空这个浏览器保存的全部塔罗历史记录吗？")) return;
    rows = [];
    save(rows);
    render();
  };
  render();
})();
