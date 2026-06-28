# 🍳 Dinner Suggestion App

A tiny local web app that suggests **2 quick dinner recipes** based on the
ingredients you have and how much time you've got. Built with
[Streamlit](https://streamlit.io/) + the [Gemini API](https://ai.google.dev/),
and designed to be opened from your iPhone on the same WiFi.

It runs entirely on your own computer — no accounts, no database, your API key
never leaves your machine.

---

## 1. Setup (one time)

### a. Install dependencies

```powershell
cd dinner-suggestion-app
pip install -r requirements.txt
```

> Tip: a virtual environment keeps things tidy.
> ```powershell
> python -m venv .venv
> .\.venv\Scripts\Activate.ps1
> pip install -r requirements.txt
> ```

### b. Add your API key

1. Get a **free** Gemini API key at <https://aistudio.google.com/app/apikey>.
2. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `.env` and paste your key:
   ```
   GEMINI_API_KEY=AIza...your_real_key...
   ```

`.env` is git-ignored, so your key won't be committed.

---

## 2. Run it (on your computer)

```powershell
python -m streamlit run app.py
```

Your browser opens at <http://localhost:8501>.

> Why `python -m streamlit` and not just `streamlit`? On this machine the
> `streamlit` command isn't on the system PATH, so `python -m streamlit` is the
> reliable way to launch it. (Plain `streamlit run app.py` works too **if** you
> add `%APPDATA%\Python\Python313\Scripts` to your PATH.)

---

## 3. Open it on your iPhone (same WiFi)

Streamlit only listens on `localhost` by default, so do this instead:

```powershell
python -m streamlit run app.py --server.address 0.0.0.0
```

Then find your PC's local IP address:

```powershell
ipconfig
```

Look for **IPv4 Address** under your WiFi adapter (e.g. `192.168.1.42`).
On your iPhone's Safari, visit:

```
http://192.168.1.42:8501
```

### If the phone can't connect — open the firewall

Windows likely blocks the port. Allow it once (run PowerShell **as
Administrator**):

```powershell
New-NetFirewallRule -DisplayName "Streamlit 8501" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

> Both devices must be on the **same WiFi network**. Some routers with "client
> isolation"/"guest network" enabled will block device-to-device traffic.

---

## 4. How it works

- You type ingredients, pick a time limit (15/30/60 min), and tap **Suggest Meals**.
- The app asks Gemini for **exactly 2 recipes** using a strict JSON schema
  (`RecipeSuggestions` in `app.py`), so the output is always structured —
  no fragile text parsing.
- Each recipe shows a name, a one-line "why it fits," and up to 6 short steps.
- **Regenerate** asks again with a fresh random seed for different ideas.

---

## 5. Project structure

```
dinner-suggestion-app/
├── app.py             # The whole app (UI + Gemini call + schema)
├── requirements.txt   # Dependencies
├── .env.example       # Template for your API key
├── .env               # Your real key (git-ignored, you create this)
├── .gitignore
└── README.md
```

---

## 6. Swapping the AI provider (optional, for learning)

The model call is isolated in `generate_recipes()` in `app.py`. To use a
different provider (e.g. OpenAI), replace the body of that function with your
provider's structured-output call and return a `list[Recipe]`. Everything else
(UI, validation, rendering) stays the same.

---

## 7. Out of scope (MVP)

No grocery lists, nutrition tracking, history, accounts, or cloud hosting — by
design. See the project notes for the future roadmap.
