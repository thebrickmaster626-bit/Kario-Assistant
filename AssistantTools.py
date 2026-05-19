import datetime
import inspect
import re
import subprocess
import threading
import time
import markdown, ollama
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import requests
from ddgs import DDGS
from SpeechToText import record_and_transcribe

"""
CODE GUIDE

Line 29: class "Important_Stuff"
Line 61: class "Apple_Integration"
Line 179: class "General_LLM_Tools"
"""

# Debug toggle:
# True  -> do not swallow tool errors; raise and crash for debugging.
# False -> return "Tool error: ..." and continue running.
# If you wish to remove the ability to send and call people, set Testing_automation to True
# If you wish for the assistant to not talk and for you to not wait for it to finish talking, set quiet_mode to True

CRASH_ON_TOOL_ERROR = False
Testing_automation = True
quiet_mode = True

# Important and miscellaneous stuff
class Important_Stuff:
    def __init__(self):
        pass

    @staticmethod
    def speak(text, block=True):
        if not quiet_mode:
            filtered = (text.replace("\n", " ")
                        .replace("\r", " ")
                        .replace("\t", " ")
                        .replace("*", "")
                        .replace("•", " ")
                        )
            if block:
                subprocess.run(["say", filtered])
            else:
                subprocess.Popen(["say", filtered])

    @staticmethod
    def run_action(func: str, args: dict):
        ACTIONS = {
            "weather": ModelTools.get_weather,
            "search": ModelTools.search_the_web,
            "start_timer" : ModelTools.start_timer,
            "stop_timer" : ModelTools.stop_timer,
            "send_imessage": Apple.send_imessage,
            "call_person": Apple.call_number,
            "set_reminder": Apple.set_reminder,
            "compose": Apple.compose,
            "calculate": ModelTools.calculate,
        }
        try:
            action = ACTIONS[func]
            sig = inspect.signature(action)

            bound = sig.bind_partial(**args)
            bound.apply_defaults()

            action_result = action(**bound.arguments)
            if action_result == None or action_result == "":
                print("Action ran successfully but has no result")
                return "Action ran successfully but has no result"
            else:
                print(action_result)
                return action_result
        except Exception as e:
            if CRASH_ON_TOOL_ERROR:
                raise
            print(e)
            return f"Action error: {e}"

    @staticmethod
    def alert():
        print("Alert")

    @staticmethod
    def better_bool(so_called_boolean):
        if str(so_called_boolean).lower() == "true" or str(so_called_boolean).lower() == "yes" or str(so_called_boolean).lower() == "1":
            return True
        else:
            return False

