import ollama
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
try:
    history = Path("chathistory.txt")
except FileNotFoundError:
    pass
username = "Salvatore"
response_text = ""

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
        history.write_bytes(b"")

    fernet = Fernet(password.encode())
    encrypted = fernet.encrypt(text.encode())
    return encrypted.decode()

def decrypt(text):
    fernet = Fernet(keyring.get_password("Kario", "Keyring_encryption_backend").encode())
    decrypted = fernet.decrypt(text.encode()).decode()
    return decrypted

OPTIONS = {
    "num_ctx": 1080,
    "num_predict": 150,
    "temperature": 0.05,
    "top_p": 0.77,
    "top_k": 5,
    "repeat_penalty": 1.04,
    "num_thread": 8,
    "num_batch": 520,
    "num_gpu": 99999,
}

system_prompt = Path("Prompt.md").read_text(encoding="utf-8")
console.print(Markdown("LLM running! Model:"))
console.print(Markdown(LLM))

if history.exists():
    if history.read_bytes() == b"":
        messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date()}."}]
        history.write_bytes(encrypt(json.dumps(messages)).encode())

    else:
        if "y" in input("Would you like to clear chat history (y/n):").lower() :
            messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date()}."}]
            history.write_bytes(encrypt(json.dumps(messages)).encode())
else:
    history.touch()

try:
    messages = json.loads(decrypt(history.read_bytes().decode()))
except Exception as e:
    print(e)
    if keyring.get_password("Kario", "Keyring_encryption_backend") is None:
        key = Fernet.generate_key().decode()

        keyring.set_password("Kario", "Keyring_encryption_backend", key)
        key = None

    messages = [{"role": "system", "content": system_prompt}, {"role": "system", "content": f"The user's name is {username} and today's date is {ModelTools.get_date()}."}]
    history.write_bytes(encrypt(json.dumps(messages)).encode())

while True:
    try:
        if Can_speak:
            prompt = record_and_transcribe()
        else:
            prompt = input("> ")
        if "computer" in prompt.lower() or "assistant" in prompt.lower() or Can_speak == False:
            messages.append({"role": "user", "content": prompt})
            history.write_bytes(encrypt(json.dumps(messages)).encode())

            try:
                # First request
                response = ollama.chat(
                    model=LLM,
                    messages=messages,
                    tools=[Important_Stuff.run_action, Apple.compose],
                    think=False,
                    options=OPTIONS,
                )
                response_text = response.message.content.strip()
                gen_tps = response.eval_count / (response.eval_duration / 1e9)
                prompt_tps = response.prompt_eval_count / (response.prompt_eval_duration / 1e9)
                prompt_seconds = response.prompt_eval_duration / 1e9
                print("gen_tps:", round(gen_tps, 2))
                print("prompt_tps:", round(prompt_tps, 2))
                print("prompt eval sec:", round(prompt_seconds, 4))
                print("conversation tokens:", response.prompt_eval_count)
            except Exception as e:
                response = "an error occurred in the LLM:", str(e)
                print("an error occurred in the LLM:", str(e))
                messages.append({"role": "assistant", "content": "Sorry, I'm having trouble right now. " + str(e)})
                history.write_bytes(encrypt(json.dumps(messages)).encode())

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

                    try:
                        if name == "run_action":
                            tool_result = Important_Stuff.run_action(**args)
                            if tool_result == "Action ran successfully but has no result":
                                has_tool_result = False
                            else:
                                has_tool_result = True
                        elif name == "compose":
                            tool_result = Important_Stuff.run_action("compose", **args)
                            has_tool_result = False
                        else:
                            tool_result = "Unknown tool"
                            Has_tool_result = True

                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": tool_result,
                        })
                        history.write_bytes(encrypt(json.dumps(messages)).encode())
                    except Exception as e:
                        print("a tool error has occurred:", str(e))
                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": "An error has occurred."
                        })
                        history.write_bytes(encrypt(json.dumps(messages)).encode())
                    # Ask the model for a *second* response after the tool results ONLY if the tool was to get data, if it is to execute actions only then this will be skipped
                    if Has_tool_result:
                        response = ollama.chat(
                            model=LLM,
                            messages=messages,
                            think=False,
                            options=OPTIONS,
                            tools=[Important_Stuff.run_action],
                        )
                        response_text = response.message.content.strip()
                        gen_tps = response.eval_count / (response.eval_duration / 1e9)
                        prompt_tps = response.prompt_eval_count / (response.prompt_eval_duration / 1e9)
                        prompt_seconds = response.prompt_eval_duration / 1e9
                        print("gen_tps:", round(gen_tps, 2))
                        print("prompt_tps:", round(prompt_tps, 2))
                        print("prompt eval sec:", round(prompt_seconds, 4))
                        print("conversation tokens:", response.prompt_eval_count)

                        messages.append({"role": "assistant", "content": response_text})
                        history.write_bytes(encrypt(json.dumps(messages)).encode())
                        console.print(Markdown(response_text))
                        Important_Stuff.speak(response_text)
                    else:
                        messages.append({"role": "assistant", "content": "Task has been completed successfully! How else can i assist you today?"})
                        history.write_bytes(encrypt(json.dumps(messages)).encode())
            else:
                # an attempt to see if the AI has hallucinated and outputted args directly, if so then output a warning and attempt to parse it
                try:
                    if "{" in response_text:
                        import warnings
                        warnings.warn("LLM has hallucinated! Please tweak the prompt or change the model.", UserWarning)
                        first_brace_index = response_text.find('{')
                        response_text = response_text[first_brace_index:]
                        response_text = json.loads(json.dumps(json.loads(response_text), indent=None))
                        tool_result = Important_Stuff.run_action(response_text.get("func"), response_text.get("args"))
                        Has_tool_result = bool(tool_result)

                        messages.append({
                            "role": "tool",
                            "tool_name": "run_action",
                            "content": tool_result,
                        })
                        history.write_bytes(encrypt(json.dumps(messages)).encode())

                        if Has_tool_result:
                            response = ollama.chat(
                                model=LLM,
                                messages=messages,
                                think=False,
                                options=OPTIONS,
                                tools=[Important_Stuff.run_action],
                            )
                            response_text = response.message.content.strip()
                            gen_tps = response.eval_count / (response.eval_duration / 1e9)
                            prompt_tps = response.prompt_eval_count / (response.prompt_eval_duration / 1e9)
                            prompt_seconds = response.prompt_eval_duration / 1e9
                            print("gen_tps:", round(gen_tps, 2))
                            print("prompt_tps:", round(prompt_tps, 2))
                            print("prompt eval sec:", round(prompt_seconds, 4))
                            print("conversation tokens:", response.prompt_eval_count)
                        else:
                            Important_Stuff.speak(response_text)
                            messages.append({"role": "assistant", "content": response_text})
                            history.write_bytes(encrypt(json.dumps(messages)).encode())
                except Exception as e:
                    print(e)

    except Exception as some_larger_error:
        print("An error occurred in the main loop:", str(some_larger_error))

    # clear chat history to preserve space and memory

    # Get turns
    turns = 0
    i = 0
    # set the starting index automatically in case system messages change
    while True:
        if messages[i].get("role").lower() == "system":
            i += 1
        else:
            i += 1
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
        if messages[3].get("role").lower() == "tool":
            for i in range(3):
                messages.pop(2)
        else:
            for i in range(2):
                messages.pop(2)
    history.write_bytes(encrypt(json.dumps(messages)).encode())
