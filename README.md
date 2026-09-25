# Alex — a voice-first desktop AI assistant

Alex is a Windows desktop assistant you talk to. Start it, leave it running,
say **"Hey Alex"**, and ask it something. It wakes up locally (no audio is
sent anywhere until you say the wake phrase), converts your speech to text
offline, sends your actual request to an AI model through
[OpenRouter](https://openrouter.ai), and speaks the answer back using your
Windows voices.

It can also, with your explicit confirmation, open applications, click,
type, press keys, take screenshots, and search the web.

---

## What's in this project

```
Alex/
├── main.py                  entry point
├── requirements.txt
├── README.md                 (this file)
├── config/settings.py        settings storage (JSON + secure API key via keyring)
├── core/
│   ├── assistant.py           the request→AI→(tool)→reply pipeline
│   ├── voice_pipeline.py       the wake→listen→think→speak loop
│   ├── memory.py               remember/forget/recall
│   ├── planner.py               turns AI text into tool calls, safely
│   └── safety.py                 STOP switch + confirmation gate
├── ai/openrouter.py           OpenRouter API client (modular - see below)
├── voice/
│   ├── wake_word.py             local "Hey Alex" detector
│   ├── speech_to_text.py         offline speech recognition (Vosk)
│   ├── text_to_speech.py          offline speech synthesis (Windows voices)
│   └── model_manager.py            downloads the one-time speech model
├── tools/                     open_application, screenshot, click,
│                                type_text, press_key, web_search
├── ui/                        the PySide6 desktop interface
├── storage/database.py       local SQLite (memory, chat history, activity log)
├── assets/icon.ico            Alex's icon
└── build/build_exe.bat        builds dist\Alex.exe
```

---

## Requirements to build

- **Windows 10 or 11** (this app is built for Windows; the voice/TTS/tool
  layers use Windows-specific features).
- **Python 3.10, 3.11, or 3.12** from [python.org](https://www.python.org/downloads/),
  with "Add python.exe to PATH" checked during install.
- An internet connection for the one-time dependency install, and for the
  one-time ~40MB speech-recognition model download.
- A free [OpenRouter](https://openrouter.ai) account and API key.

---

## Getting an OpenRouter API key

1. Go to https://openrouter.ai and sign up (free).
2. Go to **Keys** in your account and create a new API key.
3. Copy it — you'll paste it into Alex's first-run screen or Settings.

**Important:** OpenRouter's free-tier models change over time and are
**not unlimited** — they carry rate limits and can become unavailable.
Alex ships with a placeholder default model in Settings
(`meta-llama/llama-3.3-70b-instruct:free`). If it stops responding, go to
https://openrouter.ai/models, filter by "free", pick a current one, and
paste its ID into **Settings → AI → Model**.

---

## Running from source (fastest way to try it)

```bat
cd Alex
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The first launch shows a setup screen for your API key, microphone, and
voice, and downloads the offline speech model. After that, `python main.py`
just opens Alex.

---

## Building Alex.exe

```bat
cd Alex
build\build_exe.bat
```

This script creates a virtual environment if needed, installs dependencies,
runs PyInstaller, and produces:

```
dist\Alex.exe
```

Double-click it to run Alex — Python does not need to be installed on the
machine you copy `Alex.exe` to. The speech-recognition model is **not**
bundled inside the exe (it's ~40MB and downloaded once, into
`%APPDATA%\Alex\models`, the first time Alex runs on a given machine) — this
keeps the exe itself small and is exactly what happens on first run.

**Note on this build:** I wrote, unit-tested, and headlessly ran every part
of this app's logic (settings, memory, the AI/tool pipeline, confirmation
and STOP enforcement, and the full PySide6 UI construction) in a Linux
sandbox while building it. I could not run `build_exe.bat` myself or hear
real audio, because PyInstaller has to build on the target OS and this
sandbox has no Windows, no microphone, and no speakers. Please run the test
checklist below yourself the first time — if anything in it fails, tell me
exactly what happened and I'll fix it.

---

## First-run setup

On first launch, Alex asks for:

- Your OpenRouter API key (you can also add/change this later in Settings)
- Which microphone to use
- Which installed Windows voice to speak with

It then downloads the offline speech model. If that download fails (e.g. no
internet at that moment), Alex still opens — voice input just won't work
until you retry (Settings has no explicit retry button in this version;
simplest fix is to delete `%APPDATA%\Alex\models` and relaunch, or just
relaunch once you have internet, since Alex checks on every startup).

---

## Using Alex

- Say **"Hey Alex"**. It replies "Yes?" and listens for your request.
- Or type into the chat box — typing always works as a backup.
- Or click the 🎙 button next to the chat box to trigger one listen-turn
  without saying the wake word.
- Say things like:
  - "What's the weather today?"
  - "Remember that my favorite programming language is Python."
  - "What's my favorite programming language?"
  - "Forget that my favorite programming language is Python."
  - "Open Notepad."
  - "Take a screenshot."
- Anything that clicks, types, or presses a key on your behalf will ask you
  to confirm first. The big **STOP** button at the bottom always cancels
  whatever Alex is doing and returns it to READY.

---

## Changing settings

Open the **Settings** tab in the sidebar:

- **AI** — API key, model, temperature
- **Voice** — microphone, TTS voice, volume, speech rate, on/off
- **Wake Word** — enable/disable, change the phrase from "Hey Alex"
- **Web** — enable/disable web search
- **Appearance** — dark mode, accent color, animation level
- **Startup** — start with Windows, start minimized

Click **Save Settings** — changes to voice, wake word, and appearance apply
immediately without restarting.

---

## Memory

The **Memory** tab lists everything Alex has been explicitly told to
remember. You can search, delete individual entries, or clear everything.
Nothing here is uploaded anywhere — it's a local SQLite file at
`%APPDATA%\Alex\alex.db`.

## Activity log

The **Activity** tab shows a plain log of what Alex has actually done —
wake events, tool calls with their results, denied confirmations, and
errors — for transparency into what an "AI assistant with computer control"
is doing on your machine.

---

## Testing checklist (please run this on your Windows machine)

- [ ] `python main.py` launches without errors
- [ ] First-run screen appears, accepts an API key, downloads the model
- [ ] Type "Hello Alex" in the chat box → get a real AI reply
- [ ] Say "Hey Alex" → status changes to LISTENING, Alex says "Yes?"
- [ ] Say "What can you do?" → recognized correctly, AI responds, Alex
      speaks the answer, status returns to READY
- [ ] Say "Hey Alex, remember that my favorite color is blue" → confirmation
      is spoken; restart Alex; ask "What's my favorite color?" → it recalls
      it correctly
- [ ] Say "Hey Alex, forget my favorite color" → Memory tab no longer shows it
- [ ] Say "Hey Alex, open Notepad" → Notepad opens, no confirmation prompt
      (open_application is treated as low-risk); Alex confirms verbally
- [ ] Say "Hey Alex, take a screenshot" → file appears under
      `%APPDATA%\Alex\screenshots`
- [ ] Ask Alex to do something that types or clicks → a confirmation dialog
      appears before anything happens; try both Yes and No
- [ ] While Alex is mid-response, click **STOP** → it stops immediately and
      returns to READY
- [ ] Unplug/disable your microphone → Alex shows "Microphone unavailable.
      Please select another microphone in Settings." instead of crashing
- [ ] Turn off Wi-Fi → ask Alex something → it says it's offline instead of
      crashing
- [ ] Enter a wrong API key in Settings → ask Alex something → it explains
      the key was rejected, not a raw stack trace
- [ ] `build\build_exe.bat` completes and `dist\Alex.exe` launches standalone
      on a machine without Python installed

---

## Troubleshooting

**"Speech recognition failed to load" / voice never activates**
The offline model download didn't finish. Delete the (possibly partial)
folder at `%APPDATA%\Alex\models`, make sure you have internet, and relaunch
Alex — it re-downloads automatically on startup if the model is missing.

**Alex responds with garbled JSON instead of a normal sentence**
This can happen with weaker free models that don't follow instructions well.
Switch to a different free (or paid) model in **Settings → AI → Model**.

**"That OpenRouter API key was rejected"**
Double check you copied the whole key from openrouter.ai, with no extra
spaces, and that it hasn't been revoked.

**Wake word never triggers, but typing works fine**
Check **Settings → Voice → Microphone** — pick the mic you're actually
speaking into. Also confirm **Settings → Wake Word → Enable wake word** is
checked.

**Alex opens but no sound comes out**
Check **Settings → Voice → Voice enabled** and **Volume**, and confirm
Windows itself has a working default output device.

**PyInstaller build fails**
Re-run `build\build_exe.bat` and read the error text above the "Build
failed" message — it's almost always a missing dependency, fixed by
re-running `pip install -r requirements.txt` inside `.venv`.

---

## Privacy & security notes

- Your OpenRouter API key is stored via Windows' own secure credential
  store (through the `keyring` library) — never in a plain file, never in
  source code, never logged.
- No microphone audio is streamed anywhere continuously. Wake-word detection
  and full speech-to-text both run locally via the offline Vosk model. Only
  your recognized *text* request is sent to OpenRouter, and only after the
  wake word (or typing, or the manual mic button) triggers a request.
- Computer-control tools are a fixed, explicit list (`open_application`,
  `screenshot`, `click`, `type_text`, `press_key`, `web_search`) — there is
  no shell execution, no arbitrary code execution, no keylogging, and no
  hidden persistence. Keyboard/mouse actions always require your
  confirmation first.
- The STOP button is wired directly to a safety switch the AI has no code
  path to disable.

---

## Extending Alex

- **New AI provider:** implement `ai/base.BaseAIProvider` and swap it in
  where `ui/main_window.py` builds `OpenRouterProvider`.
- **New tool:** add a module under `tools/` exposing a `TOOLS = [...]` list
  (see `tools/screenshot.py` for the simplest example), then add it to
  `tools/registry.py`'s `_TOOL_MODULES` list. Set `"confirm": True` if it
  should ask before running.
