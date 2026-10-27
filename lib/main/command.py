import random
import re
import time
import traceback
import audioop
import pyttsx3
import speech_recognition as sr
import pyaudio
import wave
from faster_whisper import WhisperModel
import os
import eel
import config
import lib.main.response as response

# For Mac, If you face error related to "pyobjc" when running the `init()` method :
# Install 9.0.1 version of pyobjc : "pip install pyobjc>=9.0.1"

call_keywords = [
    "call",
    "phone call",
    "make a call",
    "dial",
    "ring",
    "place a call",
    "video call",
]
message_keywords = [
    "send message",
    "send a message",
    "message",
    "text",
    "send text",
    "send a text",
    "send a text message",
    "text message",
    "send text message",
]

math_keywords = [
    "calculate",
    "whats",
    "what's",
    "plus",
    "minus",
    "times",
    "multiply",
    "divide",
    "divided",
    "add",
    "subtract",
    "power",
    "square root",
    "percent",
]

time_date_keywords = [
    "time",
    "date",
    "day",
    "today",
    "current time",
    "current date",
    "what time",
    "what date",
    "now",
    "clock",
    "time in",
    "date in",
]

casual_keywords = [
    "hello",
    "hi",
    "hey",
    "morning",
    "afternoon",
    "evening",
    "night",
    "how are you",
    "how're you",
    "thank",
    "thanks",
    "bye",
    "goodbye",
    "awesome",
    "amazing",
    "love you",
    "sad",
    "happy",
    "bored",
    "excited",
    "who are you",
    "what are you",
    "what can you",
]

joke_keywords = [
    "joke",
    "riddle",
    "fact",
    "play",
    "game",
    "fun",
    "laugh",
    "make me smile",
    "entertain",
]

news_keywords = [
    "news",
    "headlines",
    "what's in the news",
    "what is in the news",
    "latest news",
    "tell me the news",
    "any news",
    "news flash",
    "news update",
    "headline",
]

copy_me_keywords = [
    "repeat after me",
    "repeat what i say",
    "repeat on waht im saying",
    "repeat what i said",
    "copy me",
    "do what i say",
    "copy my words",
    "copy the words that came from my mouth",
    "talk like me",
    "mimic me",
]

system_keywords = [
    "cpu",
    "processor",
    "ram",
    "memory",
    "storage",
    "disk",
    "battery",
    "performance",
    "system status",
    "system info",
    "system information",
    "system stats",
    "system status",
    "device status",
    "device info",
    "device information",
    "check my device",
    "check my system",
    "check my hardware",
    "check hardware",
    "check device",
    "check system",
]


def has_keyword(text, keywords):
    """Whole-word/phrase match, so "now" won't fire on "know" or "ram" on "program"."""
    return any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords)


NUMBER_PATTERN = re.compile(
    r"\d|\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million)\b"
)


def is_math_query(text):
    # "what's" alone is too broad ("what's your name"), so it needs a number with it
    strong = [kw for kw in math_keywords if kw not in ("whats", "what's")]
    if has_keyword(text, strong):
        return True
    return has_keyword(text, ["whats", "what's", "what is"]) and bool(
        NUMBER_PATTERN.search(text)
    )


# load model (int8 is much faster on CPU with almost no accuracy loss)
if os.path.exists(config.MODEL_DIR):
    model = WhisperModel(config.MODEL_DIR, device="cpu", compute_type="int8")
    print(f"Model folder loaded: {config.MODEL_DIR}")
elif os.path.exists(config.MODEL_BACKUP):
    model = WhisperModel(config.MODEL_BACKUP, device="cpu", compute_type="int8")
    print("Model loaded successfully!")
else:
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    print("Model loaded successfully!")

# words Whisper tends to mishear; biasing the decoder toward them helps
WHISPER_PROMPT = (
    "Ivy, open YouTube, Google, Wikipedia, WhatsApp, weather, news, "
    "battery, CPU, calculate, send a message, video call."
)

