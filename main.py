import ollama
import json
from ollama import chat
from SpeechToText import record_and_transcribe
from AssistantTools import Apple, Important_Stuff, ModelTools, Testing_automation
from pathlib import Path

LLM = ("qwen2.5:3b")
Has_tool_result = True
Can_speak = False

FAST_OPTIONS = {
    "num_ctx": 912,
    "num_predict": 120,
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 16,
    "repeat_penalty": 1.06,
    "num_thread": 11,
}
FAST_OPTIONS_SECOND_PASS = {
    "num_ctx": 912,
    "num_predict": 120,
    "temperature": 0.1,
    "top_p": 0.9,
    "top_k": 16,
    "repeat_penalty": 1.06,
    "num_thread": 11,
}

system_prompt = Path("Prompt.txt").read_text(encoding="utf-8")
print("LLM running! Model:")
print(LLM)

while True:
    if Can_speak:
        prompt = record_and_transcribe()
    else:
        prompt = input(">…")
    if "computer" in prompt.lower() or "assistant" in prompt.lower():
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    if "timer" in prompt.lower() or "countdown" in prompt.lower():
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
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
            messages=messages,
            tools=tools,
            think=False,
            options=FAST_OPTIONS,
        )
        response_text = (response.message.content or "").strip()
        if response_text:
            print(response_text)

        # If it did call any tools, handle them
        if response.message.tool_calls:
            Has_tool_result = False
            for call in response.message.tool_calls:
                name = call.function.name
                args = call.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                print(f"ran tool {name}")
                print(f"args: {args}")
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
                    messages.append({
                        "role": "tool",
                        "tool_name": name,
                        "content": tool_result,
                    })

                # Ask the model for a *second* response after the tool results ONLY if the tool was to get data, if it is to execute actions then this will be skipped
                if Has_tool_result:
                    final_response = chat(
                        model=LLM,
                        messages=messages,
                        think=False,
                        options=FAST_OPTIONS_SECOND_PASS,
                    )

                    print("Assistant after tools:", final_response.message.content)

                    Important_Stuff.speak(final_response.message.content)
        else:
            Important_Stuff.speak(response_text)
