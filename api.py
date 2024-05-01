import json
import pprint

import conf
import httpx


headers: dict[str, str] = {
    "Content-type": "application/json",
    "Accept": "application/json",
}

metrics = {}

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
    "n_predict": 160,
    "n_probs": 0,
    "penalize_nl": True,
    "presence_penalty": 0,
    "prompt": "{prompt}\n\n{history}\n{char}:",
    "repeat_last_n": 256,
    "repeat_penalty": 1.18,
    "stop": ["</s>", f"{char}:", f"{user}:"],
    "stream": True,
    "temperature": 0.75,
    "tfs_z": 1,
    "top_k": 80,
    "top_p": 0.95,
    "typical_p": 1,
}


def load_system() -> str:
    with open(conf.SYSTEM_PROMPT) as f:
        return "".join(f.readlines())


def load_homebrew() -> str:
    with open(conf.CUSTOMIZED) as f:
        return "".join(f.readlines())


def get_metrics():
    return metrics


def chat(messages: list, setting: str):
    p = params.copy()

    chat_history_template = "{name}: {message}"

    history = "\n".join(
        chat_history_template.format(name=m["role"], message=m["content"])
        for m in messages
    )

    print(f"MESSAGE={messages}")
    print(f"HISTORY={history}")

    if conf.HOMEBREW:
        setting = load_homebrew()

    system_prompt = (
        load_system()
        .replace("{{{CHARACTER}}}", setting)
        .replace("{{char}}", char)
        .replace("{{user}}", user)
    )
    p["prompt"] = p["prompt"].format(prompt=system_prompt, history=history, char=char)

    # ref: ollama/ollama-python/ollama/_client.py
    with httpx.stream("POST", conf.API, headers=headers, json=p, timeout=None) as r:
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            e.response.read()
            raise httpx.ResponseError(e.response.text, e.response.status_code) from None

        for line in r.iter_lines():
            prefix = "data: "
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
