# Kario

Kario is a smart assistant powered by [Ollama](https://ollama.com). I built it to replace Siri.
The project is still in active development, so expect bugs and occasional model changes.

## Installation

Before installing, make sure you have:

- Python 3.13 (recommended)
- [Ollama](https://ollama.com)

I currently test on Apple Silicon only. Windows is not officially supported yet, and some features require code changes
to work there.

### Recommended Hardware (Tested)

- Apple Silicon (M3 or M4, M5 and future models are supported)
- 16 GB RAM

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

3. Install dependencies:

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

## Notes

- The default model may change over time.
- Keep at least 5 GB of free disk space for local model files.
- macOS-only features currently include `say`, `osascript`, Contacts, Messages, FaceTime, and Spotify automation.
- Remove those if you would like to make the whole thing cross-compatible. I suggest you take the 10 minutes of removing
  it all (or just ask ChatGPT), as I do not have a Windows PC to test on and am not going to maintain an entirely
  separate git repository. 
