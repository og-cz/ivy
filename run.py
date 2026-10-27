import multiprocessing as mp


def start_ivy(hotword_queue):
    print("UI process is running.")
    from main import start

    start(hotword_queue)


def listen_hotword(hotword_queue):
    print("Hotword process is running.")
    from lib.main.features import hotword

    hotword(hotword_queue)


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    hotword_queue = mp.Queue()
    p1 = mp.Process(target=start_ivy, args=(hotword_queue,), daemon=False)
    p2 = mp.Process(target=listen_hotword, args=(hotword_queue,), daemon=True)
    p1.start()
    p2.start()
    p1.join()
    if p2.is_alive():
        p2.terminate()
        p2.join()
