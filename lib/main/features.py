import json
import os
import random
import re
import sqlite3
import struct
import time
import traceback
import urllib.parse
import webbrowser
import eel
import pvporcupine
import pyaudio
import pywhatkit as kit
import pyautogui as autogui
import requests
from rapidfuzz import fuzz, process
import config
import lib.main.response as response
from lib.main.command import speak
from lib.main.helper import *
from lib.utils.location import detect_city_via_ip

con = sqlite3.connect("./database/ivy.db")
cursor = con.cursor()

DEFAULT_CITY = getattr(config, "DEFAULT_CITY", None)


def _find_command(table, column, name):
    """Exact match first, then fuzzy match so "spotfy" still finds "spotify"."""
    cursor.execute(f"SELECT name, {column} FROM {table}")
    rows = cursor.fetchall()
    if not rows:
        return None
    names = [row[0].lower() for row in rows]
    if name in names:
        return rows[names.index(name)][1]
    best = process.extractOne(name, names, scorer=fuzz.WRatio, score_cutoff=85)
    return rows[best[2]][1] if best else None


# for opening apps
def open_command(query):
    from lib.main.helper import clean_app_name

    query = query.replace(config.ASSISTANT_NAME, "")
    query = query.lower().strip()

    query = re.sub(r"\bopen\b", "", query)
    query = re.sub(r"[?!.,]", "", query)
    query = query.strip()

    if query:
        # try the full name first ("visual studio code"), then the last word ("code")
        candidates = [clean_app_name(query), clean_app_name(query.split()[-1])]
        app_name = candidates[0]
        try:
            for name in candidates:
                # Check system commands first
                path = _find_command("sys_command", "path", name)
                if path:
                    speak("Opening " + name)
                    os.startfile(path)
                    return

                # Check web commands
                url = _find_command("web_command", "url", name)
                if url:
                    speak("Opening " + name)
                    webbrowser.open(url)
                    return
            else:
                speak(
                    random.choice(
                        [r.format(app=app_name) for r in response.cannot_find_app]
                    )
                )
                print(f"App '{app_name}' not found in database")
                return

        except Exception as e:
            print("Error in open_command:", e)
            traceback.print_exc()
            speak(random.choice(response.cannot_understand_user))
    else:
        speak(random.choice(response.cannot_understand_app_name))
        print("No application name provided")


def play_youtube(query):
    search_term = extract_yt_term(query)

    if not search_term:
        response_youtube = random.choice(response.cannot_understand_youtube)
        eel.DisplayMessage(response_youtube)
        speak(response_youtube)
        return

    speak(f"playing {search_term} on youtube")
    kit.playonyt(search_term)


#  running in background
def hotword(q):
    porcupine = None
    paud = None
    audio_stream = None

    try:
        print("Initializing Porcupine...")
        porcupine = pvporcupine.create(
            access_key=config.PORCUPINE_API_KEY,
            keyword_paths=[config.PORCUPINE_IVY_HOTKEY_MODEL],
        )

        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        print("Listening for hotword...")

        last_detected = 0
        cooldown = 3  # seconds to wait before re-triggering

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                now = time.time()
                if now - last_detected > cooldown:
                    print("Hotword detected!")

                    # the UI process picks this up and starts listening,
                    # even when the Ivy window isn't focused
                    q.put("hotword")
                    last_detected = now
    except Exception as e:
        print("Error:", repr(e))
        traceback.print_exc()
    finally:
        if porcupine:
            porcupine.delete()
        if audio_stream:
            audio_stream.close()
        if paud:
            paud.terminate()
        print("Program exited cleanly.")


# find contacts in whatsapp
def findContact(query):
    words_to_remove = [
        config.ASSISTANT_NAME,
        "make",
        "a",
        "to",
        "phone",
        "call",
        "send",
        "message",
        "whatsapp",
        "video",
        "please",
        "can",
        "you",
        "me",
        "for",
        "the",
        "contact",
        ".",
        ",",
        "on",
        "with",
        "",
    ]
    query = remove_words(query, words_to_remove)
    query = query.strip().lower()

    cursor.execute("SELECT name, mobile_no FROM contacts")
    contacts = cursor.fetchall()
    contact_names = [name.lower() for name, _ in contacts]

    best = process.extractOne(query, contact_names) if query and contacts else None
    if best and best[1] > 70:
        match, score, idx = best
        mobile_number_str = str(contacts[idx][1])
        print(f"Selected contact: {match}, Number: {mobile_number_str}")
        if not mobile_number_str.startswith(
            config.COUNTRY_CODES["PH"]
        ):  # change this number according to your country
            mobile_number_str = config.COUNTRY_CODES["PH"] + mobile_number_str
        return mobile_number_str, match
    else:
        speak(random.choice(response.cannot_find_whatsapp_contact))
        return 0, 0


