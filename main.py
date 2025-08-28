import streamlit as st
import pandas as pd
import random

# ---------- Config ----------
CSV_EN_PATH = "hanzi_en.csv"
CSV_ES_PATH = "hanzi_es.csv"
CHOICES_PER_QUESTION = 4
REVIEW_COOLDOWN = 3  # wrong items return after this many questions

# ---------- Translations ----------
TRANSLATIONS = {
    "en": {
        "title": "Hanzi Trainer with Multiple Modes",
        "select_language": "Select Language",
        "english": "English",
        "spanish": "Spanish",
        "mode_selection": "Select a Practice Mode",
        "mode1": "Mode 1: Hanzi to Meaning",
        "mode1_desc": "See a Hanzi with Pinyin, choose the correct meaning",
        "mode2": "Mode 2: Pinyin to Hanzi",
        "mode2_desc": "See Pinyin with meaning, choose the correct Hanzi",
        "mode3": "Mode 3: Meaning to Hanzi",
        "mode3_desc": "See meaning only, choose the correct Hanzi",
        "mode4": "Mode 4: Hanzi to Pinyin",
        "mode4_desc": "See Hanzi only, choose the correct Pinyin",
        "progress": "Progress",
        "correct": "Correct",
        "wrong": "Wrong",
        "review_queue": "Review queue",
        "reset_session": "Reset session",
        "choose_meaning": "Choose the correct meaning:",
        "choose_hanzi": "Choose the correct Hanzi:",
        "choose_pinyin": "Choose the correct Pinyin:",
        "submit": "Submit",
        "next": "Next",
        "correct_answer": "✅ Correct!",
        "wrong_answer": "❌ Wrong!",
        "all_done": "🎉 All words done!",
        "restart": "Restart",
        "please_select": "Please select an answer!",
        "correct_answer_text": "Correct answer:",
        "you_selected": "You selected:",
        "select": "Select",
        "mode": "Mode",
        "meaning": "meaning",  # Added missing translation
        "pinyin": "pinyin"  # Added missing translation
    },
    "es": {
        "title": "Entrenador de Hanzi con Múltiples Modos",
        "select_language": "Selecciona el Idioma",
        "english": "Inglés",
        "spanish": "Español",
        "mode_selection": "Selecciona un Modo de Práctica",
        "mode1": "Modo 1: Hanzi a Significado",
        "mode1_desc": "Ver un Hanzi con Pinyin, elegir el significado correcto",
        "mode2": "Modo 2: Pinyin a Hanzi",
        "mode2_desc": "Ver Pinyin con significado, elegir el Hanzi correcto",
        "mode3": "Modo 3: Significado a Hanzi",
        "mode3_desc": "Ver solo el significado, elegir el Hanzi correcto",
        "mode4": "Modo 4: Hanzi a Pinyin",
        "mode4_desc": "Ver solo el Hanzi, elegir el Pinyin correcto",
        "progress": "Progreso",
        "correct": "Correctas",
        "wrong": "Incorrectas",
        "review_queue": "Cola de repaso",
        "reset_session": "Reiniciar sesión",
        "choose_meaning": "Elige el significado correcto:",
        "choose_hanzi": "Elige el Hanzi correcto:",
        "choose_pinyin": "Elige el Pinyin correcto:",
        "submit": "Enviar",
        "next": "Siguiente",
        "correct_answer": "✅ Correcto!",
        "wrong_answer": "❌ Incorrecto!",
        "all_done": "🎉 Todas las palabras completadas!",
        "restart": "Reiniciar",
        "please_select": "Por favor selecciona una respuesta!",
        "correct_answer_text": "Respuesta correcta:",
        "you_selected": "Seleccionaste:",
        "select": "Seleccionar",
        "mode": "Modo",
        "meaning": "significado",  # Added missing translation
        "pinyin": "pinyin"  # Added missing translation
    }
}


# ---------- Data ----------
@st.cache_data
def load_data(language):
    path = CSV_EN_PATH if language == "en" else CSV_ES_PATH
    df = pd.read_csv(path)
    df = df.rename(columns={c: c.lower() for c in df.columns})
    for c in ["hanzi", "pinyin", "meaning"]:
        df[c] = df[c].astype(str).str.strip()
    return df


