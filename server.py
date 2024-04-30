import json
import random
import textwrap
from typing import Any, Optional

import conf
import streamlit as st


db: dict[Any, Any] = {}


def load() -> None:
    with open(conf.FILE) as f:
        lines = f.readlines()

    j = json.loads("".join(lines))

    # ['tag', 'featuredCharacters', 'topCharacters', 'newCharacters', 'relatedTags', 'charactersByRelatedTagId'])
    for p in j:
        for c in p["featuredCharacters"]:
            add(c, db)

        for c in p["topCharacters"]:
            add(c, db)

        for c in p["newCharacters"]:
            add(c, db)

        for tag in p["charactersByRelatedTagId"]:
            for c in p["charactersByRelatedTagId"][tag]:
                add(c, db)


def add(c: dict, db: dict) -> None:
    if c["_id"] not in db:
        c["description"] = (
            c["description"].replace("\r\n", ". ").replace(c["name"], "{{char}}")
        )
        c["scenario"] = (
            c["scenario"].replace("\r\n", ". ").replace(c["name"], "{{char}}")
        )
        db[c["_id"]] = c


def search(keyword: str, db: dict) -> Optional[dict]:
    keyword = keyword.lower()
    results = {}
    for c in db.values():
        i = c["_id"]
        tags = [t["title"] for t in c["tags"]]

        if i not in results and "Male" not in tags:
            if (
                keyword in c["name"].lower()
                or keyword in c["description"].lower()
                or keyword in c["scenario"].lower()
                or keyword in " ".join(c["traits"]).lower()
                or keyword in " ".join(tags).lower()
            ):
                results[i] = c

    st.session_state["char_search_results"] = results

    if len(results) == 0:
        return None

    return random.choice(list(results.values()))


def character_card() -> None:
    c = st.session_state["char"]
    st.subheader(c["name"])
    st.write(f'URL: {conf.SITE}/characters/details?characterId={c["_id"]}')
    st.markdown(f'```text\nTags: {[t["title"] for t in c["tags"]]}\n```')
    st.image(c["imageUrl"])
    st.markdown(st.session_state["char_setting"])


st.title("llama gone wild")
load()

search_term = st.text_input(f"Character search ({len(db)} characters loaded)", "tits")
c = st.session_state.get("char", search(search_term, db))

if st.button("Refresh") or search_term != st.session_state.get("search_term", ""):
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
        if "messages" in st.session_state:
            del st.session_state["messages"]
        if "started" in st.session_state:
            del st.session_state["started"]
        st.session_state["initialized"] = True
        st.switch_page("pages/chat.py")
