# Kario

Kario is a smart assistant powered by [Ollama](https://ollama.com) and built it to replace Siri. It is still in active
development, so expect bugs and occasional model changes. LLMs and AI in general are never going to be perfect,
especially at this size. If the LLM starts hallucinating, try a different or slightly larger model or rewrite the prompt
to prevent this from happening.

## Installation

Before installing, make sure you have:

- Python 3.13
- [Ollama](https://ollama.com)

I currently test on Apple Silicon only. Windows is not officially supported yet, and some code must be modified for full
compatibility.

### Recommended hardware (tested)

- Apple Silicon (M3 or M4)
- 16 GB RAM

You can change the Ollama model if you want. For speed, I recommend models between 1B and 4B parameters. If you attempt
to modify this to support Windows, I recommend a good GPU like an RTX 3070 or 3080 / 3090 TI and above. I also recommend
the same amount of ram, preferably DDR5. DDR4 works still but may be slower.

### Steps

1. Clone the repository and enter the project folder:

```bash
git clone https://github.com/thebrickmaster626-bit/Kario-Assistant
cd Kario-Assistant
```

2. Create and activate a virtual environment (Python 3.13):

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

If `python` or `python3` already points to Python 3.13 on your machine, you can use that instead.

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Pull the Ollama model:

```bash
ollama pull qwen2.5:3b
```

5. run the assistant. Commands can vary between python version, but it is best to just use your python IDE play button.

```bash
python3.13 main.py
```

## Notes

- The default model may change over time.
- Make sure you have enough disk space for local models (often 1 to 5 GB, depending on model size). I reccomend having
  at least 4 gigabytes for model and perhaps an extra gigabyte for breathing room.
