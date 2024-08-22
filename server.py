import json
import random
import textwrap
from typing import Any, Optional

import api
import conf
import streamlit as st


db: dict[Any, Any] = {}


def load_db() -> dict[Any, Any]:
    with open(conf.DB_FILE) as f:
        lines: list[str] = f.readlines()

    db = json.loads("".join(lines))
    print(f"{len(db)} characters loaded")
    return db


def search(keyword: str, db: dict) -> Optional[dict]:
    keyword = keyword.lower()
    results = {}
    for c in db.values():
        i = c["_id"]
        tags = [t["title"] for t in c["tags"]]

        if (
            i not in results
            and "Male" not in tags
            and (
                keyword in c["name"].lower()
                or keyword in c["description"].lower()
                or keyword in c["scenario"].lower()
                or keyword in " ".join(c["traits"]).lower()
                or keyword in " ".join(tags).lower()
            )
        ):
            results[i] = c

    st.session_state["char_search_results"] = results

    return random.choice(list(results.values())) if results else None


def character_card() -> None:
    if not conf.HOMEBREW:
        c = st.session_state["char"]
        st.subheader(c["name"])
        st.write(f'URL: {conf.SITE}/characters/details?characterId={c["_id"]}')
        st.markdown(f'```text\nTags: {[t["title"] for t in c["tags"]]}\n```')
        st.image(c["imageUrl"])
        st.markdown(st.session_state["char_setting"])
    else:
        st.subheader("Homebrew mode")
        st.markdown(api.load_homebrew())


st.title("llama gone wild")
db = load_db()

if st.button("Toggle homebrew mode"):
    conf.HOMEBREW = not conf.HOMEBREW

search_term = st.text_input(
    f"Character search ({len(db)} characters loaded)",
    st.session_state.get("search_term", "tits"),
)
c = st.session_state.get("char", search(search_term, db))

if st.button("Refresh") or search_term != st.session_state.get(
    "search_term", ""
):
    c = search(search_term, db)

st.write(f'found {len(st.session_state["char_search_results"])} results')

if c is not None:
    st.session_state["char"] = c
    st.session_state["search_term"] = search_term
    st.session_state["char_setting"] = textwrap.dedent(
        f"""
            [Description: {c["description"]}]

            [Scenario: {c["scenario"]}]

            [Traits: You MUST act with the following characteristics: {c["traits"]}]
    """
    )

    character_card()

    if st.button("💦 Start Chat"):
        for state in ("messages", "started", "autoreplies"):
            if state in st.session_state:
                del st.session_state[state]
        st.session_state["initialized"] = True
        st.switch_page("pages/chat.py")