# Functions that integrate the assistant with macOS
class Apple_Integration:
    # Apple integration functions
    def __init__(self):
        pass

    @staticmethod
    def escape_applescript_string(value):
        text = "" if value is None else str(value)
        text = text.replace("\\", "\\\\")
        text = text.replace("\"", "\\\"")
        text = text.replace("\r", " ").replace("\n", " ")
        return text

    # Used to turn a phone number like +1 (123) 456 7890 to 11234567890 so that way it's cleaner
    @staticmethod
    def normalize_phone(number):
        digits = re.sub(r"\D", "", number)

        # US numbers
        if len(digits) == 10:
            return "1" + digits

        # already includes country code (like 11 digits starting with 1)
        if len(digits) == 11:
            return digits

        # fallback (unknown format)
        return digits

    # Uses the contacts app to get a person's phone number from: their first and/or last, or their nickname
    @staticmethod
    def get_phone_number(name):
        name = Apple.escape_applescript_string(name)
        script = f'''
        on run argv
            tell application "Contacts"
                set thePerson to first person whose first name is "{name}" or last name is "{name}" or nickname is "{name}" or name contains "{name}"
                set phoneList to value of every phone of thePerson
                return phoneList
            end tell
        end tell
        '''

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True
        )

        result.stdout.strip()

        return Apple.normalize_phone(result.stdout.strip())

    # Sends an imessage to a person
    @staticmethod
    def send_imessage(recipient):
        buddy = Apple.get_phone_number(recipient)

        while True:
            Important_Stuff.speak("What would you like to say?")
            message = record_and_transcribe()
            if message != "cancel":
                Important_Stuff.speak(f"Is this correct? {message}")
                confirmation = record_and_transcribe()
                confirmation = confirmation.lower()
                if "yes" in confirmation or "yeah" in confirmation:
                    break
                elif "cancel" in confirmation:
                    return
                else:
                    pass
            else:
                return
        if not Testing_automation:
            buddy = Apple.escape_applescript_string(buddy)
            message = Apple.escape_applescript_string(message)
            script = f'''
            on run argv
                tell application "Messages"
                    set targetService to 1st service whose service type = iMessage
                    set targetBuddy to buddy "{buddy}" of targetService
                    send "{message}" to targetBuddy
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            Important_Stuff.speak(f"Message sent to {buddy} saying {message}")
        else:
            print("Automation blocked for testing")

    # Calls the specified person with Facetime or Facetime audio
    @staticmethod
    def call_number(name, video=False):
        call_type = Important_Stuff.better_bool(video)
        buddy = Apple.get_phone_number(name)
        call_type = "video" if call_type else "audio"

        if not Testing_automation:
            if not re.fullmatch(r"\d{10,11}", buddy):
                raise ValueError("Invalid phone number for FaceTime automation")
            script = f'''
            on run argv
                tell application "FaceTime"
                    activate
                    call "{buddy}" using {call_type}
                end tell
            end tell
            '''

            subprocess.run(["osascript", "-e", script])
        else:
            print("Automation blocked for testing")

    # Resumes or pauses spotify
    @staticmethod
    def resume_or_pause_spotify():
        script = '''
        tell application "Spotify"
            playpause
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("Spotify Resumed")

    # Plays a song, sadly this search feature cannot play a playlist. Also, it is currently unknown if it will continue playing songs that kinda match
    @staticmethod
    def play_song(playlist):
        playlist = quote_plus("" if playlist is None else str(playlist))
        script = f'''
        on run argv
            tell application "Spotify"
                play track "spotify:search:{playlist}"
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("Playing Spotify")

    @staticmethod
    def set_reminder(name, offset_day, hour, minute, AMPM="military"):

        hour = int(hour)
        minute = int(minute)
        offset_day = int(offset_day)

        # ---- compute target date from today + offset ----
        target = datetime.now() + timedelta(days=offset_day)

        year = target.year
        month = target.month
        day = target.day

        # ---- AM/PM conversion ----
        if hour < 12 or AMPM != "military":
            if AMPM.lower() == "am":
                if hour == 12:
                    hr = 0
                else:
                    hr = hour
            elif AMPM.lower() == "pm":  # pm
                if hour == 12:
                    hr = 12
                else:
                    hr = hour + 12
            else:
                print("ERROR: AMPM MUST BE AM or PM")
                return
        # We shall assume that it is in military time if hour is greater than 12 or AMPM is not provided
        else:
            hr = hour


        script = f'''
        on run argv
            tell application "Reminders"
                set d to current date
                set year of d to {year}
                set month of d to {month}
                set day of d to {day}
                set hours of d to {hr}
                set minutes of d to {minute:02d}
    
                make new reminder with properties {{name:"{name}", due date:d}}
            end tell
        end
        '''

        minute = f"{minute:02d}"
        subprocess.run(["osascript", "-e", script])
        Important_Stuff.speak(f"I have set a reminder for you to go off at {hour}:{'' if minute == '00' else minute} {AMPM}")

    # Uses MORE AI to draft lists and write emails
    @staticmethod
    def compose(ai_prompt, is_email_draft=False):
        is_email_draft = bool(is_email_draft)
        if not is_email_draft:
            prompt = """
            You are Kario's writer.
            Write clean Markdown text from Kario's request.

            Rules:
            - Be concise and follow the request.
            - Keep Kario's intent exactly; do not add unrelated content.
            - Use headings and bullet points when helpful / asked.
            - If Kario gives Markdown, preserve its structure and improve clarity.
            - Output only the final Markdown note body, no extra commentary.
            - In your writing, never include something like "Ok, Kario!" or "Here are your notes!"
            - You are not limited to just notes, you can write reports, lists, books, or just stick to notes.

            Note: Kario is an assistant for a user. You are a writing backend for Kario, so if you were to put a placeholder that says [Kario's name] or [Kario's address] for example, please use User instead of Kario.
            """.strip()
        else:
            prompt = """
            You are Kario's email drafter.
            Write clean text from Kario's request.

            Rules:
            - Be concise and follow the request.
            - Keep Kario's intent exactly; do not add unrelated content.
            - Output only the final email body, no extra commentary.
            - In your writing, never include something like "Ok, Kario!" or "Here are your notes!"
            - Please do not use headings or titles at all.
            - Please do not generate an email subject at all, you are only drafting the email body.

            Note: Kario is an assistant for a user. You are a writing backend for Kario, so if you were to put a placeholder that says [Kario's name] or [Kario's address] for example, please use User instead of Kario.
            """.strip()
        response = ollama.chat(
            model="phi4-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": ai_prompt},
            ],
        )
        ai_text = response.message.content
        html = markdown.markdown(ai_text, extensions=["extra", "sane_lists"])
        print(html)

        if not is_email_draft:
            script = f'''
            on run argv
                tell application "Notes"
                    tell default account
                        tell default folder
                            make new note with properties {{body:"{html}"}}
                        end tell
                    end tell
                    activate
                end tell
            end
            '''
        else:
            script = f'''
            on run argv
                tell application "Mail"
                    set newMessage to make new outgoing message with properties {{visible:true, content:"{html}"}}
                    activate
                end tell
            end
            '''
        subprocess.run(
            ["osascript", "-e", script],
        )

Apple = Apple_Integration()

timers = {}
timer_stop_flags = {}

# General tools for the LLM to use
class General_LLM_Tools:
    def __init__(self):
        pass

    # Gets the current date
    @staticmethod
    def get_date(include_time=False):
        now = datetime.now()

        if include_time:
            hour = now.strftime("%I").lstrip("0")
            minute = now.strftime("%M")
            ampm = now.strftime("%p")

            value = f"{now.strftime('%Y-%m-%d')} {hour}:{minute} {ampm}"
        else:
            value = f"{now.strftime('%Y-%m-%d')}"

        print(value)
        return value


    # Starts a timer
    @staticmethod
    def start_timer(hour=0, min=0, sec=0):
        hour = int(hour)
        min = int(min)
        sec = int(sec)
        total_seconds = (hour * 3600) + (min * 60) + sec
        display = f"{hour:02d}:{min:02d}:{sec:02d}"
        print(f"Timer started, hours: {hour}, minutes: {min}, seconds: {sec}")
        Important_Stuff.speak(f"Timer started for {hour} hours, {min} minutes, and {sec} seconds")

        def wait():
            for i in range(total_seconds):
                if timer_stop_flags.get(display):
                    print("timer stopped")
                    return
                time.sleep(1)
                print(f"{total_seconds - i} seconds left")
            Important_Stuff.alert()
            del timers[display]
            del timer_stop_flags[display]

        thread = threading.Thread(target=wait, daemon=False)
        timers[display] = thread
        timer_stop_flags[display] = False
        thread.start()

    # Stops a timer
    @staticmethod
    def stop_timer(timer_time):
        if timer_time in timers:
            timer_stop_flags[timer_time] = True
            del timers[timer_time]
            del timer_stop_flags[timer_time]
            print(f"Timer for '{timer_time}' stopped.")
            Important_Stuff.speak(f"Timer has sucessfully stopped")
        else:
            print(f"No timer found with time '{timer_time}'.")
            Important_Stuff.speak("Error: no timer found with that time")

    # Stops all timers
    @staticmethod
    def stop_all_timers():
        for key in timer_stop_flags:
            timer_stop_flags[key] = True
        timer_stop_flags.clear()
        timers.clear()
        Important_Stuff.speak("All timers stopped")
        print("All timers stopped.")

    # Searches the web, provides basic results
    @staticmethod
    def search_the_web(prompt):
        search = f"{prompt}"
        Important_Stuff.speak("Hold on, let me look it up", False)
        # 1) SEARCH: use DDGS to get the first search result
        print("debug:", "used web search, prompt used:", prompt)
        try:
            with DDGS() as ddgs:
                results = ddgs.text(search, max_results=6, timelimit="y")
                results_list = list(results)
        except Exception as e:
            return f"Search failed: {str(e)}"

        if not results_list:
            return "No search results found."

        clean_lines = []
        for i, result in enumerate(results_list):
            title = (result.get("title") or "Untitled").strip()
            href = (result.get("href") or "").strip()
            body = (result.get("body") or "").strip()
            body = " ".join(body.split())
            if len(body) > 900:
                body = body[:900].rstrip() + "…"
            clean_lines.append(f"{i}. {title}\n{body}\nSource: {href}")

        clean_text = "\n\n".join(clean_lines)
        print(clean_text)
        return clean_text

    # Gets a 24 hours rain and temp forecast
    @staticmethod
    def get_weather(single_hour_forecast=False):
        no_forecast = Important_Stuff.better_bool(single_hour_forecast)
        print("debug: used weather")
        # --- get location from IP ---
        loc = requests.get("http://ip-api.com/json/").json()
        lat, lon = loc["lat"], loc["lon"]

        # --- get weather from Open-Meteo ---
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation_probability",
                "temperature_unit": "fahrenheit",
                "forecast_hours": 13,
                "timezone": "auto"
            }
        ).json()

        temps = r["hourly"]["temperature_2m"]
        rain_probs = r["hourly"]["precipitation_probability"]
        times = r["hourly"]["time"]

        hourly_forecast = []

        for t, temp, rain in zip(times, temps, rain_probs):
            dt = datetime.fromisoformat(t)

            hourly_forecast.append({
                "time_local": dt.strftime("%I:%M %p"),
                "temp_f": round(temp, 1),
                "rain_chance_percent": rain,
            })

        # ---------------------------
        # FORECAST MODE SWITCH
        # ---------------------------
        first = hourly_forecast[0]
        if no_forecast:
            # ONLY FIRST FORECAST ITEM

            formatted_output = (
                f"CURRENT TEMP AND RAIN\n"
                f"{first['time_local']} — {first['temp_f']}°F — {first['rain_chance_percent']}% rain"
            )

        else:
            # full 13-hour forecast
            hourly_forecast = hourly_forecast[:13]
            temps = temps[:13]
            rain_probs = rain_probs[:13]

            forecast_lines = [
                f"{item['time_local']} — {item['temp_f']}°F — {item['rain_chance_percent']}% rain"
                for item in hourly_forecast
            ]

            formatted_output = (
                    f"NEXT 12 HOURS WEATHER\n"
                    f"Current weather: {first['time_local']} — {first['temp_f']}°F — {first['rain_chance_percent']}% rain\n\n"
                    f"Low: {round(min(temps), 1)}°F\n"
                    f"High: {round(max(temps), 1)}°F\n"
                    f"Peak rain chance: {max(rain_probs)}%\n\n"
                    f"Hourly forecast:\n" +
                    "\n".join(forecast_lines)
            )

        print(formatted_output)
        return formatted_output

    @staticmethod
    def calculate(Math_problem):
        Result = Math_problem.lower().replace("x", "*").replace("×", "*").replace("÷", "/").replace("^", "**")
        return Result

ModelTools = General_LLM_Tools()
