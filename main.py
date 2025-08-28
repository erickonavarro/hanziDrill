import streamlit as st
import pandas as pd
import random

# ---------- Config ----------
CSV_PATH = "hanzis.csv"
CHOICES_PER_QUESTION = 4
REVIEW_COOLDOWN = 3  # wrong items return after this many questions

# ---------- Data ----------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df = df.rename(columns={c: c.lower() for c in df.columns})
    for c in ["hanzi", "pinyin", "meaning"]:
        df[c] = df[c].astype(str).str.strip()
    return df

df = load_data(CSV_PATH)

# ---------- Initialize State ----------
if "phase" not in st.session_state:
    st.session_state.phase = "question"
    st.session_state.remaining = random.sample(df.to_dict(orient="records"), len(df))
    st.session_state.review = []
    st.session_state.current = None
    st.session_state.options = []
    st.session_state.selected = None
    st.session_state.feedback = None
    st.session_state.correct_answer = None
    st.session_state.step = 0
    st.session_state.qid = 0
    st.session_state.score = {"correct": 0, "wrong": 0}
    st.session_state.submit_clicked = False
    st.session_state.next_clicked = False


# ---------- Helpers ----------
def pick_next_word():
    ready_idx = [i for i, r in enumerate(st.session_state.review) if r["due"] <= st.session_state.step]
    if ready_idx:
        i = random.choice(ready_idx)
        return st.session_state.review.pop(i)["word"]

    if st.session_state.remaining:
        return st.session_state.remaining.pop()

    if st.session_state.review:
        min_due = min(r["due"] for r in st.session_state.review)
        st.session_state.step = min_due
        ready_idx = [i for i, r in enumerate(st.session_state.review) if r["due"] <= st.session_state.step]
        if ready_idx:
            i = random.choice(ready_idx)
            return st.session_state.review.pop(i)["word"]

    return None


def make_options(correct):
    all_meanings = list({m for m in df["meaning"].tolist() if m != correct})
    random.shuffle(all_meanings)
    return random.sample(all_meanings, min(len(all_meanings), CHOICES_PER_QUESTION - 1)) + [correct]


def start_new_question():
    w = pick_next_word()
    if not w:
        st.session_state.phase = "done"
        return

    st.session_state.current = w
    st.session_state.options = make_options(w["meaning"])
    random.shuffle(st.session_state.options)
    st.session_state.selected = None
    st.session_state.feedback = None
    st.session_state.correct_answer = w["meaning"]
    st.session_state.phase = "question"
    st.session_state.qid += 1


def handle_submit():
    sel = st.session_state.selected
    if sel is None:
        st.warning("Please select an answer!")
        return
    if sel == st.session_state.correct_answer:
        st.session_state.feedback = "correct"
        st.session_state.score["correct"] += 1
    else:
        st.session_state.feedback = "wrong"
        st.session_state.score["wrong"] += 1
        st.session_state.review.append(
            {"word": st.session_state.current, "due": st.session_state.step + REVIEW_COOLDOWN}
        )
    st.session_state.phase = "feedback"
    st.session_state.submit_clicked = False


def handle_next():
    st.session_state.step += 1
    start_new_question()
    st.session_state.next_clicked = False


# ---------- UI ----------
st.title("Hanzi Trainer with Review Queue")

# Sidebar stats
with st.sidebar:
    st.markdown("### Progress")
    st.write(f"Correct: {st.session_state.score['correct']}")
    st.write(f"Wrong: {st.session_state.score['wrong']}")
    st.write(f"Review queue: {len(st.session_state.review)}")
    if st.button("Reset session"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# Auto-handle clicks
if st.session_state.submit_clicked:
    handle_submit()
if st.session_state.next_clicked:
    handle_next()

# Load first question if needed
if st.session_state.current is None and st.session_state.phase != "done":
    start_new_question()

# Main flow
if st.session_state.phase == "question" and st.session_state.current:
    hanzi = st.session_state.current["hanzi"]
    pinyin = st.session_state.current["pinyin"]

    st.markdown(f"## {hanzi}  \n*pinyin:* {pinyin}")
    st.session_state.selected = st.radio(
        "Choose the correct meaning:",
        st.session_state.options,
        index=None,
        key=f"q_{st.session_state.qid}"
    )
    if st.button("Submit", key="submit_btn"):
        st.session_state.submit_clicked = True
        st.rerun()

elif st.session_state.phase == "feedback":
    if st.session_state.feedback == "correct":
        st.success("✅ Correct!")
    else:
        st.error(f"❌ Wrong! Correct answer: **{st.session_state.correct_answer}**")
    if st.button("Next", key="next_btn"):
        st.session_state.next_clicked = True
        st.rerun()

elif st.session_state.phase == "done":
    st.success("🎉 All words done!")
    st.write(f"Correct: {st.session_state.score['correct']}, Wrong: {st.session_state.score['wrong']}")
    if st.button("Restart"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