def whatsApp(mobile_no, message, flag, name):

    if flag == "message":
        target_tab = 12
        ivy_message = f"Message sent successfully to {name}"
    elif flag == "call":
        target_tab = 7
        message = ""
        ivy_message = f"Calling {name}"
    else:
        target_tab = 6
        message = ""
        ivy_message = f"Starting video call with {name}"

    message = re.sub(r"'{2,}", "'", message)
    message = message.replace(".", "")
    message = message.strip()

    whatsapp_url = (
        f"whatsapp://send?phone={urllib.parse.quote(mobile_no)}"
        f"&text={urllib.parse.quote(message)}"
    )

    try:
        os.startfile(whatsapp_url)
        eel.sleep(5)

        autogui.hotkey("ctrl", "f")
        for _ in range(1, target_tab):
            autogui.hotkey("tab")
        autogui.hotkey("enter")
        speak(ivy_message)
    except Exception as e:
        print("Error sending WhatsApp message:", e)
        speak(random.choice(response.cannot_send_whatsapp_message))


def _resolve_city_for_weather(query: str) -> str:
    from lib.main.helper import extract_city_from_query

    city = extract_city_from_query(query)
    if city:
        return city
    info = detect_city_via_ip()
    if info and info.get("label"):
        return info["label"]

    if DEFAULT_CITY:
        return DEFAULT_CITY
    return ""


def _condition_matches(cond: str, is_sunny: bool, desc: str) -> bool:
    d = (desc or "").lower()
    if cond == "sunny":
        return bool(is_sunny)
    if cond == "rain":
        return any(k in d for k in ("rain", "drizzle", "shower", "storm"))
    if cond == "cloudy":
        return any(k in d for k in ("cloud", "overcast"))
    if cond == "windy":
        return "wind" in d
    if cond == "snow":
        return "snow" in d
    if cond == "storm":
        return any(k in d for k in ("storm", "thunder"))
    return False


def answer_weather_query(query: str) -> None:

    from lib.utils.weather import get_city_weather

    city = _resolve_city_for_weather(query)
    if not city:
        speak("Which city should I check the weather for?")
        return

    data = get_city_weather(city)
    if not data:
        safe_city = (city or "your city").strip()
        map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(safe_city)}"
        line = (
            (
                response.city_not_found_user
                and (
                    random.choice(response.city_not_found_user).format(
                        city=safe_city, map_url=map_url
                    )
                )
            )
            if hasattr(response, "city_not_found_user")
            else f"Sorry, I could not find details for {safe_city}."
        )
        speak(line)
        return

    name = data.get("city_name") or city
    temp = data.get("temperature")
    desc = data.get("weather_description") or ""
    is_sunny = bool(data.get("is_sunny"))

    cond = extract_condition_from_query(query)

    if cond:
        yes = _condition_matches(cond, is_sunny, desc)
        if yes:
            if temp is not None:
                speak(f"Yes, it's {cond} in {name}. Around {temp} degrees.")
            else:
                speak(f"Yes, it's {cond} in {name}.")
        else:
            if temp is not None:
                speak(f"No, it's {desc.lower()} in {name}. Around {temp} degrees.")
            else:
                speak(f"No, it's {desc.lower()} in {name}.")
    else:
        if temp is not None:
            speak(f"In {name}, it is {temp} degrees and {desc}.")
        else:
            speak(f"In {name}, the weather is {desc}.")


@eel.expose
def assistantName():
    name = config.ASSISTANT_NAME
    if name == "":
        name = "Ivy"
    return name


@eel.expose
def personalInfo():
    try:
        cursor.execute("SELECT * FROM info")
        results = cursor.fetchall()
        jsonArr = json.dumps(results[0])
        eel.getData(jsonArr)
        return 1
    except:
        print("no data")


@eel.expose
def updatePersonalInfo(name, designation, mobileno, email, city):
    cursor.execute("SELECT COUNT(*) FROM info")
    count = cursor.fetchone()[0]

    if count > 0:
        # Update existing record
        cursor.execute(
            """UPDATE info 
               SET name=?, designation=?, mobileno=?, email=?, city=?""",
            (name, designation, mobileno, email, city),
        )
    else:
        # Insert new record if no data exists
        cursor.execute(
            """INSERT INTO info (name, designation, mobileno, email, city) 
               VALUES (?, ?, ?, ?, ?)""",
            (name, designation, mobileno, email, city),
        )

    con.commit()
    personalInfo()
    return 1


