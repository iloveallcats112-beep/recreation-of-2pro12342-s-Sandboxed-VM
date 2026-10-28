"""Sandboxed VM — Made by 2pro12342.

Run as main.py in a CodeHS Python Graphics (tkinter) sandbox.
This is a real Linux desktop session with native applications, not an OS mockup.
Packages are extracted into this program's own directory, without sudo.
Roblox is a website shortcut; a native Roblox Linux client is not included.
"""
import atexit
import json
import math
import os
from pathlib import Path
import queue
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
import tkinter as tk
from tkinter import messagebox
from xml.sax.saxutils import escape
from concurrent.futures import ThreadPoolExecutor

TITLE = "Linux Web Desktop"
AUTHOR = "2pro12342"
# Explicitly approved by the user for Chrome inside this CodeHS Linux session.
# Set False to require Chrome's own sandbox and block unsupported launches.
ALLOW_CHROME_WITHOUT_SANDBOX = True
HERE = Path(__file__).resolve().parent
BASE = HERE / ".sandboxed-vm-linux"
RUNTIME = BASE / "runtime"
DOWNLOADS = BASE / "downloads"
DOCUMENTS = HERE / "Documents"
LOGS = BASE / "logs"
APPS = BASE / "apps"
USER_APPS = BASE / "user-apps"
USER_APP_DB = BASE / "user-apps.json"
SOCKET = BASE / "control.sock"
SCRIPT = Path(__file__).resolve()
for directory in (BASE, RUNTIME, DOWNLOADS, DOCUMENTS, LOGS, APPS, USER_APPS, BASE / "profiles", BASE / "run", BASE / "icons"):
    directory.mkdir(parents=True, exist_ok=True)


def environment():
    env = os.environ.copy()
    libdirs = [
        USER_APPS / "usr/lib/x86_64-linux-gnu",
        USER_APPS / "lib/x86_64-linux-gnu",
        USER_APPS / "usr/lib",
        USER_APPS / "lib",
        RUNTIME / "usr/lib/x86_64-linux-gnu",
        RUNTIME / "lib/x86_64-linux-gnu",
        RUNTIME / "usr/lib",
        RUNTIME / "lib",
    ]
    env["LD_LIBRARY_PATH"] = ":".join([str(p) for p in libdirs if p.exists()] + [env.get("LD_LIBRARY_PATH", "")])
    env["PATH"] = ":".join([
        str(USER_APPS / "usr/bin"), str(USER_APPS / "bin"),
        str(RUNTIME / "usr/bin"), env.get("PATH", "")
    ])
    env["XDG_DATA_DIRS"] = str(RUNTIME / "usr/share") + ":" + env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    env["XDG_RUNTIME_DIR"] = str(BASE / "run")
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=" + str(BASE / "run/bus")
    env["NO_AT_BRIDGE"] = "1"
    env["GTK_A11Y"] = "none"
    env["DISPLAY"] = os.environ.get("DISPLAY", ":99")
    return env


def client(action):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(3)
            connection.connect(str(SOCKET))
            connection.sendall((json.dumps({"action": action}) + "\n").encode())
            print(connection.recv(16384).decode())
        return 0
    except OSError as exc:
        print("Start Sandboxed VM first:", exc)
        return 1


def checked(command, log_name="setup.log", timeout=240, env=None):
    with (LOGS / log_name).open("ab", buffering=0) as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, env=env)
    if result.returncode:
        detail = (LOGS / log_name).read_text(errors="replace")[-2200:]
        raise RuntimeError("{} failed ({}).\n{}".format(Path(command[0]).name, result.returncode, detail))


def fetch(url, destination):
