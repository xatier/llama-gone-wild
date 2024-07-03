from typing import Any, Callable, Generator, Union
import api
import server
import streamlit as st


st.title("llama gone wild")

USER: dict[str, str] = api.USER
BOT: dict[str, str] = api.BOT

# go back if character selected or not initialized
if "char" not in st.session_state or "initialized" not in st.session_state:
    st.switch_page("server.py")

# show character card
server.character_card()


def reply(
    actor: dict[str, str], content: Union[str, Callable], stream: bool = False
) -> None:
    with st.chat_message(actor["role"], avatar=actor["avatar"]):
        if stream:
            st.write_stream(content)
        else:
            st.write(content)


def push(actor: dict[str, str], content: str) -> None:
    st.session_state["messages"].append({"actor": actor, "content": content})


def pop() -> None:
    st.session_state["messages"].pop()


def generate_response() -> Generator[str, None, None]:
    response: Generator[Any, None, None] = api.chat(
        messages=st.session_state["messages"],
        setting=st.session_state["char_setting"],
    )
    for partial_resp in response:
        token: str = partial_resp["content"]
        st.session_state["full_message"] += token
        yield token


def bot_reply() -> None:
    st.session_state["full_message"] = ""
    reply(BOT, generate_response, stream=True)
    push(BOT, st.session_state["full_message"].rstrip("\n"))


# no history, or the bot hasn't finished the reply yet (due to page changes)
if "messages" not in st.session_state or len(st.session_state["messages"]) < 1:
    st.session_state["messages"] = []
    bot_reply()

# print chat history
if "started" in st.session_state:
    for msg in st.session_state["messages"]:
        reply(msg["actor"], msg["content"])

st.session_state["started"] = True

# hack: use internal `st._bottom` container to ensure they are at the bottom
# of the page
# ref: https://github.com/streamlit/streamlit/issues/8198
(
    col1,
    col2,
    col3,
) = st._bottom.empty().columns(  # type: ignore[reportPrivateUsage]
    [0.8, 0.1, 0.1]
)

if prompt := col1.chat_input(placeholder=f'{USER["avatar"]}: Your message'):
    reply(USER, prompt)
    push(USER, prompt)
    bot_reply()

if col2.button("💦", help="continue"):
    bot_reply()

if col3.button("🔙", help="regenerate"):
    pop()
    bot_reply()
    # reload the page to get a fresh print of history
    st.rerun()


metrics: dict[str, Any] = api.get_metrics()
st.caption(
    f"""
    {metrics["tokens_evaluated"]} tokens evaluated,
    {metrics["tokens_predicted"]} tokens predicted,
    {metrics["tokens_cached"]} cached,
    {metrics["timings"]["predicted_per_token_ms"]:.0f}ms per token
    {metrics["timings"]["predicted_per_second"]:.3f} tokens per second
"""
)