# phrases Whisper invents when it hears silence or noise
WHISPER_HALLUCINATIONS = {
    "you",
    "thank you",
    "thanks for watching",
    "thank you for watching",
    "bye",
    "okay",
}


def speak(text):

    engine = pyttsx3.init()

    engine.setProperty("rate", 174)

    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)

    eel.DisplayMessage(text)
    eel.receiverText(text)

    engine.say(text)
    engine.runAndWait()


def speak_with_display(display_text, speak_text):
    """
    Display one message on screen, speak a different message via voice.
    Used when you want to show formatted numbers but speak words.
    """
    engine = pyttsx3.init()

    engine.setProperty("rate", 174)

    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)

    eel.DisplayMessage(display_text)
    eel.receiverText(speak_text)

    engine.say(speak_text)
    engine.runAndWait()


def record_audio(
    filename="input.wav",
    ambient_sample_seconds=0.5,
    silence_factor=3.0,
    min_silence_threshold=300,
    silence_duration=1.0,
    start_timeout=6.0,
    max_duration=15.0,
):

    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    rate = 16000

    p = pyaudio.PyAudio()
    stream = p.open(
        format=sample_format,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk,
    )

    # --- calibrate ambient RMS ---
    frames_cal = []
    calibr_chunks = int(rate / chunk * ambient_sample_seconds)
    for _ in range(max(1, calibr_chunks)):
        data = stream.read(chunk, exception_on_overflow=False)
        frames_cal.append(data)
    ambient_rms = audioop.rms(b"".join(frames_cal), 2)
    # compute threshold from ambient rms but enforce a sensible minimum
    silence_threshold = max(int(ambient_rms * silence_factor), min_silence_threshold)

    eel.DisplayMessage(f"Listening...")
    print(f"threshold={silence_threshold}")

    frames = []
    silence_start = None
    speech_started = False
    started_at = time.time()

    try:
        while True:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

            # compute instantaneous rms
            rms = audioop.rms(data, 2)

            # --- debug line (uncomment during tuning) ---
            # print(f"rms={rms}, threshold={silence_threshold}")

            elapsed = time.time() - started_at
            if elapsed > max_duration:
                break

            if not speech_started:
                # don't count the pause before the user starts talking as "done"
                if rms >= silence_threshold:
                    speech_started = True
                elif elapsed > start_timeout:
                    break
                continue

            if rms < silence_threshold:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > silence_duration:
                    break
            else:
                # voice detected; reset silence timer
                silence_start = None

        eel.DisplayMessage("Recognizing....")
    except Exception as e:
        print("Recording error:", e)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))

    return filename


def transcribe_audio(filename="input.wav"):
    segments, _ = model.transcribe(
        filename,
        language="en",
        beam_size=5,
        vad_filter=True,  # drop silence/noise so Whisper doesn't make up words
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
        initial_prompt=WHISPER_PROMPT,
    )
    text = " ".join(
        segment.text.strip() for segment in segments if segment.no_speech_prob < 0.6
    ).strip()
    if os.path.exists(filename):
        os.remove(filename)

    # strip trailing punctuation Whisper adds ("Open YouTube." -> "Open YouTube")
    text = text.rstrip(".!?,")
    if text.lower() in WHISPER_HALLUCINATIONS:
        return ""
    return text


# THE CORE CONNECTION OF ALL COMMANDS
@eel.expose
def take_command():
    # eel.DisplayMessage("Hello, I am Ivy")
    # eel.sleep(1.0)
    file = record_audio()
    query = transcribe_audio(file)
    eel.DisplayMessage(query)

    # brief pause so the user can see what was heard; eel.sleep keeps the UI responsive
    eel.sleep(0.6)

    return query


def take_command_without_display():

    file = record_audio()
    query = transcribe_audio(file)

    return query