@eel.expose
def displaySysCommand():
    cursor.execute("SELECT * FROM sys_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displaySysCommand(jsonArr)
    return 1


@eel.expose
def deleteSysCommand(id):
    cursor.execute("DELETE FROM sys_command WHERE id = ?", (id,))
    con.commit()


@eel.expose
def addSysCommand(key, value):
    cursor.execute("""INSERT INTO sys_command VALUES (?, ?, ?)""", (None, key, value))
    con.commit()


@eel.expose
def displayWebCommand():
    cursor.execute("SELECT * FROM web_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayWebCommand(jsonArr)
    return 1


@eel.expose
def addWebCommand(key, value):
    cursor.execute("""INSERT INTO web_command VALUES (?, ?, ?)""", (None, key, value))
    con.commit()


@eel.expose
def deleteWebCommand(id):
    cursor.execute("DELETE FROM web_command WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def displayPhoneBookCommand():
    cursor.execute("SELECT * FROM contacts")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayPhoneBookCommand(jsonArr)
    return 1


@eel.expose
def deletePhoneBookCommand(id):
    cursor.execute("DELETE FROM contacts WHERE Id = ?", (id,))
    con.commit()


@eel.expose
def InsertContacts(Name, MobileNo, Email, City):
    cursor.execute(
        """INSERT INTO contacts VALUES (?, ?, ?, ?, ?)""",
        (None, Name, MobileNo, Email, City),
    )
    con.commit()


# getting time and date
def get_time_date(query):
    from lib.utils.weather import get_city_weather
    import datetime

    city = extract_city_from_query(query)
    if city:
        result = get_city_weather(city)
        if result:
            date = result["date"]
            time_ = result["time"]
            city_name = result["city_name"]
            response_text = random.choice(response.city_time_success).format(
                city=city_name, date=date, time=time_
            )
            print(response_text)
            return response_text
        else:
            response_text = random.choice(response.city_time_fail).format(city=city)
            print(response_text)
            return response_text
    try:
        info = detect_city_via_ip()
        if info and info.get("timezone"):
            from zoneinfo import ZoneInfo

            now = datetime.datetime.now(ZoneInfo(info["timezone"]))
            city_label = info.get("label", "your location")
            tz = info["timezone"]
            date = now.strftime("%A, %B %d, %Y")
            time_ = now.strftime("%I:%M %p")
            response_text = random.choice(response.local_time_success).format(
                city=city_label, date=date, time=time_, tz=tz
            )
            print(response_text)
            return response_text
    except Exception:
        pass
    now = datetime.datetime.now()
    date = now.strftime("%A, %B %d, %Y")
    time_ = now.strftime("%I:%M %p")
    response_text = random.choice(response.system_time_success).format(
        date=date, time=time_
    )
    print(response_text)
    return response_text


def extract_search_query(command: str):
    """
    Extracts a Google search query from a natural language command.
    Returns the extracted query string, or None if no match.
    """
    command = command.lower().strip()

    patterns = [
        r"search\s+(?:for\s+)?(.+?)\s+on\s+google",
        r"search\s+(.+?)\s+on\s+google",
        r"search\s+google\s+for\s+(.+)",
        r"look\s+up\s+(.+?)\s+(?:on|using)\s+google",
        r"find\s+(?:out\s+)?(.+?)\s+on\s+google",
        r"show\s+me\s+(.+?)\s+on\s+google",
        r"check\s+on\s+google\s+for\s+(.+)",
        r"get\s+info\s+on\s+google\s+about\s+(.+)",
        r"see\s+what\s+google\s+says\s+about\s+(.+)",
        r"(?:can\s+you\s+|could\s+you\s+|please\s+|just\s+|let'?s\s+|hey,?\s+)?google\s+(.+?)(?:\s+for\s+me)?$",
        r"open\s+google\s+and\s+search\s+(?:for\s+)?(.+)",
        r"type\s+(.+?)\s+on\s+google",
        r"i\s+want\s+to\s+google\s+(.+)",
        r"do\s+a\s+(?:quick\s+)?google\s+search\s+for\s+(.+)",
        r"google\s+search\s+(.+)",
        r"(?:what|who|where|when|why|how)\s+(?:is|are|to|does|did|can|do)?\s*(.+?)\s+on\s+google",
    ]

    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            query = match.group(1).strip()
            query = re.sub(r"\s+(for\s+me|please)$", "", query)
            return query

    if "google" in command:
        after_google = command.split("google", 1)[1].strip()
        query = re.sub(r"^(for|that|this|it|about|the)\s+", "", after_google)
        query = re.sub(r"\s+(for\s+me|please)$", "", query)
        if query:
            return query

    return None


def google_search(command: str):

    query = extract_search_query(command)

    if query:
        speak(f"Searching {query} on Google")
        webbrowser.open(
            f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        )
    else:
        speak(random.choice(response.google_search_failures))


def get_news(limit=5):
    """
    Fetch top headlines from NewsAPI (source set by config.NEWS_SOURCE).
    Returns list of articles (may be empty list on failure).
    """
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"sources": config.NEWS_SOURCE, "pageSize": limit},
            headers={"X-Api-Key": config.NEWS_API_KEY},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])[:limit]
    except Exception as e:
        print("get_news error:", e)
        return []


