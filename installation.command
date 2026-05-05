git clone https://github.com/thebrickmaster626-bit/Kario-Assistant
cd Kario-Assistant
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
ollama pull qwen2.5:3b
say "Assistant is ready to run. Before using, please make sure Ollama is open and that the server is on."