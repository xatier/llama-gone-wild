import json
import pprint
from typing import Any, Generator

import conf
import httpx


headers: dict[str, str] = {
    "Content-type": "application/json",
    "Accept": "application/json",
}

metrics: dict[str, Any] = {}

char = "惠惠"
user = "Master"
USER: dict[str, str] = {
    "avatar": "😈",
    "role": user,
}

BOT: dict[str, str] = {
    "avatar": "❤️‍🔥",
    "role": char,
}

MODE = "default"
# MODE = "IM"
# MODE = "META"

N_PREDICT = 250

params = {
    "api_key": "",
    "cache_prompt": True,
    "frequency_penalty": 0,
    "format": "json",
    "grammar": "",
    "image_data": [],
    "min_keep": 0,
    "min_p": 0.05,
    "mirostat": 0,
    "mirostat_eta": 0.1,
    "mirostat_tau": 5,
    "n_predict": N_PREDICT,
    "n_probs": 0,
    "n_keep": -1,
    "penalize_nl": True,
    "presence_penalty": 0,
    "prompt": (
        "{prompt}\n\n{history}\n<|im_start|>{char}:"
        if MODE == "IM"
        else (
            "{prompt}\n\n{history}\n<|start_header_id|>{char}:"
            if MODE == "META"
            else "{prompt}\n\n{history}\n{char}:"
        )
    ),
    "repeat_last_n": 256,
    "repeat_penalty": 1.18,
    "stop": ["</s>", f"{char}:", f"{user}:", "<|im_end|>", "<|eot_id|>"],
    "stream": True,
    "temperature": 0.75,
    "tfs_z": 1,
    "top_k": 200,
    "top_p": 0.95,
    "typical_p": 1,
}


def load_system() -> str:
    with open(conf.SYSTEM_PROMPT) as f:
        return "".join(f.readlines())


def load_homebrew() -> str:
    with open(conf.CUSTOMIZED) as f:
        return "".join(f.readlines())


def get_metrics() -> dict[str, Any]:
    return metrics


# tokenizer.chat_template
def apply_chat_template(name: str, message: str) -> str:
    if MODE == "IM":
        return f"<|im_start|>{name}: {message}<|im_end|>"
    if MODE == "META":
        return (
            f"<|start_header_id|>{name}<|end_header_id|>: {message}<|eot_id|>"
        )

    return f"{name}: {message}"


def chat(messages: list, setting: str) -> Generator[Any, None, None]:
    p = params.copy()

    history: str = "\n".join(
        apply_chat_template(name=m["actor"]["role"], message=m["content"])
        for m in messages
    )

    print(f"MESSAGE={messages}")
    print(f"HISTORY={history}")

    if conf.HOMEBREW:
        setting = load_homebrew()

    system_prompt: str = (
        load_system()
        .replace("{{{CHARACTER}}}", setting)
        .replace("{{N_PREDICT}}", str(N_PREDICT))
        .replace("{{char}}", char)
        .replace("{{user}}", user)
        .replace(
            "[INST]",
            (
                "<|im_start|>system\n\n"
                if MODE == "IM"
                else (
                    "<|start_header_id|>system<|end_header_id|>\n\n"
                    if MODE == "META"
                    else "[INST]"
                )
            ),
        )
        .replace(
            "[/INST]",
            (
                "<|im_end|>"
                if MODE == "IM"
                else "<|eot_id|>" if MODE == "META" else "[/INST]"
            ),
        )
    )
    p["prompt"] = p["prompt"].format(
        prompt=system_prompt, history=history, char=char
    )

    # ref: ollama/ollama-python/ollama/_client.py
    with httpx.stream(
        "POST", conf.API, headers=headers, json=p, timeout=None
    ) as r:
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            e.response.read()
            raise httpx.ResponseError(
                e.response.text, e.response.status_code
            ) from None

        prefix = "data: "
        for line in r.iter_lines():
            if not line.startswith(prefix):
                continue
            # trim prefix
            line = line.removeprefix(prefix)
            partial = json.loads(line)
            if err := partial.get("error"):
                raise httpx.ResponseError(err)
            if partial.get("stop"):
                global metrics
                metrics = {
                    "timings": partial.get("timings"),
                    "tokens_cached": partial.get("tokens_cached"),
                    "tokens_evaluated": partial.get("tokens_evaluated"),
                    "tokens_predicted": partial.get("tokens_predicted"),
                    "truncated": partial.get("truncated"),
                }
                pprint.pprint(metrics)
                return
            yield partial
