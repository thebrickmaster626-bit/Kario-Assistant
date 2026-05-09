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
    "num_ctx": 2560,
    "num_predict": 215,
    "temperature": 0.15,
    "top_p": 0.86,
    "top_k": 15,
    "repeat_penalty": 1.14,
    "num_thread": 7,
    "num_batch": 270
}

system_prompt = Path("Prompt.md").read_text(encoding="utf-8")
console.print(Markdown("LLM running! Model:"))
console.print(Markdown(LLM))

if history.exists():
    if history.read_bytes() == b"":
        messages = encrypt(json.dumps([{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date_and_time()}."}])).encode()
        history.write_bytes(messages)

    else:
        if "y" in input("Would you like to clear chat history (y/n):").lower() :
            messages = encrypt(json.dumps([{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date_and_time()}."}])).encode()
            history.write_bytes(messages)

else:
    history.touch()

while True:
    if Can_speak:
        prompt = record_and_transcribe()
    else:
        prompt = input("> ")
    if "computer" in prompt.lower() or "assistant" in prompt.lower() or Can_speak == False:
        messages = json.loads(decrypt(history.read_bytes().decode()))
        messages.append({"role": "user", "content": prompt})
        messages[1] = {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date_and_time()}."}
        history.write_bytes(encrypt(json.dumps(messages)).encode())

        tools = [
            ModelTools.get_weather,
            ModelTools.search_the_web,
            ModelTools.start_timer,
            ModelTools.stop_timer,
            ModelTools.stop_all_timers,
            Apple.send_imessage,
            Apple.call_number,
            Apple.set_reminder,
        ]

        # First request
        response = ollama.chat(
            model=LLM,
            messages=json.loads(decrypt(history.read_bytes().decode())),
            tools=tools,
            think=False,
            options=OPTIONS,
        )
        gen_tps = response.eval_count / (response.eval_duration / 1e9)
        prompt_tps = response.prompt_eval_count / (response.prompt_eval_duration / 1e9)
        prompt_seconds = response.prompt_eval_duration / 1e9
        print("gen_tps:", round(gen_tps, 2))
        print("prompt_tps:", round(prompt_tps, 2))
        print("prompt eval sec:", round(prompt_seconds, 4))
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
                    tool_result = "Timer has been stopped."
                    Has_tool_result = False
                elif name == "stop_all_timers":
                    ModelTools.stop_all_timers()
                    tool_result = "All timers have been stopped."
                    Has_tool_result = False
                elif name == "send_imessage":
                    Important_Stuff.safe_call(Apple.send_imessage, args)
                    tool_result = "Message has been sent."
                    Has_tool_result = False
                elif name == "call_number":
                    Important_Stuff.safe_call(Apple.call_number, args)
                    tool_result = "A call has been successfully initiated."
                    Has_tool_result = False
                elif name == "set_reminder":
                    Important_Stuff.safe_call(Apple.set_reminder, args)
                    tool_result = "Reminder has been set."
                    Has_tool_result = False
                else:
                    tool_result = "Unknown tool"
                    Has_tool_result = True

                messages = json.loads(decrypt(history.read_bytes().decode()))
                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": tool_result,
                })
                history.write_bytes(encrypt(json.dumps(messages)).encode())
                # Ask the model for a *second* response after the tool results ONLY if the tool was to get data, if it is to execute actions only then this will be skipped
                if Has_tool_result:
                    response = ollama.chat(
                        model=LLM,
                        messages=json.loads(decrypt(history.read_bytes().decode())),
                        think=False,
                        options=OPTIONS,
                        tools=tools,
                    )
                    gen_tps = response.eval_count / (response.eval_duration / 1e9)
                    prompt_tps = response.prompt_eval_count / (response.prompt_eval_duration / 1e9)
                    prompt_seconds = response.prompt_eval_duration / 1e9
                    print("gen_tps:", round(gen_tps, 2))
                    print("prompt_tps:", round(prompt_tps, 2))
                    print("prompt eval sec:", round(prompt_seconds, 4))

                    messages = json.loads(decrypt(history.read_bytes().decode()))
                    messages.append({"role": "assistant", "content": response.message.content})
                    history.write_bytes(encrypt(json.dumps(messages)).encode())
                    console.print(Markdown(response.message.content))
                    Important_Stuff.speak(response.message.content)
                else:
                    messages = json.loads(decrypt(history.read_bytes().decode()))
                    messages.append({"role": "assistant", "content": "Task has been completed successfully! How else can i assist you today?"})
                    history.write_bytes(encrypt(json.dumps(messages)).encode())
        else:
            Important_Stuff.speak(response_text)
            messages = json.loads(decrypt(history.read_bytes().decode()))
            messages.append({"role": "assistant", "content": response.message.content})
            history.write_bytes(encrypt(json.dumps(messages)).encode())

        # clear chat history to preserve space and memory
        messages = json.loads(decrypt(history.read_bytes().decode()))
        # Get turns
        turns = 0
        i = 1
        first_real_message = 0
        # set the starting index automatically in case system messages change
        while True:
            if messages[i].get("role").lower() == "system":
                i += 1
            else:
                first_real_message = (i - 1)
                break

        # Get turns
        while True:
            if i >= len(messages):
                break
            if messages[i].get("role").lower() == "tool":
                i += 3
            else:
                i += 2
            turns += 1

        if turns >= 4:
            console.print(Markdown("too many messages! cutting off old ones..."))
            if messages[first_real_message].get("role").lower() == "tool":
                for i in range(3):
                    messages.pop(2)
            else:
                for i in range(2):
                    messages.pop(2)
        history.write_bytes(encrypt(json.dumps(messages)).encode())
