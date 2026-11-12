# ⚡ RUTH — Autonomous AI Business Assistant & Jarvis System

> **A 100% private, local voice-first AI executive assistant designed to manage business workflows, automate Windows PC tasks, answer website inquiries, and deliver scheduled reports.**

[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Local Engine](https://img.shields.io/badge/Local%20AI-Ollama%20%7C%20Llama%203.2-orange.svg)](https://ollama.com/)
[![Voice](https://img.shields.io/badge/TTS-Edge--TTS%20(Ultra--Soft)-purple.svg)](https://github.com/rany2/edge-tts)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Cost](https://img.shields.io/badge/Operating%20Cost-%240%2Fmonth-brightgreen.svg)]()

---

## 🌟 Overview

**Ruth** is a customizable, offline-capable AI business assistant inspired by Tony Stark's J.A.R.V.I.S. Rather than relying on rigid if/else statements or cloud APIs that leak business data, Ruth runs **entirely on your local machine** using `llama3.2:1b` (via Ollama) and a ChromaDB vector database.

She strictly knows **your business data** (ingested from [freelanceayush.com](https://freelanceayush.com) and your documents) and executes full Windows operating system tasks via voice or text commands.

---

## 🚀 Key Features

### 1. 🧠 Strict Business & Website RAG (No Hallucinations)
- **Zero general-trivia spam**: Ruth refuses to answer random trivia questions outside your domain.
- **Trained on your real website**: Scrapes and indexes your portfolio, projects, services, blog posts, and rates.
- **Local vector memory**: Uses ChromaDB and Sentence-Transformers on disk to store interactions and documents forever.

### 2. 💻 Full Windows Desktop & PC Automation
Command Ruth to take direct action on your PC:
- **Launch Any App**: `"open Chrome"`, `"open Calculator"`, `"open Notepad"`, `"open VS Code"`, `"open Spotify"`.
- **Web Navigation**: `"search on Google Next.js performance"`, `"search on YouTube lo-fi beats"`.
- **Keyboard & Mouse Control**: `"type [text]"`, `"press enter"`, `"close active window"`, `"click"`.
- **Hardware & Media**: `"volume up"`, `"volume down"`, `"mute"`, `"take screenshot"`.

### 3. 🎙️ Continuous Voice I/O (Bilingual + Ultra-Soft Voice)
- **Always-on Wake-Word**: Listens for *"Hey Ruth"*, *"Ruth"*, or Hindi *"रूथ"*.
- **Speech-to-Text (STT)**: Offline Whisper model with automatic English/Hindi language detection.
- **Text-to-Speech (TTS)**: Ultra-soft, gentle female voice (`en-US-EmmaMultilingualNeural` / `hi-IN-SwaraNeural`) with calibrated warm acoustic pitch (`-5Hz`), unhurried cadence (`-7%`), and gentle volume (`-15%`).

### 4. 📧 Automated Reporting & Email Management
- Reads and categorizes incoming unread emails via OAuth2.
- Generates morning voice briefings and structured HTML email reports summarizing website uptime, task queues, and email notifications.

### 5. ⚡ 4GB RAM & $0/Month Friendly
- Specifically engineered to run smoothly on machines with **4GB RAM** on CPU.
- **Zero cloud API subscriptions** — runs 100% free forever.

---

## 📁 Architecture & File Structure

```text
d:\Ruth\
├── run_ruth.py               # Main launcher (Voice or Keyboard modes)
├── LAUNCH_RUTH.bat           # 1-Click interactive launcher for Windows
├── START_RUTH.bat            # Alternative launcher menu
├── pull_model.py             # Script to pull local Llama model via Ollama
├── setup.py                  # One-click dependency installer
├── requirements.txt          # Python packages
├── .env                      # Local configuration (never pushed)
├── .env.example              # Environment variables template
├── .gitignore                # Protects local DBs, logs, and audio caches
└── ruth/
    ├── config.py             # System configuration loader
    ├── agent/
    │   └── brain.py          # Strict RAG decision engine, prompt & tools router
    ├── voice/
    │   ├── listener.py       # Whisper STT & wake-word detection engine
    │   └── speaker.py        # Edge-TTS soft female speech output
    ├── tools/
    │   ├── pc_control.py     # OS automation (apps, keyboard, mouse, media)
    │   └── tools.py          # Unified tool registry
    ├── memory/
    │   └── memory_store.py   # ChromaDB vector recall + SQLite persistent memory
    ├── training/
    │   └── trainer.py        # Website crawler & document training pipeline
    ├── integrations/
    │   ├── email.py          # Gmail read/draft/reporting manager
    │   └── website.py        # Website health & uptime monitor
    └── reporting/
        └── engine.py         # Scheduled morning briefings & summaries
```

---

## 🛠️ Quick Installation

### Prerequisites
1. **Windows 10/11**
2. **Python 3.11+** installed and added to `PATH`.
3. **Ollama for Windows**: Download from [ollama.com/download](https://ollama.com/download).

### Step 1: Clone Repository
```powershell
git clone https://github.com/Ayush08k/Ruth-Business-AI-.git
cd Ruth-Business-AI-
```

### Step 2: Install Dependencies
```powershell
python setup.py
```

### Step 3: Pull Local AI Engine
Make sure Ollama is running (`ollama serve`), then pull the lightweight model:
```powershell
ollama pull llama3.2:1b
```

---

## 🎯 How to Use

### 1. Launch Ruth
Simply double-click **`LAUNCH_RUTH.bat`** or run in your terminal:

- **Voice Assistant Mode (Full Jarvis Experience):**
  ```powershell
  python run_ruth.py
  ```
  *Say "Hey Ruth, what services does Ayush offer?" or "Hey Ruth, open Chrome".*

- **Console / Text Mode (Test without Microphone):**
  ```powershell
  python run_ruth.py --text
  ```

### 2. Train Ruth on Additional Documents / Sites
```powershell
python run_ruth.py --train
```
- **Option 4**: Crawl and ingest any website URL into vector memory.
- **Option 2**: Add targeted Q&A pairs (e.g. pricing, policies).
- **Option 1**: Upload `.pdf`, `.docx`, `.txt` business documentation.

---

## 🗣️ Example Commands

| Command | Action |
|---|---|
| *"Ruth, what services does Ayush offer?"* | Answers strictly from `freelanceayush.com` data |
| *"Ruth, tell me about the Starbucks 3D project"* | Details your project portfolio |
| *"Ruth, open Calculator"* | Launches Windows Calculator |
| *"Ruth, search on Google Next.js performance"* | Opens browser and searches Google |
| *"Ruth, search on YouTube lo-fi music"* | Opens YouTube with query results |
| *"Ruth, type Hello from Ruth AI"* | Types text into active window |
| *"Ruth, volume up / down / mute"* | Controls system volume |
| *"Ruth, check my website status"* | Checks `freelanceayush.com` uptime |
| *"Ruth, kya kaam pending hai?"* | Lists task queue in Hindi |

---

## 🛡️ Privacy & Security

- All vector embeddings and conversation histories remain strictly on your local disk in `ruth_data/`.
- No customer conversations, queries, or screen interactions are uploaded to any external cloud API or third-party server.

---

## 👤 Author
**Ayush**
- Website: [freelanceayush.com](https://freelanceayush.com)
- GitHub: [@Ayush08k](https://github.com/Ayush08k)

---
*Built with Python, LangGraph, Ollama, Whisper, and Edge-TTS.*