def get_random_news_for_speech():
    """
    Pick one random article (from up to 5) and return a short, conversational string
    suitable for TTS. Never raises — returns friendly fallback on error.
    """
    from datetime import datetime

    try:
        articles = get_news(limit=5)
        if not articles:
            return "I couldn't fetch the latest news right now. Try again in a bit."

        article = random.choice(articles)
        title = article.get("title") or "Untitled headline"
        description = article.get("description") or ""
        # trim description to first sentence if long
        if len(description) > 140:
            description = description.split(".")[0].strip()
            if description and not description.endswith("."):
                description += "."

        published = article.get("publishedAt", "")
        try:
            pub_time = datetime.fromisoformat(published.replace("Z", "+00:00"))
            time_str = pub_time.strftime("%B %d")
        except Exception:
            time_str = "recently"

        openers = [
            "Here’s something from today’s news.",
            "Quick news update.",
            "Here’s a headline you might like.",
            "This just in.",
        ]
        opener = random.choice(openers)

        desc_fragment = f" {description}" if description else ""
        speak_text = f"{opener} {title}.{desc_fragment} It was published {time_str}."

        if len(speak_text.split()) > 40:
            speak_text = f"{opener} {title}. It was published {time_str}."

        return speak_text
    except Exception as e:
        print("get_random_news_for_speech error:", e)
        return "I had trouble preparing the news just now."


@eel.expose
def repeat_after_me():
    from lib.main.command import take_command_without_display

    speak(random.choice(response.copy_me_response))
    phrase = take_command_without_display()

    if phrase and phrase.strip():
        print(f"You said: {phrase}")
        speak(phrase)
    else:
        print("Nothing heard.")
        speak(random.choice(response.copy_me_failed))


def get_system_status(query):
    from lib.main.command import take_command, speak_with_display
    from lib.utils.system_info import (
        get_cpu_usage,
        get_memory_usage,
        get_battery_level,
        get_disk_usage,
        get_system_summary,
    )

    query = query.lower()

    affirmatives = [
        "yes",
        "sure",
        "go",
        "fine",
        "good",
        "let's go",
        "lets go",
        "give me",
        "okay",
        "ok",
        "why not",
        "try",
        "can you",
        "do it",
        "proceed",
        "yep",
        "yeah",
    ]

    def report(text):
        # read the stat once (CPU sampling takes a second) and reuse it
        speak_with_display(text, normalize_units(text))

    def mentions(*words):
        return any(re.search(rf"\b{w}\b", query) for w in words)

    try:
        if mentions("battery"):
            report(get_battery_level())
        elif mentions("cpu", "processor"):
            report(get_cpu_usage())
        elif mentions("ram", "memory"):
            report(get_memory_usage())
        elif mentions("disk", "storage"):
            report(get_disk_usage())
        elif mentions("system", "performance"):
            report(get_system_summary())
        else:
            speak(
                "Would you like to get the battery, cpu, ram, disk, and system information?"
            )
            r = take_command()
            print(r)
            if r and any(word in r.lower() for word in affirmatives):
                report(get_system_summary())
            else:
                ...
                # speak(random.choice(response.cancel_responses))
    except Exception as e:
        print("something went wrong", e)


def wikipedia_search(topic):
    import wikipedia as wp

    try:
        res = wp.summary(topic.strip(), sentences=1)
        speak(res)
    except Exception as e:

        print("error:", e)
        speak(random.choice(response.cannot_find_wikipedia))
