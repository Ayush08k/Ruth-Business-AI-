# 🤖 RUTH — Private AI Business Assistant
### 100% Local • No External APIs • Trained Only on YOUR Data

Ruth only answers questions about YOUR business.
She will NOT answer general knowledge questions — only what you teach her.

---

## How Ruth Works (Custom AI)

```
Your Documents / Website / Q&A
         ↓
    Ruth's Memory (ChromaDB - local)
         ↓
    Local AI (Ollama - on your PC)
         ↓
    Answer — ONLY from your data
```

If she doesn't know → she says: "I don't have that information. Please train me."

---

## Quick Start (3 Steps)

### Step 1 — Install Ollama (Local AI Engine)
Download from: **https://ollama.com/download** → install → restart PC

### Step 2 — Setup AI Model (run once)
```
python setup_model.py
```
Choose `phi3:mini` (recommended for 4GB RAM) — downloads once (~2.3GB)

### Step 3 — Train Ruth with YOUR Data
```
python run_ruth.py --train
```
Choose what to add:
- **Option 2 (Q&A pairs)** — most reliable — type your own Q&A
- **Option 4 (Scrape website)** — auto-learns from your website
- **Option 1 (Upload docs)** — upload PDF/Word/TXT files

### Step 4 — Start Ruth
```
python run_ruth.py --text    # Test without mic first
python run_ruth.py           # Full voice mode
```

Or double-click **START_RUTH.bat** ✅

---

## Training Examples

### Add Q&A Pairs (best method)
When you run training mode and choose option 2:
```
Question: What products do you sell?
Answer:   We sell handmade leather bags, wallets, and belts.

Question: What are your business hours?
Answer:   Monday to Saturday, 9 AM to 7 PM IST.

Question: What is your return policy?
Answer:   We accept returns within 30 days with original packaging.
```

### Scrape Your Website
Choose option 4, enter your website URL.
Ruth will automatically read all your pages and learn from them.

### Upload Documents
Choose option 1, provide path to PDF/Word/TXT file.
Great for: price lists, product catalogs, SOPs, FAQs.

---

## Voice Commands (after training)

| You Say | Ruth Does |
|---|---|
| "Hey Ruth, check my emails" | Email summary |
| "Hey Ruth, website ka status batao" | Website status (Hindi) |
| "Hey Ruth, kya products hai hamare?" | Answers from your data (Hindi) |
| "Hey Ruth, add task: call client" | Adds task |
| "Hey Ruth, send me a report" | Emails business report |

---

## What Ruth WILL Answer
✅ Questions about YOUR products/services  
✅ Questions about YOUR business hours, policies, pricing  
✅ Questions from your uploaded documents  
✅ Email summaries, website status, task management  
✅ Anything you explicitly train her on  

## What Ruth WILL NOT Answer
❌ General knowledge questions  
❌ News, weather (outside your data)  
❌ Anything not in her training data  
→ She says: "I don't have that information. Please train me."

---

## Project Files

```
d:\Ruth\
├── run_ruth.py       → Main launcher
├── setup_model.py    → Download AI model (run once)
├── setup.py          → Install Python packages
├── START_RUTH.bat    → Windows menu launcher
├── .env              → Your settings (no API keys needed!)
└── ruth/
    ├── agent/        → Custom AI brain (Ollama + strict RAG)
    ├── voice/        → Whisper STT + Edge-TTS (female voice)
    ├── integrations/ → Email + website monitor
    ├── memory/       → Local ChromaDB + SQLite
    ├── reporting/    → Scheduled reports
    └── training/     → Upload docs, Q&A, website scraper
```

---

## Cost: $0 — Fully Free & Private
- No API keys needed
- No data sent anywhere
- Runs entirely on your Windows PC
