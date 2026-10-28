"""Tarot Reader: keep the original Streamlit interface, add card images,
Waite's original card meanings, and private browser history.

Requires the tarot_core.py and history.js already in the GitHub repository.
"""

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

# --- Original page configuration ---
st.set_page_config(page_title="AI Tarot Reader", page_icon="🔮", layout="centered")

# --- Original dark card styling (only extended to display the pictures) ---
st.markdown("""
<style>
    .card-box {
        background-color: #2E2E2E;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #4F4F4F;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .card-image {
        width: 100%;
        max-width: 180px;
        aspect-ratio: 0.58;
        object-fit: contain;
        border-radius: 5px;
        background: #222;
    }
    .card-image.reversed { transform: rotate(180deg); }
    .card-name { font-size: 18px; font-weight: bold; color: #FFD700; margin-top: 10px; }
    .card-pos { font-size: 14px; color: #AAAAAA; font-style: italic; }
    .card-name-cn { font-size: 13px; color: #BBBBBB; }
</style>
""", unsafe_allow_html=True)

# --- Original sidebar ---
with st.sidebar:
    st.header("🔮 Settings")
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.info("Your API key is not saved and is only used for this session.")

@st.cache_data(show_spinner=False, ttl=86400)
def load_tarot_data():
    return load_cards()


def show_card(card: dict, orientation: str) -> None:
    image = html.escape(card["image"], quote=True)
    name = html.escape(card["name"])
    name_cn = html.escape(card["name_zh"])
    direction = "Upright" if orientation == "正位" else "Reversed"
    css_class = "reversed" if orientation == "逆位" else ""
    st.markdown(f"""
      <div class="card-box">
        <img src="{image}" class="card-image {css_class}" alt="{name}" loading="eager">
        <div class="card-name">{name}</div>
        <div class="card-name-cn">{name_cn}</div>
        <div class="card-pos">{direction}</div>
      </div>
    """, unsafe_allow_html=True)


def show_waite_meanings(card: dict, orientation: str) -> None:
    # Quote the original text exactly, in English; it is not modern keyword shorthand.
    field = "waite_upright" if orientation == "正位" else "waite_reversed"
    other_field = "waite_reversed" if orientation == "正位" else "waite_upright"
    st.markdown(f"**Waite original ({'Upright' if orientation == '正位' else 'Reversed'})**")
    st.write(card[field])
    st.caption("Other orientation: " + card[other_field])
    extra = card.get("additional_upright" if orientation == "正位" else "additional_reversed")
    if extra:
        st.caption("Additional meaning: " + extra)


def interpret_with_ai(question: str, drawn: list[dict], by_id: dict, api_key: str) -> str:
    descriptions = []
    for item in drawn:
        card = by_id[item["id"]]
        meaning_key = "waite_upright" if item["orientation"] == "正位" else "waite_reversed"
        descriptions.append(
            f"{card['name']} / {card['name_zh']} ({item['orientation']}): "
            f"Waite original meaning: {card[meaning_key]}"
        )
    prompt = (
        f"I want to know: {question or 'No specific question'}\n"
        "I drew these cards:\n" + "\n".join(descriptions)
    )
    response = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=45).chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": (
                "You are a skilled tarot reader who speaks Chinese. "
                "Answer questions directly, be concise and avoid repetition. "
                "First explain each card's original Waite meaning and upright/reversed nuance, "
                "then interpret the cards together in the context of the question; "
                "end with key uncertainty and practical advice. "
                "Keep original historical card meanings separate from your interpretation. "
                "Do not make false claims of certainty."
            )},
            {"role": "user", "content": prompt},
        ],
        stream=False,
    )
    return response.choices[0].message.content or "The model returned no interpretation."