# ---------- Initialize State ----------
if "phase" not in st.session_state:
    st.session_state.phase = "language_selection"
    st.session_state.language = None
    st.session_state.mode = None
    st.session_state.df = None
    st.session_state.remaining = []
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
def t(key):
    """Get translation for the current language"""
    return TRANSLATIONS[st.session_state.language][key]


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


def make_options(correct, mode):
    if mode == 1:  # Hanzi + Pinyin -> Choose Meaning
        all_meanings = list({m for m in st.session_state.df["meaning"].tolist() if m != correct})
        random.shuffle(all_meanings)
        return random.sample(all_meanings, min(len(all_meanings), CHOICES_PER_QUESTION - 1)) + [correct]
    elif mode == 2:  # Pinyin + Meaning -> Choose Hanzi
        all_hanzis = list({h for h in st.session_state.df["hanzi"].tolist() if h != correct})
        random.shuffle(all_hanzis)
        return random.sample(all_hanzis, min(len(all_hanzis), CHOICES_PER_QUESTION - 1)) + [correct]
    elif mode == 3:  # Meaning -> Choose Hanzi
        all_hanzis = list({h for h in st.session_state.df["hanzi"].tolist() if h != correct})
        random.shuffle(all_hanzis)
        return random.sample(all_hanzis, min(len(all_hanzis), CHOICES_PER_QUESTION - 1)) + [correct]
    else:  # mode == 4: Hanzi -> Choose Pinyin
        all_pinyins = list({p for p in st.session_state.df["pinyin"].tolist() if p != correct})
        random.shuffle(all_pinyins)
        return random.sample(all_pinyins, min(len(all_pinyins), CHOICES_PER_QUESTION - 1)) + [correct]


def start_new_question():
    w = pick_next_word()
    if not w:
        st.session_state.phase = "done"
        return

    st.session_state.current = w

    if st.session_state.mode == 1:
        st.session_state.correct_answer = w["meaning"]
    elif st.session_state.mode in [2, 3]:
        st.session_state.correct_answer = w["hanzi"]
    else:  # mode == 4
        st.session_state.correct_answer = w["pinyin"]

    st.session_state.options = make_options(st.session_state.correct_answer, st.session_state.mode)
    random.shuffle(st.session_state.options)
    st.session_state.selected = None
    st.session_state.feedback = None
    st.session_state.phase = "question"
    st.session_state.qid += 1


def handle_submit():
    sel = st.session_state.selected
    if sel is None:
        st.warning(t("please_select"))
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


def select_language(language):
    st.session_state.language = language
    st.session_state.df = load_data(language)
    st.session_state.remaining = random.sample(st.session_state.df.to_dict(orient="records"),
                                               len(st.session_state.df))
    st.session_state.phase = "mode_selection"


def select_mode(mode):
    st.session_state.mode = mode
    st.session_state.phase = "question"
    start_new_question()


def get_word_info(word):
    if st.session_state.mode == 1:
        return f"{word['hanzi']} ({t('pinyin')}: {word['pinyin']}, {t('meaning')}: {word['meaning']})"
    elif st.session_state.mode == 2:
        return f"{word['hanzi']} ({t('pinyin')}: {word['pinyin']}, {t('meaning')}: {word['meaning']})"
    elif st.session_state.mode == 3:
        return f"{word['hanzi']} ({t('pinyin')}: {word['pinyin']}, {t('meaning')}: {word['meaning']})"
    else:  # mode == 4
        return f"{word['pinyin']} ({t('meaning')}: {word['meaning']})"


# ---------- UI ----------
# Language selection
if st.session_state.phase == "language_selection":
    st.title("Hanzi Trainer")
    st.header(TRANSLATIONS["en"]["select_language"])  # Show in English since no language selected yet

    col1, col2 = st.columns(2)

    with col1:
        if st.button(TRANSLATIONS["en"]["english"], key="lang_en"):
            select_language("en")

    with col2:
        if st.button(TRANSLATIONS["en"]["spanish"], key="lang_es"):
            select_language("es")

