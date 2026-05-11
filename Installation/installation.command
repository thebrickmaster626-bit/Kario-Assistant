read "DEST?Enter the full folder path where you want the project to be cloned: "
cd "$DEST" || exit 1

git clone https://github.com/thebrickmaster626-bit/Kario-Assistant
cd Kario-Assistant
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r Installation/requirements.txt
ollama pull qwen2.5:3b-instruct-q8_0
ollama pull ministral-3:3b
ollama serve
echo "Assistant is ready to run."