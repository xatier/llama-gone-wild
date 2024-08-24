# llama gone wild

This is an exercise for learning
[streamlit](https://github.com/streamlit/streamlit/)'s new chat element APIs.
Nothing more, nothing less.

## setup

You need the followings:

- [llama.cpp](https://github.com/ggerganov/llama.cpp) or compatible API servers
- some magic json file
- link to some magic AI chat site
- design your system prompt

Refer to `conf.py.example` for details.

```bash
python -m venv venv
source venv/bin/activate

streamlit run server.py
```

## screenshots

character card

![1](images/1.png)

character descriptions and scenarios

![2](images/2.png)

fun chat

![3](images/3.png)

screenshot with newly added features:

- `continue` and `regenerate` buttons
- automatic reply (branches)

![4](images/4.png)