# core logic for all commands
@eel.expose
def all_commands(message=1) -> str:
    from lib.main.helper import is_weather_query, is_youtube_query

    if message == 1:
        query = take_command()
        query = query.rstrip()
        print("query is :", query)
        eel.senderText(query)
    else:
        query = message
        eel.senderText(query)

    try:
        q = (query or "").lower().strip()

        # if no voice
        if len(query) < 2:

            speak(random.choice(response.cannot_understand_user))
            return

        # ===== PRIORITY 1: CORE COMMANDS =====

        # OPEN COMMAND - Must check first
        if has_keyword(q, ["open"]) and not is_youtube_query(query):
            # Make sure it's not "open [something] on youtube"
            from lib.main.features import open_command

            open_command(query)
            return

        # YOUTUBE - Flexible detection with intelligent title extraction
        if is_youtube_query(query):
            from lib.main.features import play_youtube

            play_youtube(query)
            return

        # WEATHER
        if is_weather_query(query):
            from lib.main.features import answer_weather_query

            answer_weather_query(query)
            return

        # GOOGLE
        if (
            "google" in q
            and not is_youtube_query(query)
            and not is_weather_query(query)
        ):

            from lib.main.features import extract_search_query, google_search

            google_q = extract_search_query(query)

            if google_q:

                google_search(query)
            else:
                speak("What would you like me to search on Google?")
                follow_up = take_command()
                follow_up = (follow_up or "").strip()
                if len(follow_up) >= 2:
                    google_search(f"google {follow_up}")
                else:
                    speak("Okay, cancelled Google search.")
            return

        # WIKIPEDIA
        if (
            "wikipedia" in q
            and not is_weather_query(query)
            and not is_youtube_query(query)
        ):
            from lib.main.features import wikipedia_search

            query = query.replace("wikipedia", "")
            wikipedia_search(query)
            return

        # LET IVY REPEAT YOUR WORDS
        if has_keyword(q, copy_me_keywords):
            from lib.main.features import repeat_after_me

            repeat_after_me()
            return

        # GET SYSTEM INFO
        if has_keyword(q, system_keywords):
            from lib.main.features import get_system_status

            get_system_status(query)
            return

        # TIME & DATE
        if has_keyword(q, time_date_keywords):
            from lib.main.features import get_time_date

            speak(get_time_date(query))
            return

        # GET SOME NEWS
        if has_keyword(q, news_keywords) and not (
            "youtube" in q or "google" in q
        ):
            from lib.main.features import get_random_news_for_speech

            try:
                speak(get_random_news_for_speech())
            except Exception as e:

                print("Error while handling news command:", e)
                traceback.print_exc()
                speak(random.choice(response.news_fetch_failures))
            return

        # MATH CALCULATIONS
        if is_math_query(q):
            from lib.math.calculator import calculate

            result = calculate(query)
            if result["success"]:
                speak_with_display(
                    f"The answer is {result['result_display']}",
                    f"The answer is {result['result_words']}",
                )
            else:
                speak(
                    random.choice(response.cannot_calculate).format(
                        error=result["error"]
                    )
                )
            return

        # WHATSAPP
        if has_keyword(q, message_keywords + call_keywords):
            from lib.main.features import findContact, whatsApp
            import re

            cleaned_query = re.sub(r"[^\w\s]", "", query)
            cleaned_query = re.sub(
                r"\b("
                + "|".join(message_keywords + call_keywords)
                + r"|to|and|a|please)\b",
                "",
                cleaned_query,
                flags=re.IGNORECASE,
            )
            cleaned_query = cleaned_query.strip()

            contact_no, name = findContact(cleaned_query.lower())
            if contact_no != 0:
                flag = ""
                message = ""
                if any(kw in query.lower() for kw in message_keywords):
                    flag = "message"
                    speak("What message to send?")
                    message = take_command()
                elif any(kw in query.lower() for kw in call_keywords):
                    if "video call" in query.lower():
                        flag = "video call"
                    else:
                        flag = "call"
                    print(flag)
                else:
                    flag = "message"

                whatsApp(contact_no, message if flag == "message" else "", flag, name)
            else:
                print("something went wrong in whatsapp command.py")
            return

        # ===== PRIORITY 2: CONVERSATION HANDLING =====

        from lib.conversations.router import route_conversation

        conversation_response = route_conversation(query)
        if conversation_response:
            speak(conversation_response)
            return

        # # ===== PRIORITY 3: UNKNOWN QUERY =====

        # friendly_responses = [
        #     "Hmm, I'm not sure how to help with that. Want to try something else?",
        #     "I didn't quite catch that. Could you rephrase it?",
        #     "That's a new one for me! Try asking me to open an app, check the weather, or tell you a joke!",
        # ]
        # speak(random.choice(friendly_responses))
        # print(f"Unknown query: {query!r}")

    except Exception as e:
        from lib.main import response

        print("Error in all_commands:", e)
        traceback.print_exc()
        speak(random.choice(response.error_in_allcommands))

    finally:
        print("showing the orb back...")
        try:
            eel.ShowHood()
        except Exception as e:
            print("ShowHood error:", e)


