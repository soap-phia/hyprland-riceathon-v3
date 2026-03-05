import atexit
import json
import signal
import subprocess
import sys
import threading
import time

_children = []


def _cleanup():
    for p in _children:
        try:
            p.kill()
        except Exception:
            pass


atexit.register(_cleanup)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

LENGTH = 22
PAD = 6
SPEED = 0.4
INTERVAL = 3

lock = threading.Lock()
state = {"status": "", "artist": "", "title": "", "app": ""}
last_output = ""


def set_state(status, artist, title, app):
    with lock:
        state.update(status=status, artist=artist, title=title, app=app)


def get_state():
    with lock:
        return state["status"], state["artist"], state["title"], state["app"]


def run(*args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


def emit(window):
    global last_output
    status, artist, title, app = get_state()

    if not title:
        out = {"text": "", "class": "empty", "alt": "empty"}
    else:
        cls = "playing" if status == "Playing" else "paused"
        alt = "spotify" if "spotify" in app.lower() else "default"
        tooltip = f"{artist}\n{title}" if artist else title
        out = {"text": f"  {window}", "alt": alt, "tooltip": tooltip, "class": cls}

    encoded = json.dumps(out)
    if encoded != last_output:
        print(encoded, flush=True)
        last_output = encoded


display_lock = threading.Condition()
display_text = ""


def set_scroll(text):
    global display_text
    with display_lock:
        display_text = text
        display_lock.notify()


def scroll():
    text = ""
    literals = ""
    padded = ""
    needs_scroll = False
    offset = 0

    while True:
        with display_lock:
            display_lock.wait(timeout=SPEED)
            if display_text != text:
                text = display_text
                offset = 0
                literals = text
                needs_scroll = len(literals) > LENGTH
                if needs_scroll:
                    padded = text + " " * PAD + text
                    emit(literals[:LENGTH])
                else:
                    emit(text)
                continue

        if not text:
            continue
        if not needs_scroll:
            emit(text)
            continue

        status = get_state()[0]
        if status != "Playing":
            offset = 0
            emit(literals[:LENGTH])
            continue

        window = padded[offset : offset + LENGTH]
        emit(window)
        offset = (offset + 1) % (len(literals) + PAD)


def get_apps():
    out = run("playerctl", "-l")
    return out.split("\n") if out else []


def get_status(app):
    return run("playerctl", "-p", app, "status") or "Stopped"


def get_metadata(app):
    out = run("playerctl", "-p", app, "metadata", "-f", "{{artist}}\t{{title}}")
    parts = out.split("\t", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (out, "")


def pick(apps):
    for p in apps:
        if "spotify" in p.lower():
            return p
    active = run("playerctl", "-a", "metadata", "-f", "{{playerName}}\t{{status}}")
    if active:
        for line in active.split("\n"):
            parts = line.split("\t", 1)
            if len(parts) == 2 and parts[1] == "Playing":
                return parts[0]
    return apps[0] if apps else ""


def make_text(artist, title):
    return f"{artist} — {title}" if artist else title


def follow(app):
    try:
        p = subprocess.Popen(
            ["playerctl", "-p", app, "metadata", "-f",
             "{{status}}\t{{artist}}\t{{title}}", "-F"],
            stdout=subprocess.PIPE, text=True,
        )
        _children.append(p)
        return p
    except Exception:
        return None


def _kill_proc(proc):
    try:
        proc.kill()
    except Exception:
        pass
    try:
        _children.remove(proc)
    except ValueError:
        pass


def main():
    threading.Thread(target=scroll, daemon=True).start()

    current = ""
    proc = None

    while True:
        apps = get_apps()
        app = pick(apps)

        if not app:
            set_state("Stopped", "", "", "")
            set_scroll("")
            time.sleep(INTERVAL)
            continue

        if app != current:
            if proc:
                _kill_proc(proc)
            current = app
            status = get_status(app)
            artist, title = get_metadata(app)
            set_state(status, artist, title, app)
            set_scroll(make_text(artist, title))
            proc = follow(app)

        if not proc or not proc.stdout:
            if proc:
                _kill_proc(proc)
            proc = None
            current = ""
            set_state("Stopped", "", "", "")
            set_scroll("")
            time.sleep(1)
            continue

        line = proc.stdout.readline()
        if not line:
            _kill_proc(proc)
            proc = None
            current = ""
            set_state("Stopped", "", "", "")
            set_scroll("")
            time.sleep(1)
            continue

        parts = line.strip().split("\t", 2)
        if len(parts) == 3:
            set_state(parts[0], parts[1], parts[2], app)
            set_scroll(make_text(parts[1], parts[2]))


if __name__ == "__main__":
    main()