# Main app after language selection
elif st.session_state.language and st.session_state.df is not None:
    st.title(t("title"))

    # Mode selection
    if st.session_state.phase == "mode_selection":
        st.header(t("mode_selection"))
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.subheader(t("mode1"))
            st.write(t("mode1_desc"))
            if st.button(t("select"), key="mode1"):
                select_mode(1)

        with col2:
            st.subheader(t("mode2"))
            st.write(t("mode2_desc"))
            if st.button(t("select"), key="mode2"):
                select_mode(2)

        with col3:
            st.subheader(t("mode3"))
            st.write(t("mode3_desc"))
            if st.button(t("select"), key="mode3"):
                select_mode(3)

        with col4:
            st.subheader(t("mode4"))
            st.write(t("mode4_desc"))
            if st.button(t("select"), key="mode4"):
                select_mode(4)

    # Sidebar stats
    with st.sidebar:
        st.markdown(f"### {t('progress')}")
        if st.session_state.mode:
            st.write(f"{t('mode')}: {st.session_state.mode}")
        st.write(f"{t('correct')}: {st.session_state.score['correct']}")
        st.write(f"{t('wrong')}: {st.session_state.score['wrong']}")
        st.write(f"{t('review_queue')}: {len(st.session_state.review)}")
        if st.button(t("reset_session")):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # Auto-handle clicks
    if st.session_state.submit_clicked:
        handle_submit()
    if st.session_state.next_clicked:
        handle_next()

    # Main flow
    if st.session_state.phase == "question" and st.session_state.current:
        if st.session_state.mode == 1:
            hanzi = st.session_state.current["hanzi"]
            pinyin = st.session_state.current["pinyin"]
            st.markdown(f"## {hanzi}  \n*{t('pinyin')}:* {pinyin}")
            question_text = t("choose_meaning")
        elif st.session_state.mode == 2:
            pinyin = st.session_state.current["pinyin"]
            meaning = st.session_state.current["meaning"]
            st.markdown(f"## {pinyin}  \n*{t('meaning')}:* {meaning}")
            question_text = t("choose_hanzi")
        elif st.session_state.mode == 3:
            meaning = st.session_state.current["meaning"]
            st.markdown(f"## {meaning}")
            question_text = t("choose_hanzi")
        else:  # mode == 4
            hanzi = st.session_state.current["hanzi"]
            st.markdown(f"## {hanzi}")
            question_text = t("choose_pinyin")

        st.session_state.selected = st.radio(
            question_text,
            st.session_state.options,
            index=None,
            key=f"q_{st.session_state.qid}"
        )
        if st.button(t("submit"), key="submit_btn"):
            st.session_state.submit_clicked = True
            st.rerun()

    elif st.session_state.phase == "feedback":
        if st.session_state.feedback == "correct":
            current = st.session_state.current
            if st.session_state.mode == 1:
                st.success(t("correct_answer"))
            elif st.session_state.mode in [2, 3, 4]:
                st.success(f"{t('correct_answer')} {get_word_info(current)}")
        else:
            current = st.session_state.current
            selected = st.session_state.selected

            if st.session_state.mode == 1:
                st.error(f"{t('wrong_answer')} {t('correct_answer_text')} **{st.session_state.correct_answer}**")
            elif st.session_state.mode in [2, 3]:
                # Find the selected hanzi in the dataset to get its info
                selected_word = next((item for item in st.session_state.df.to_dict(orient="records")
                                      if item["hanzi"] == selected), None)
                if selected_word:
                    st.error(f"{t('wrong_answer')} {t('you_selected')}: {get_word_info(selected_word)}")
                else:
                    st.error(f"{t('wrong_answer')} {t('you_selected')}: {selected}")
                st.error(f"{t('correct_answer_text')} {get_word_info(current)}")
            else:  # mode == 4
                # Find the selected pinyin in the dataset to get its info
                selected_word = next((item for item in st.session_state.df.to_dict(orient="records")
                                      if item["pinyin"] == selected), None)
                if selected_word:
                    st.error(f"{t('wrong_answer')} {t('you_selected')}: {get_word_info(selected_word)}")
                else:
                    st.error(f"{t('wrong_answer')} {t('you_selected')}: {selected}")
                st.error(f"{t('correct_answer_text')} {get_word_info(current)}")

        if st.button(t("next"), key="next_btn"):
            st.session_state.next_clicked = True
            st.rerun()

    elif st.session_state.phase == "done":
        st.success(t("all_done"))
        st.write(
            f"{t('correct')}: {st.session_state.score['correct']}, {t('wrong')}: {st.session_state.score['wrong']}")
        if st.button(t("restart")):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()