def check_mic_to_use():
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(
            'Microphone with name "{1}" found for `Microphone(device_index={0})`'.format(
                index, name
            )
        )


""" _disabled_

def take_command_vosk():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("listening...")
        eel.DisplayMessage("listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=10)
        except sr.WaitTimeoutError:
            print("Timeout waiting for speech.")
            return ""

    try:
        print("recognizing")
        eel.DisplayMessage("recognizing....")

        # reuse the same model
        rec = KaldiRecognizer(model, 16000)
        rec.AcceptWaveform(audio.get_raw_data(convert_rate=16000, convert_width=2))
        result = json.loads(rec.Result())

        query = result.get("text", "").strip()
        if not query:
            eel.DisplayMessage("Could not understand, please try again.")
            eel.sleep(3.5)
            eel.ShowHood()
            return ""

        eel.DisplayMessage(query)
        eel.sleep(3.5)
        eel.ShowHood()
        return query.lower()

    except Exception as e:
        print("Recognition error:", e)
        eel.DisplayMessage(f"Error: {e}")
        eel.sleep(3.5)
        eel.ShowHood()
        return ""


# backup a bruteforce way if sr.recognize function is not working
def take_command_force(device_index=None):
       
        Brute-force listen-and-recognize loop using Vosk/Kaldi.

        under the hood version for speech recognition sr.recognize_vosk() -> str
        if it that function is not available we can use this

        Args:
            device_index (int|None): optional microphone device index for sr.Microphone

        Returns:
            str: recognized text in lowercase, or "" if the model folder is missing.
 
    model_dir = "machine-learning/vosk-model-en-us-0.22-lgraph"
    if not os.path.isdir(model_dir):
        print(f"Model folder not found: {model_dir}")
        print("Download a Vosk model and extract it there.")
        return ""
    model = Model(model_dir)

    r = sr.Recognizer()
    r.pause_threshold = 0.7
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone(device_index=device_index) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = r.listen(source, timeout=10, phrase_time_limit=6)
    except sr.WaitTimeoutError:
        print("No speech detected (timeout).")
        return ""
    except OSError as e:
        print(f"Microphone error: {e}")
        return ""

    try:
        print("Recognizing...")
        rec = KaldiRecognizer(model, 16000)
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        if rec.AcceptWaveform(raw):
            data = json.loads(rec.Result())
        else:
            data = json.loads(rec.FinalResult())
        text = data.get("text", "").strip()
        return text.lower()
    except json.JSONDecodeError:
        print("JSON parse error.")
    except Exception as e:
        print(f"Recognition error: {e}")
    return ""

"""