def show_history(new_entry: dict | None) -> None:
    # JS only writes time, question, card names and orientations to browser storage.
    payload = json.dumps(new_entry, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = (BASE_DIR / "history.js").read_text(encoding="utf-8").replace("__DRAW_ENTRY__", payload)
    # st.html executes JS in an isolated component when enabled. History stays local
    # to the user's browser; it is never written to the GitHub repo.
    st.html(
        f"""<style>
            body {{ background:transparent; color:inherit; font-family:sans-serif; }}
            .history-controls {{ display:flex;flex-wrap:wrap;gap:7px;margin:10px 0; }}
            .history-search {{ flex:1;min-width:130px;padding:8px;border:1px solid #777;border-radius:6px; }}
            .history-action,.history-remove {{ border:1px solid #777;border-radius:6px;padding:7px;cursor:pointer; }}
            .history-item {{ border-bottom:1px solid #777; padding:9px 2px; }}
            .history-item-heading {{ display:flex; justify-content:space-between;align-items:center; }}
            .history-question {{ margin:7px 0;overflow-wrap:anywhere; }}
            .history-time,.history-cards,.history-status {{ opacity:.78;font-size:.9em; }}
            </style><div id="tarot-history-mount"></div><script>{script}</script>""",
        unsafe_allow_javascript=True,
    )

# --- Original single-page flow ---
st.title("🔮 DeepSeek AI Tarot Reader")
st.write("Focus on your question, and let the AI interpret the cards for you.")

try:
    data_tarot = load_tarot_data()
except Exception as err:
    st.error("Card data could not be loaded. Check the app's network connection.")
    st.caption(f"{type(err).__name__}: {err}")
    st.stop()

by_id = {card["id"]: card for card in data_tarot}
for key, default in (
    ("tarot_drawn", None),
    ("tarot_question", ""),
    ("tarot_interpretation", ""),
    ("tarot_ai_error", ""),
    ("tarot_new_history", None),
):
    st.session_state.setdefault(key, default)

question = st.text_input("What do you want to ask the cards?", "How is my month going?")

if st.button("Draw Cards & Read", type="primary"):
    selected = draw(data_tarot, 3)
    st.session_state["tarot_drawn"] = selected
    st.session_state["tarot_question"] = question.strip()
    st.session_state["tarot_interpretation"] = ""
    st.session_state["tarot_ai_error"] = ""
    st.session_state["tarot_new_history"] = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": question.strip(),
        "cards": selected,
    }
    if api_key:
        with st.spinner("Consulting the spirits (and DeepSeek)..."):
            try:
                st.session_state["tarot_interpretation"] = interpret_with_ai(question.strip(), selected, by_id, api_key)
            except Exception as err:
                st.session_state["tarot_ai_error"] = f"DeepSeek error: {type(err).__name__}: {err}"

if st.session_state["tarot_drawn"]:
    selection = st.session_state["tarot_drawn"]
    cols = st.columns(3)
    for col, item in zip(cols, selection):
        with col:
            card = by_id[item["id"]]
            show_card(card, item["orientation"])
            with st.expander("📖 Waite original meaning"):
                show_waite_meanings(card, item["orientation"])

    st.markdown("---")
    st.subheader("📜 The Interpretation")
    if st.session_state["tarot_ai_error"]:
        st.error(st.session_state["tarot_ai_error"])
    if st.session_state["tarot_interpretation"]:
        st.write(st.session_state["tarot_interpretation"])
    elif not api_key:
        st.info("Enter your DeepSeek API Key in the sidebar for the AI interpretation. You can still draw cards and read their original meanings without it.")
    if api_key and not st.session_state["tarot_interpretation"]:
        if st.button("Generate the AI interpretation"):
            with st.spinner("Consulting the spirits (and DeepSeek)..."):
                try:
                    st.session_state["tarot_interpretation"] = interpret_with_ai(
                        st.session_state["tarot_question"], selection, by_id, api_key
                    )
                    st.rerun()
                except Exception as err:
                    st.error(f"DeepSeek error: {type(err).__name__}: {err}")

# The new tools are below the original reading interface, collapsed by default.
with st.expander("📜 History · 历史抽牌记录"):
    st.caption("仅保存问题、时间、牌面和正逆位；不会保存 AI 回答或 API Key。记录仅留在当前浏览器。")
    show_history(st.session_state["tarot_new_history"])
st.session_state["tarot_new_history"] = None

with st.expander("📚 All 78 cards · 韦特原始牌义查询"):
    labels = {f"{card['name']} · {card['name_zh']}": card for card in data_tarot}
    selected_label = st.selectbox("Choose a card", list(labels.keys()), key="card_lookup")
    card = labels[selected_label]
    st.image(card["image"], width=135)
    st.markdown("**Upright (Waite original)**")
    st.write(card["waite_upright"])
    st.markdown("**Reversed (Waite original)**")
    st.write(card["waite_reversed"])

st.caption("Waite original meanings: The Pictorial Key to the Tarot (1911). Rider–Waite–Smith artwork: Pamela Colman Smith (1909).")
