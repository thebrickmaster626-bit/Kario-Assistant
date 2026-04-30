# Kario

Kario is a smart assistant powered by [Ollama](https://ollama.com). I built it to replace Siri.
The project is still in active development, so expect bugs and sometimes frequent model changes.

## Installation

Before installing, make sure you have:

- Python 3.13 (recommended)
- [Ollama](https://ollama.com)

I currently test on Apple Silicon only. Windows is not officially supported yet, and some features require code changes
to work there.

### Recommended Hardware (Tested)

- Apple Silicon (M3 or M4, M5 and future models are supported)
- 16 GB RAM, 8 GB ram is most likely the bare minimum you can use

You can change the Ollama model if you want. For speed, I recommend models between 1B and 4B parameters. Also, if you
use Intel Macs, expect it to be ***VERY*** slow.

## Setup Steps

1. Clone the repository and enter the project folder:

```sh
git clone https://github.com/thebrickmaster626-bit/Kario-Assistant
cd Kario-Assistant
```

2. Create and activate a virtual environment:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
```

If that doesn't work, use the command below:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
```

If `python` or `python3` already points to Python 3.13 on your machine, you can use that instead.

3. Install libraries:

```sh
pip install -r requirements.txt
```

4. Pull the Ollama model:

```sh
ollama pull qwen2.5:3b
```

5. Run the assistant:

```sh
python main.py
```

## How to use

Run the command above, and just say "hey computer" or "computer" and then continue the rest of your prompt. There is
currently no GUI, as I want the whole thing to be voice-oriented like Alexa or Siri. Also, please note the wake word
detection is just seeing if the wakeword is in the prompt, so it may not be totally accurate.

## Notes

- The default model may change over time.
- Keep at least 5 GB of free disk space for local model files.
- macOS-only features currently include `say`, `osascript`, Contacts, Messages, FaceTime, and Spotify automation.
- Remove the class `Apple_Integration` and rewrite the `say` function if you would like to make the whole thing cross-compatible. I suggest you take the 10 minutes of removing
  it all (or just ask ChatGPT), as I do not have a Windows PC to test on and am not going to maintain an entirely
  separate git repository. 
