import os
import queue
import random
import time
import socket
import subprocess
import shutil
from pathlib import Path
import eel
import config
from lib.main.features import *
from lib.main.command import *
from lib.auth import recognize
import lib.main.response as response


def _wait_port(host, port, timeout=10):
    """Silently wait for port to be ready without printing"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection((host, port), timeout=0.5)
            s.close()
            return True
        except OSError:
            time.sleep(0.5)
    return False


def start(hotword_queue=None):
    eel.init("ui")

    root = Path(__file__).resolve().parent
    bat = root / "device.bat"
    if bat.exists():
        try:
            print(f"Running {bat} ...")
            subprocess.run(str(bat), shell=True, check=False)
        except Exception as e:
            print(f"device.bat error: {e}")
    else:
        print(f"{bat} not found, skipping.")

    @eel.expose
    def init():
        # The UI shows "Initializing..." automatically
        # eel.sleep keeps the UI responsive while everything loads
        eel.sleep(2)

        eel.hideLoader()
        print("Ready for face authentication")
        speak("Ready for Face Authentication")
        flag = recognize.AuthenticateFace()
        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication was Successful")
            eel.hideFaceAuthSuccess()
            speak(random.choice(response.welcome_back_user))
            eel.hideStart()
        else:
            speak("Face Authentication has Failed")

    start_page = f"index.html?v={config.VERSION}"
    url = f"http://{config.HOST}:{config.PORT}/{start_page}"

    try:
        print("Starting Ivy...")
        eel.start(
            start_page,
            options={"mode": None, "host": config.HOST, "port": config.PORT},
            block=False,
        )
        print("Eel server started successfully")
    except Exception as e:
        print(f"Error starting Eel: {e}")
        try:
            print("Trying fallback port 5500...")
            eel.start("index.html", mode="default", port=5500, block=False)
        except Exception as e2:
            print(f"Fallback also failed: {e2}")

    def _open_app_window(u: str) -> bool:
        edge = shutil.which("msedge") or shutil.which("msedge.exe")
        chrome = shutil.which("chrome") or shutil.which("chrome.exe")
        candidates = [
            edge,
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            chrome,
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for exe in filter(None, candidates):
            if os.path.exists(exe):
                try:
                    subprocess.Popen([exe, "--new-window", f"--app={u}"])
                    return True
                except Exception as e:
                    pass
        try:
            os.startfile(u)
            return True
        except Exception as e:
            print("Failed to open browser:", e)
            return False

    # Wait silently for server - UI shows "Initializing..." during this time
    if _wait_port(config.HOST, config.PORT, timeout=5):
        print("Ivy is ready!")
        _open_app_window(url)
    else:
        # Even if port check times out, try opening anyway
        print("Opening Ivy...")
        _open_app_window(url)

    listening = False

    def _listen_from_hotword():
        nonlocal listening
        listening = True
        try:
            eel.ShowSiriWave()
            all_commands()
        finally:
            listening = False

    while True:
        eel.sleep(0.2)
        if hotword_queue is None:
            continue
        try:
            hotword_queue.get_nowait()
        except queue.Empty:
            continue
        if not listening:
            eel.spawn(_listen_from_hotword)
