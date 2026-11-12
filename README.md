# 🚀 Let's Create Something Together!

> **Looking to build hands-on AI engineering experience, level up your resume with a real-world Jarvis project, or contribute to an open-source autonomous business assistant? You're in the right place!**
>
> Feel free to **Fork**, **Clone**, test new features, open a **Pull Request**, and collaborate. High-quality PRs will be reviewed and merged promptly. Use this project to showcase practical applied AI, local LLM orchestration, desktop automation, and RAG pipelines on your resume or portfolio.
>
> 🔗 **GitHub Repository:** [https://github.com/Ayush08k/Ruth-Business-AI-.git](https://github.com/Ayush08k/Ruth-Business-AI-.git)

---

# ⚡ RUTH — Autonomous AI Business Assistant & Executive Automation Engine

[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Local Engine](https://img.shields.io/badge/Local%20AI-Ollama%20%7C%20Llama%203.2-orange.svg)](https://ollama.com/)
[![Voice](https://img.shields.io/badge/TTS-Edge--TTS%20(Ultra--Soft)-purple.svg)](https://github.com/rany2/edge-tts)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](https://github.com/Ayush08k/Ruth-Business-AI-/pulls)
[![Operating Cost](https://img.shields.io/badge/Operating%20Cost-%240%2Fmonth%20(100%25%20Local)-brightgreen.svg)]()

**Ruth** is an autonomous, voice-driven AI business assistant engineered to automate daily operations, manage communications, execute Windows PC actions, answer business domain questions, and provide automated scheduled briefings — with **zero cloud subscription costs ($0/mo)** and **100% data privacy**.

---

## 🛠️ How It Works (System Architecture)

Ruth combines a local Large Language Model, persistent vector retrieval, and native operating system hooks to function as an end-to-end executive assistant:

```
                  ┌───────────────────────────────┐
                  │   🎙️ Voice / Text Input       │
                  │   ("Hey Ruth" Wake-Word / CLI)│
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ 👂 Whisper STT (Bilingual)    │
                  │ (Auto-detects English / Hindi)│
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ 🧠 Ruth Custom Decision Brain │
                  │  (Llama 3.2:1b via Ollama)    │
                  └───────┬───────────────┬───────┘
                          │               │
       Direct OS Actions  │               │ Business Queries
                          ▼               ▼
     ┌─────────────────────────┐     ┌─────────────────────────┐
     │ 🖥️ Windows Automation   │     │ 🗂️ Local Memory & RAG   │
     │  - Launch Applications  │     │  - ChromaDB Vector Store│
     │  - Web / YouTube Search │     │  - SQLite Interaction DB│
     │  - Typing & Hotkeys     │     │  - Crawled Business Data│
     │  - Media / Volume Ctrl  │     └────────────┬────────────┘
     └────────────┬────────────┘                  │
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ 🔊 Ultra-Soft Female TTS      │
                  │ (Edge-TTS Emma / Swara Neural)│
                  └───────────────────────────────┘
```

1. **Voice Capture & Transcription**: Listens continuously for wake triggers (*"Hey Ruth"*, *"Ruth"*, *"रूथ"*). Uses OpenAI Whisper locally to parse commands in real time.
2. **Context & Semantic Retrieval**: Searches your private ChromaDB vector embeddings for matched business facts, pricing, catalogs, and policies. If a query is outside your company's data, Ruth strictly refuses to hallucinate false information.
3. **Execution Engine**: Directs system-level commands to native Windows automation scripts (`pyautogui`, `pywinauto`, `webbrowser`, `subprocess`) to open software, type, or browse the web.
4. **Natural Acoustic Voice**: Generates calm, human-like voice responses via calibrated acoustic models (`-5Hz` pitch, `-15%` volume, relaxed pace).

---

## ✨ Key Features

### 🏢 1. Made to Automate Business Workflows
- **Knowledge Ingestion Pipeline**: Ingest any business website URL, customer FAQ, or product catalog into vector memory with a single command.
- **Strict Domain Bounds**: Ruth is configured to speak only on your business data — preventing awkward AI hallucinations with clients.
- **Email Categorization & Briefings**: Reads, summarizes, and classifies incoming emails and prepares morning executive briefings.

### 💻 2. Full Windows PC Automation
Control your entire computer completely hands-free:
- **Application Launcher**: Open any software (*"open Chrome"*, *"open Calculator"*, *"open VS Code"*, *"open Notepad"*, *"open Spotify"*).
- **Web & Video Search**: Instantly searches Google or YouTube (*"search on Google Next.js performance"*, *"search on YouTube deep focus music"*).
- **Keyboard & Mouse Automation**: Dictate text (*"type [message]"*), press key combinations (*"press enter"*, *"close active window"*), and take screenshots.
- **System Controls**: Adjust or mute system volume, pause/play background media.

### 🎙️ 3. Bilingual Voice & Calibrated Persona
- Speaks in **English** and **Hindi**.
- Tuned for an ultra-soft, warm, unhurried female voice (`en-US-EmmaMultilingualNeural` / `hi-IN-SwaraNeural`) that sounds conversational and non-intrusive.

### 🔒 4. 100% Private, Local & $0/Month
- Runs completely on your PC using **`llama3.2:1b`** via Ollama.
- Engineered specifically to run within **4GB RAM** on CPU.
- **Zero API keys required**, no subscription fees, and no client data ever leaves your computer.

---

## 📁 Repository Structure

```text
Ruth-Business-AI-/
├── run_ruth.py               # Main assistant execution script
├── LAUNCH_RUTH.bat           # 1-Click interactive launcher for Windows
├── START_RUTH.bat            # Quick command-line launcher
├── pull_model.py             # Pulls local Llama model via Ollama API
├── setup.py                  # One-click dependency installer
├── setup_model.py            # Local model configurator
├── requirements.txt          # Python package requirements
├── .env.example              # Sample environment configuration
├── .gitignore                # Protects local DBs, memory, and logs
└── ruth/
    ├── config.py             # Central configuration loader
    ├── agent/
    │   └── brain.py          # Strict RAG decision engine & tool router
    ├── voice/
    │   ├── listener.py       # Whisper speech-to-text & wake-word engine
    │   └── speaker.py        # Ultra-soft female voice synthesizer
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

## ⚡ Quick Start Guide

### 1. Prerequisites
- **Windows 10/11**
- **Python 3.11+** installed and added to `PATH`
- **Ollama for Windows** installed from [ollama.com/download](https://ollama.com/download)

### 2. Clone the Repository
```powershell
git clone https://github.com/Ayush08k/Ruth-Business-AI-.git
cd Ruth-Business-AI-
```

### 3. Install Dependencies
```powershell
python setup.py
```

### 4. Pull the Local Model
Ensure Ollama is running (`ollama serve`), then run:
```powershell
ollama pull llama3.2:1b
```

### 5. Start Ruth
Double-click **`LAUNCH_RUTH.bat`** or run:

- **Voice Mode (Full Jarvis experience):**
  ```powershell
  python run_ruth.py
  ```
- **Text / CLI Mode (Type commands without mic):**
  ```powershell
  python run_ruth.py --text
  ```

---

## 📚 Training Ruth on Your Business

Feed your company's documents, website, or policies into Ruth:

```powershell
python run_ruth.py --train
```

- **Option 4**: Crawl and ingest any business website URL into vector memory.
- **Option 2**: Add targeted Q&A pairs (e.g. pricing, refund rules, client onboarding steps).
- **Option 1**: Upload `.pdf`, `.docx`, or `.txt` documentation.

---

## 🤝 Contributing & Pull Requests

We want this to be the best open-source local AI assistant available! Whether you're fixing a bug, adding new PC automation features, optimizing prompts, or improving voice responsiveness:

1. **Fork the Repository**
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/AmazingNewFeature
   ```
3. **Commit Your Changes**:
   ```bash
   git commit -m "feat: add AmazingNewFeature to Ruth"
   ```
4. **Push to the Branch**:
   ```bash
   git push origin feature/AmazingNewFeature
   ```
5. **Open a Pull Request**: Submit your PR on GitHub, detail your improvements, and it will be reviewed and merged!

Add this project to your portfolio or resume to demonstrate practical proficiency with **Applied AI, Local LLM Inference, LangChain, Vector Databases (ChromaDB), and Windows OS Automation**.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.
