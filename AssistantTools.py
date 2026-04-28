import datetime
import inspect
import json
import re
import subprocess
import threading
import time
from datetime import datetime
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
# If you wish to remove the ability to send and call people, set Testing_automation to true

CRASH_ON_TOOL_ERROR = True
Testing_automation = True

# Important and miscellaneous stuff
class Important_Stuff:
    def __init__(self):
        pass

    @staticmethod
    def speak(text):
        subprocess.run(["say", text])

    @staticmethod
    def safe_call(func, args):
        try:
            sig = inspect.signature(func)

            # keep only valid parameters
            filtered = {
                k: args.get(k)
                for k in sig.parameters.keys()
            }

            return func(**filtered)

        except Exception as e:
            if CRASH_ON_TOOL_ERROR:
                raise
            return f"Tool error: {e}"

    @staticmethod
    def alert():
        print("Alert")

# Functions that integrate the assistant with MacOS
class Apple_Integration:
    # Apple integration functions
    def __init__(self):
        pass

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
        script = f'''
        tell application "Contacts"
            set thePerson to first person whose first name is "{name}" or last name is "{name}" or nickname is "{name}" or name contains "{name}"
            set phoneList to value of every phone of thePerson
            return phoneList
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
            Important_Stuff.speak(f"Is this correct? {message}")
            confirmation = record_and_transcribe()
            confirmation = confirmation.lower()
            if "yes" in confirmation or "yeah" in confirmation:
                break
            elif "cancel" in confirmation:
                return
            else:
                pass
        if not Testing_automation:
            script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{buddy}" of targetService
                send "{message}" to targetBuddy
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
        else:
            print("Automation blocked for testing.")

    # Calls the specified person with Facetime or Facetime audio
    @staticmethod
    def call_number(name, video=False):
        buddy = Apple.get_phone_number(name)
        call_type = "video" if video else "audio"

        if not Testing_automation:
            script = f'''
            tell application "FaceTime"
                activate
                call "{Apple.normalize_phone(buddy)}" using {call_type}
            end tell
            '''

            subprocess.run(["osascript", "-e", script])
        else:
            print("Automation blocked for testing.")

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
        script = f'''
        tell application "Spotify"
            play track "spotify:search:{playlist}"
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("Playing Spotify")

Apple = Apple_Integration()

timers = {}
timer_stop_flags = {}

# General tools for the LLM to use
class General_LLM_Tools:
    def __init__(self):
        pass

    # Gets the current date
    @staticmethod
    def get_date_and_time():
        now = datetime.now()

        hour = now.strftime("%I").lstrip("0")
        minute = now.strftime("%M")
        ampm = now.strftime("%p")

        value = f"{now.strftime('%Y-%m-%d')} {hour}:{minute} {ampm}"

        print(value)
        return value


    # Starts a timer
    @staticmethod
    def start_timer(hour, min, sec):
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

        # 1) SEARCH: use DDGS to get the first search result
        print("debug:", "used web search, prompt used:", prompt)
        try:
            with DDGS() as ddgs:
                results = ddgs.text(prompt, max_results=4)
                results_list = list(results)
        except Exception as e:
            return f"Search failed: {str(e)}"

        if not results_list:
            return "No search results found."

        clean_lines = []
        for i, result in enumerate(results_list[:3], start=1):
            title = (result.get("title") or "Untitled").strip()
            href = (result.get("href") or "").strip()
            body = (result.get("body") or "").strip()
            body = " ".join(body.split())
            if len(body) > 740:
                body = body[:740].rstrip() + "..."
            clean_lines.append(f"{i}. {title}\n{body}\nSource: {href}")

        clean_text = "\n\n".join(clean_lines)
        print(clean_text)
        return clean_text

    # Gets a 24 hours rain and temp forecast
    @staticmethod
    def get_weather():
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
                "forecast_hours": 12,
                "timezone": "auto"
            }
        ).json()

        temps = r["hourly"]["temperature_2m"]
        rain_probs = r["hourly"]["precipitation_probability"]
        times = r["hourly"]["time"]

        max_rain = max(rain_probs)
        max_rain_idx = rain_probs.index(max_rain)
        peak_rain_time = datetime.fromisoformat(times[max_rain_idx]).strftime("%I:%M %p")

        hourly_forecast = []
        for t, temp, rain in zip(times, temps, rain_probs):
            hourly_forecast.append({
                "time_local": datetime.fromisoformat(t).strftime("%I:%M %p"),
                "temp_f": round(temp, 1),
                "rain_chance_percent": rain,
            })

        summary = {
            "next_12h_temp_low_f": round(min(temps), 1),
            "next_12h_temp_high_f": round(max(temps), 1),
            "max_rain_chance_percent": max_rain,
            "peak_rain_time_local": peak_rain_time,
            "hourly_forecast": hourly_forecast,
        }
        return json.dumps(summary, separators=(", ", ": "))

ModelTools = General_LLM_Tools()
