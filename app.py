"""Streamlit Tarot Reading: original Waite meanings, RWS illustrations, private history."""

from __future__ import annotations

import html
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from openai import OpenAI
from tarot_core import draw, load_cards

BASE_DIR = Path(__file__).resolve().parent
st.set_page_config(page_title="韦特塔罗 · Tarot Reading", page_icon="🔮", layout="wide")

st.markdown("""
<style>
.stApp {background: radial-gradient(ellipse at top, #191630 0%, #0e1020 62%, #0c0d15 100%);}
.block-container {max-width: 1100px; padding-top: 2rem;}
h1,h2,h3 {letter-spacing: .035em;}
.tarot-intro {color:#d1c6ea; margin-bottom:1.2rem;}
.tarot-panel {background:rgba(42,35,72,.42); border:1px solid rgba(230,206,145,.20);
              border-radius:16px; padding:14px 13px 17px; text-align:center;}
.tarot-panel img {width:100%; max-width:240px; height:auto; aspect-ratio:0.59; object-fit:contain;
                  border-radius:7px; box-shadow:0 8px 24px rgba(0,0,0,.3); background:#231e33;}
.tarot-panel img.reversed {transform:rotate(180deg);}
.tarot-card-title {font-size:1.1rem; font-weight:650; color:#f7e6b8; margin-top:10px;}
.tarot-card-en {font-size:.84rem;color:#c7bed9;min-height:20px;}
.tarot-card-pos {font-size:.9rem;color:#e2c97a;margin-top:5px;}
.history-controls {display:flex; flex-wrap:wrap; gap:9px;align-items:center;margin:10px 0;}
.history-search {flex:1; min-width:190px; padding:9px 12px; background:#1a1930;color:#eee;
 border:1px solid #57516f;border-radius:9px;}
.history-action,.history-remove {cursor:pointer;border:1px solid #68607c;background:#2a2542;color:#eee;
 padding:8px 12px;border-radius:8px;}
.history-action:hover,.history-remove:hover {border-color:#e2c97a;}
.history-danger {color:#f2b5b5;}
.history-status {font-size:.88rem;color:#b6abc8;}
.history-item {background:#211d36;border:1px solid #3c3550;border-radius:12px;padding:13px 16px;margin:10px 0;}
.history-item-heading {display:flex;justify-content:space-between;align-items:center;gap:10px;}
.history-time,.history-cards {font-size:.88rem;color:#c8bdd8;}
.history-question {color:#fff;margin:7px 0;font-weight:600;white-space:pre-wrap;overflow-wrap:anywhere;}
.history-empty,.history-error {padding:17px;color:#c9bed9;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=24 * 60 * 60)
def get_cards():
    return load_cards()


def draw_picture(card: dict, orientation: str = "正位"):
    """The inverted card itself is rotated, not merely its caption."""
    name = html.escape(card["name"])
    image = html.escape(card["image"], quote=True)
    zh = html.escape(card["name_zh"])
    cls = "reversed" if orientation == "逆位" else ""
    st.markdown(f'''<div class="tarot-panel">
        <img src="{image}" class="{cls}" alt="{name}" loading="lazy">
        <div class="tarot-card-title">{zh}</div>
        <div class="tarot-card-en">{name}</div>
        <div class="tarot-card-pos">{orientation}</div>
      </div>''', unsafe_allow_html=True)


def original_text(card: dict, orientation: str):
    main_key = "waite_reversed" if orientation == "逆位" else "waite_upright"
    other_key = "waite_upright" if orientation == "逆位" else "waite_reversed"
    first = orientation
    second = "正位" if orientation == "逆位" else "逆位"
    st.markdown(f"**Waite 原著 · {first}**")
    st.write(card[main_key])
    st.caption(f"原著另一个方向（{second}）：{card[other_key]}")
    additional = card.get("additional_reversed" if orientation == "逆位" else "additional_upright")
    if additional:
        st.caption(f"原著附加释义：{additional}")


def ai_interpret(question: str, cards: list[dict], lookup: dict, api_key: str) -> str:
    descriptions = []
    for item in cards:
        card = lookup[item["id"]]
        key = "waite_reversed" if item["orientation"] == "逆位" else "waite_upright"
        descriptions.append(f"{item['name_zh']} / {item['name']}（{item['orientation']}）: Waite 原文：{card[key]}")
    prompt = f"用户问题：{question.strip() or '未指定具体问题'}\n抽出的牌：\n" + "\n".join(descriptions)
    result = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=45).chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是中文塔罗解读助手。严格参考提供的 A. E. Waite 1911 年原著释义，不得把现代常见关键词伪装成原文。"
             "先以中文准确转述每张牌的原著意义，再根据用户的问题分析牌与牌之间的联系，最后提供现实可操作的思考建议。"
             "清楚区分原著描述和你自己的情境推论；塔罗只用于象征和自我反思，不声称能确定预测现实事件。简洁、不重复。"},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )
    return result.choices[0].message.content or "模型未返回内容"


def show_history(pending: dict | None):
    # Encode as a JS literal. Escaping '<' prevents text such as '</script>' in questions
    # from prematurely ending the script and executing untrusted markup.
    payload = json.dumps(pending, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = (BASE_DIR / "history.js").read_text(encoding="utf-8").replace("__DRAW_ENTRY__", payload)
    st.html(f'<div id="tarot-history-mount"></div><script>{script}</script>', unsafe_allow_javascript=True)


st.title("✧ 韦特塔罗 · Tarot Reading")
st.markdown('<div class="tarot-intro">78 张经典 Rider–Waite–Smith 牌面 · Waite 原著正逆位释义 · 本机私密记录</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("解读设置")
    api_key = st.text_input("DeepSeek API Key（可选）", type="password", help="不填仍可抽牌、查看原文、保存记录；Key 不写入历史。")
    st.caption("AI 解读仅在你点击生成时调用 DeepSeek。历史记录不会存储 AI 内容。")
    st.divider()
    st.caption("牌义：《The Pictorial Key to the Tarot》（A. E. Waite，1911）；原著英文。")
    st.markdown("[查看 Waite 原著](https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot)")

try:
    cards = get_cards()
except Exception as error:
    st.error("无法加载 78 张 Waite 原著牌义。请检查网络后重试，或先运行：python scripts/build_waite_data.py")
    st.caption(f"技术信息：{type(error).__name__}: {error}")
    st.stop()

lookup = {card["id"]: card for card in cards}
for k, initial in (("last_cards", None), ("last_question", ""), ("last_ai", ""), ("pending_history", None)):
    st.session_state.setdefault(k, initial)

tab_draw, tab_history, tab_library = st.tabs(["🔮 抽牌与解读", "📜 历史记录", "📚 78 张牌库"])

with tab_draw:
    st.subheader("提出一个问题")
    question = st.text_area("问题（可以留空）", placeholder="最近我该把精力放在哪个方向？", max_chars=1000, height=88)
    count = st.select_slider("抽牌张数", options=[1, 2, 3], value=3)
    if st.button("✦ 开始抽牌", type="primary", use_container_width=True):
        selected = draw(cards, count)
        st.session_state["last_cards"] = selected
        st.session_state["last_question"] = question.strip()
        st.session_state["last_ai"] = ""
        st.session_state["pending_history"] = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": question.strip(),
            "cards": selected,
        }
    if st.session_state["last_cards"]:
        selected = st.session_state["last_cards"]
        cols = st.columns(len(selected))
        for col, item in zip(cols, selected):
            with col:
                card = lookup[item["id"]]
                draw_picture(card, item["orientation"])
                with st.expander("📖 Waite 原著牌义", expanded=True):
                    original_text(card, item["orientation"])
        st.divider()
        st.subheader("中文综合解读（可选）")
        if st.button("通过 DeepSeek 生成中文解读", disabled=not bool(api_key)):
            with st.spinner("正在根据 Waite 原文生成中文解读…"):
                try:
                    st.session_state["last_ai"] = ai_interpret(st.session_state["last_question"], selected, lookup, api_key)
                except Exception as error:
                    st.error(f"DeepSeek 调用失败：{type(error).__name__}: {error}")
        if not api_key:
            st.caption("需要中文 AI 解读时，在左侧填写自己的 DeepSeek API Key。抽牌、原文和历史不依赖 Key。")
        if st.session_state["last_ai"]:
            st.markdown(st.session_state["last_ai"])
    else:
        st.info("抽出 1–3 张牌后，可查看完整牌面、正逆位和 Waite 原著含义。")

with tab_history:
    st.subheader("历史记录")
    st.caption("仅保存抽牌时间、可选问题、牌名与正逆位。记录仅存在当前浏览器 localStorage；换设备、换浏览器或清除网站数据后不会自动同步。")
    show_history(st.session_state["pending_history"])
    st.session_state["pending_history"] = None

with tab_library:
    st.subheader("查看 78 张牌")
    names = {f"{card['name_zh']} · {card['name']}": card for card in cards}
    chosen_label = st.selectbox("选择卡牌", list(names), index=0)
    chosen = names[chosen_label]
    left, right = st.columns([1, 2], vertical_alignment="top")
    with left:
        draw_picture(chosen)
    with right:
        st.markdown("**Waite 原著 · 正位**")
        st.write(chosen["waite_upright"])
        st.markdown("**Waite 原著 · 逆位**")
        st.write(chosen["waite_reversed"])
        if chosen.get("additional_upright") or chosen.get("additional_reversed"):
            with st.expander("原著补充牌义"):
                st.write("正位：", chosen.get("additional_upright") or "—")
                st.write("逆位：", chosen.get("additional_reversed") or "—")
        st.caption("原著英语保留历史措辞。上下文解读与原始词义应当分开看待。")

st.caption("图片：Pamela Colman Smith（1909），牌面由 sixseeds/tarot-api 提供；牌义整理数据：StarTarotOnline/tarot-rws-dataset（CC BY 4.0）。")
