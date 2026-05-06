import ollama
from ollama import chat
from SpeechToText import record_and_transcribe
from AssistantTools import Apple, Important_Stuff, ModelTools
from pathlib import Path
import keyring
from cryptography.fernet import Fernet
import json
from rich.console import Console
from rich.markdown import Markdown

console = Console()

LLM = "ministral-3:3b"
Has_tool_result = True
Can_speak = False
history = Path("chathistory.txt")
username = "Salvatore"

if keyring.get_password("Kario", "Keyring_encryption_backend") is None:
    key = Fernet.generate_key().decode()

    keyring.set_password("Kario", "Keyring_encryption_backend", key)
    key = None

def encrypt(text):
    password = keyring.get_password("Kario", "Keyring_encryption_backend")

    if password is None:
        key = Fernet.generate_key().decode()
        keyring.set_password("Kario", "Keyring_encryption_backend", key)
        password = key

    fernet = Fernet(password.encode())
    encrypted = fernet.encrypt(text.encode())
    return encrypted.decode()

def decrypt(text):
    fernet = Fernet(keyring.get_password("Kario", "Keyring_encryption_backend").encode())
    decrypted = fernet.decrypt(text.encode()).decode()
    return decrypted

OPTIONS = {
    "num_ctx": 3072,
    "num_predict": 280,
    "temperature": 0.25,
    "top_p": 0.88,
    "top_k": 24,
    "repeat_penalty": 1.14,
    "num_thread": 8,
}

system_prompt = Path("Prompt.txt").read_text(encoding="utf-8")
console.print(Markdown("LLM running! Model:"))
console.print(Markdown(LLM))

if history.exists():
    if history.read_bytes() == b"":
        messages = encrypt(json.dumps([{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username}."}])).encode()
        history.write_bytes(messages)
        messages = None
    else:
        if input("Would you like to clear chat history (y/n):") == "y":
            messages = encrypt(json.dumps([{"role": "system", "content": system_prompt}])).encode()
            history.write_bytes(messages)
            messages = None
else:
    history.touch()

while True:
    if Can_speak:
        prompt = record_and_transcribe()
    else:
        prompt = input("> ")
    if "computer" in prompt.lower() or "assistant" in prompt.lower() or Can_speak == False:
        messages = json.loads(decrypt(history.read_bytes().decode()))
        messages.append({'role': 'user', 'content': prompt})
        history.write_bytes(encrypt(json.dumps(messages)).encode())
        messages = None
        tools = [
            ModelTools.get_weather,
            ModelTools.get_date_and_time,
            ModelTools.search_the_web,
            ModelTools.start_timer,
            ModelTools.stop_timer,
            ModelTools.stop_all_timers,
            Apple.send_imessage,
            Apple.call_number,
        ]

        # First request
        response = ollama.chat(
            model=LLM,
            messages=json.loads(decrypt(history.read_bytes().decode())),
            tools=tools,
            think=False,
            options=OPTIONS,
        )
        response_text = (response.message.content or "").strip()
        if response_text:
            console.print(Markdown(response_text))

        # If it did call any tools, handle them
        if response.message.tool_calls:
            for call in response.message.tool_calls:
                Has_tool_result = False
                name = call.function.name
                args = call.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                console.print(Markdown(f"ran tool {name}"))
                console.print(Markdown(f"args: {args}"))
                if name == "get_weather":
                    tool_result = ModelTools.get_weather()
                    Has_tool_result = True
                elif name == "search_the_web":
                    tool_result = Important_Stuff.safe_call(ModelTools.search_the_web, args)
                    Has_tool_result = True
                elif name == "start_timer":
                    tool_result = Important_Stuff.safe_call(ModelTools.start_timer, args)
                    Has_tool_result = False
                elif name == "stop_timer":
                    Important_Stuff.safe_call(ModelTools.stop_timer, args)
                    Has_tool_result = False
                elif name == "stop_all_timers":
                    ModelTools.stop_all_timers()
                    Has_tool_result = False
                elif name == "send_imessage":
                    Important_Stuff.safe_call(Apple.send_imessage, args)
                    Has_tool_result = False
                elif name == "call_number":
                    Important_Stuff.safe_call(Apple.call_number, args)
                    Has_tool_result = False
                elif name == "get_date_and_time":
                    tool_result = ModelTools.get_date_and_time()
                    Has_tool_result = True
                else:
                    tool_result = "Unknown tool"

                if Has_tool_result:
                    messages = json.loads(decrypt(history.read_bytes().decode()))
                    messages.append({
                        "role": "tool",
                        "tool_name": name,
                        "content": tool_result,
                    })
                    history.write_bytes(encrypt(json.dumps(messages)).encode())

                # Ask the model for a *second* response after the tool results ONLY if the tool was to get data, if it is to execute actions then this will be skipped
                if Has_tool_result:
                    response = chat(
                        model=LLM,
                        messages=json.loads(decrypt(history.read_bytes().decode())),
                        think=False,
                        options=OPTIONS,
                        tools=tools,
                    )
                if response.message.content != "":
                    messages = json.loads(decrypt(history.read_bytes().decode()))
                    if Has_tool_result:
                        messages.pop()
                        messages.append({'role': 'assistant', 'content': response.message.content})
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": "Tool ran successfully.",
                        })
                    history.write_bytes(encrypt(json.dumps(messages)).encode())
                    messages = None
                    console.print(Markdown(response.message.content))
                    Important_Stuff.speak(response.message.content)
        else:
            Important_Stuff.speak(response_text)

        # clear chat history to preserve space and memory
        messages = json.loads(decrypt(history.read_bytes().decode()))
        if len(messages) > 14:
            console.print(Markdown("too many messages! cutting off old ones..."))
            messages.pop(2)
            messages.pop(2)
        history.write_bytes(encrypt(json.dumps(messages)).encode())