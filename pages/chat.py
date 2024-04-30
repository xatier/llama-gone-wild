import api
import server
import streamlit as st


st.title("llama gone wild")

USER = api.USER
BOT = api.BOT

# go back if character selected or not initialized
if "char" not in st.session_state or "initialized" not in st.session_state:
    st.switch_page("server.py")

# show character card
server.character_card()


def reply(role: str, avatar: str, content, stream: bool = False) -> None:
    with st.chat_message(role, avatar=avatar):
        if stream:
            st.write_stream(content)
        else:
            st.write(content)


def push(role: str, content: str) -> None:
    st.session_state["messages"].append({"role": role, "content": content})


def generate_response():
    response = api.chat(
        messages=st.session_state["messages"], setting=st.session_state["char_setting"]
    )
    for partial_resp in response:
        token = partial_resp["content"]
        st.session_state["full_message"] += token
        yield token


def bot_reply() -> None:
    st.session_state["full_message"] = ""
    reply(BOT["role"], BOT["avatar"], generate_response, stream=True)
    push(BOT["role"], st.session_state["full_message"])


# no history, or the bot hasn't finished the reply yet (due to page changes)
if "messages" not in st.session_state or len(st.session_state["messages"]) < 2:
    st.session_state["messages"] = []
    push(USER["role"], "")
    bot_reply()

# print chat history
if "started" in st.session_state:
    for msg in st.session_state["messages"][1:]:
        reply(
            msg["role"],
            USER["avatar"] if msg["role"] == USER["role"] else BOT["avatar"],
            msg["content"],
        )

st.session_state["started"] = True
if prompt := st.chat_input(placeholder=f'{USER["avatar"]}: Your message'):
    reply(USER["role"], USER["avatar"], prompt)
    push(USER["role"], prompt)
    bot_reply()

metrics = api.get_metrics()
st.caption(
    f"""
    {metrics["tokens_predicted"]} tokens predicted, {metrics["tokens_cached"]} cached
    {metrics["timings"]["predicted_per_token_ms"]:.0f}ms per token
    {metrics["timings"]["predicted_per_second"]:.3f} tokens per second
"""
)
