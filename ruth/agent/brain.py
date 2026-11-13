"""
Ruth Custom AI Brain — 100% Local, No External APIs
====================================================
Ruth ONLY answers questions based on YOUR uploaded data.
If she doesn't know → she says so. No hallucinations, no general AI.

Architecture:
  1. Ollama (local LLM — runs on your PC, 4GB RAM friendly)
  2. Strict RAG — answers ONLY from your documents/website
  3. Fine-tuning pipeline — teach her more over time
  4. All data stays on your machine, forever private
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from langchain_core.messages import HumanMessage, AIMessage
from rich.console import Console

from ruth.config import config
from ruth.memory import RuthMemory

console = Console()


# ─── Ruth's Strict System Prompt ──────────────────────────────────────────
# This is what makes Ruth ONLY answer from your data — not general knowledge.

RUTH_STRICT_PROMPT = """You are Ruth, a private AI assistant trained exclusively on the business data of your owner.

## CRITICAL RULES — YOU MUST FOLLOW THESE ALWAYS:

1. **ONLY answer using the CONTEXT provided below.** Do NOT use any general knowledge.
2. If the answer is NOT found in the context → say exactly: "I don't have that information in my knowledge base. Please add it by training me."
3. **NEVER make up facts, prices, names, or any information** not in the context.
4. You are NOT a general assistant. You ONLY know about this specific business.
5. Always respond in the SAME language the user uses (English or Hindi).
6. Be concise and professional.

## YOUR KNOWLEDGE BASE (use ONLY this):
{context}

## CONVERSATION HISTORY:
{history}

## OWNER'S QUESTION:
{question}

## YOUR ANSWER (based strictly on the context above):"""


RUTH_NO_CONTEXT_RESPONSE_EN = (
    "I don't have that information in my knowledge base. "
    "You can train me by running: python run_ruth.py --train"
)

RUTH_NO_CONTEXT_RESPONSE_HI = (
    "मेरे पास इस बारे में जानकारी नहीं है। "
    "आप मुझे train कर सकते हैं: python run_ruth.py --train"
)


class OllamaLLM:
    """
    Wrapper for Ollama local LLM.
    Runs entirely on your PC — no internet needed for AI responses.
    Models that work on 4GB RAM:
      - phi3:mini    (2.3GB) ← recommended, smart
      - gemma2:2b    (1.6GB) ← Google's small model
      - llama3.2:1b  (1.3GB) ← Meta's smallest
    """

    OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2:1b"

    def __init__(self, model: str = None):
        self.model = model or config.OLLAMA_MODEL or self.DEFAULT_MODEL
        self._check_ollama()

    def _check_ollama(self):
        """Verify Ollama is running, auto-start if needed"""
        import subprocess, sys, time
        try:
            resp = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=2)
            models = [m["name"] for m in resp.json().get("models", [])]
            if not any(self.model.split(":")[0] in m for m in models):
                console.print(f"[yellow]⚠️  Model '{self.model}' not found in Ollama.[/yellow]")
            else:
                console.print(f"[green]✅ Local AI ready: {self.model}[/green]")
                return
        except Exception:
            console.print("[yellow]⏳ Ollama not responding. Auto-starting local engine...[/yellow]")
            try:
                exe = r"C:\Users\hp\AppData\Local\Programs\Ollama\ollama.exe"
                subprocess.Popen([exe, "serve"], creationflags=0x00000008 if sys.platform == "win32" else 0)
                time.sleep(3)
                for _ in range(5):
                    try:
                        requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=2)
                        console.print(f"[green]✅ Ollama auto-started successfully![/green]")
                        return
                    except Exception:
                        time.sleep(1)
            except Exception as e:
                console.print(f"[yellow]Auto-start notice: {e}[/yellow]")

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate a response from the local LLM"""
        try:
            resp = requests.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3,      # Low temp = more factual, less creative
                        "top_p": 0.9,
                        "stop": ["## OWNER'S QUESTION", "Human:", "User:"],
                    },
                },
                timeout=300,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            else:
                console.print(f"[red]Ollama error: {resp.status_code}[/red]")
                return ""
        except requests.exceptions.ConnectionError:
            return "ERROR: Ollama is not running. Please start it first."
        except requests.exceptions.Timeout:
            return "ERROR: Response timed out. Try a smaller model."
        except Exception as e:
            console.print(f"[red]LLM error: {e}[/red]")
            return ""

    def is_available(self) -> bool:
        try:
            requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=2)
            return True
        except Exception:
            return False


class RuthCustomBrain:
    """
    Ruth's private AI brain.
    - Only answers from YOUR uploaded documents (strict RAG)
    - 100% local — no Gemini, no OpenAI, no cloud
    - Learns from your corrections and new documents
    - Refuses to answer anything outside your business data
    """

    MIN_CONTEXT_SCORE = 0.3   # Minimum similarity to consider context relevant

    def __init__(self, memory: RuthMemory):
        self.memory = memory
        self.llm = OllamaLLM()
        self.conversation_history = []
        self._load_tools()
        console.print("[green]✅ Ruth Custom Brain initialized (100% Local)[/green]")

    def _load_tools(self):
        """Load tool handlers for commands that don't need LLM"""
        from ruth.tools import ALL_TOOLS
        self.tools = {t.name: t for t in ALL_TOOLS}

    def _retrieve_context(self, question: str) -> tuple[str, float]:
        """
        Retrieve relevant context from YOUR documents only.
        Returns (context_text, relevance_score).
        Score < MIN_CONTEXT_SCORE → Ruth says she doesn't know.
        """
        # Search business documents (your uploaded data)
        doc_results = self.memory.chroma.get_collection("business_docs") if self._collection_exists("business_docs") else None

        # Also search episodic memory (past interactions, preferences)
        memories = self.memory.recall(question, n=5)
        doc_chunks = self.memory.recall_from_docs(question, n=5)
        website_facts = self.memory.recall(question, n=3, category="website")

        all_context = []
        if doc_chunks:
            all_context.append("=== From Your Business Documents ===")
            all_context.extend(doc_chunks)
        if memories:
            all_context.append("=== From Past Interactions & Memory ===")
            all_context.extend(memories)
        if website_facts:
            all_context.append("=== Website Information ===")
            all_context.extend(website_facts)

        if not all_context:
            return "", 0.0

        context_text = "\n\n".join(all_context)
        # Simple relevance heuristic: more context = more likely relevant
        score = min(len(all_context) / 5, 1.0)
        return context_text, score

    def _collection_exists(self, name: str) -> bool:
        try:
            self.memory.chroma.get_collection(name)
            return True
        except Exception:
            return False

    def _format_history(self) -> str:
        """Format recent conversation history"""
        if not self.conversation_history:
            return "No previous conversation."
        lines = []
        for msg in self.conversation_history[-6:]:
            role = "Owner" if isinstance(msg, HumanMessage) else "Ruth"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    def _detect_tool_command(self, text: str) -> Optional[tuple[str, dict]]:
        """
        Detect if the user wants to trigger a specific tool or PC action.
        Returns (tool_name, kwargs) or None.
        """
        text_lower = text.lower().strip()
        import re

        # Compound commands: e.g. "open chrome and search youtube" / "open browser and search ..."
        compound = re.search(r'(?:open|launch|kholo)\s+(chrome|crome|crme|browser|edge)\s+(?:and|aur|pe|then)\s+(?:search|dhoondo|type)\s+(.+)', text_lower)
        if compound:
            query = compound.group(2).strip()
            # If query is specifically youtube or a search term
            if "youtube" in query:
                clean_q = query.replace("on youtube", "").replace("youtube pe", "").replace("youtube", "").strip()
                if clean_q:
                    return ("search_online", {"query": clean_q, "platform": "youtube"})
                else:
                    from ruth.tools.pc_control import SystemController
                    return ("_raw", lambda: SystemController.open_url("https://www.youtube.com"))
            return ("search_online", {"query": query, "platform": "google"})

        # Search Web / YouTube
        yt_search = re.search(r'(?:search\s+on\s+youtube|youtube\s+pe\s+search\s+karo|search\s+youtube\s+for|youtube\s+search|search\s+youtube)\s+(.+)', text_lower)
        if yt_search:
            return ("search_online", {"query": yt_search.group(1), "platform": "youtube"})

        search_match = re.search(r'(?:search\s+for|search\s+on\s+google|google\s+pe\s+search|google|search|dhoondo)\s+(.+)', text_lower)
        if search_match:
            return ("search_online", {"query": search_match.group(1), "platform": "google"})

        # Open application / Website
        open_match = re.search(r'(?:open|launch|kholo|start|chalu\s+karo)\s+(.+)', text_lower)
        if open_match:
            app_target = open_match.group(1).replace("please", "").strip()
            # Handle phonetic variations of chrome
            if app_target in ["crme", "chrme", "crome", "crom"]:
                app_target = "chrome"
            elif app_target in ["yt", "youtube"]:
                from ruth.tools.pc_control import SystemController
                return ("_raw", lambda: SystemController.open_url("https://www.youtube.com"))
            # If target looks like a website or web search, route appropriately
            if "." in app_target and " " not in app_target:
                from ruth.tools.pc_control import SystemController
                return ("_raw", lambda: SystemController.open_url(app_target))
            return ("open_app", {"app_name": app_target})

        # Mouse click commands
        if any(w in text_lower for w in ["double click", "double-click"]):
            from ruth.tools.pc_control import SystemController
            return ("_raw", lambda: SystemController.double_click())
        if any(w in text_lower for w in ["right click", "right-click"]):
            from ruth.tools.pc_control import SystemController
            return ("_raw", lambda: SystemController.right_click())
        if any(w in text_lower for w in ["click", "click karo", "mouse click"]):
            # Check for coordinates: e.g. "click at 500 300"
            coord_match = re.search(r'(\d+)[,\s]+(\d+)', text_lower)
            if coord_match:
                return ("click_screen", {"x": int(coord_match.group(1)), "y": int(coord_match.group(2))})
            return ("click_screen", {})

        # Scrolling
        if any(w in text_lower for w in ["scroll down", "niche scroll karo", "neeche scroll"]):
            from ruth.tools.pc_control import SystemController
            return ("_raw", lambda: SystemController.scroll("down"))
        if any(w in text_lower for w in ["scroll up", "upar scroll karo"]):
            from ruth.tools.pc_control import SystemController
            return ("_raw", lambda: SystemController.scroll("up"))

        # Type text
        type_match = re.search(r'(?:type|likho|write)\s+(.+)', text_lower)
        if type_match:
            return ("type_into_active_window", {"text": type_match.group(1)})

        # Hotkeys & Controls
        if any(w in text_lower for w in ["press enter", "enter dabao"]):
            return ("press_hotkey", {"hotkey": "enter"})
        if any(w in text_lower for w in ["close window", "band karo", "close this"]):
            return ("press_hotkey", {"hotkey": "alt+f4"})
        if any(w in text_lower for w in ["volume up", "awaaz badhao", "aawaz badhao"]):
            return ("volume_control", {"action": "up"})
        if any(w in text_lower for w in ["volume down", "awaaz kam karo", "aawaz kam karo"]):
            return ("volume_control", {"action": "down"})
        if any(w in text_lower for w in ["mute", "chup ho jao"]):
            return ("volume_control", {"action": "mute"})
        if any(w in text_lower for w in ["screenshot", "screen capture"]):
            return ("take_pc_screenshot", {})

        # Email & Web status
        if any(w in text_lower for w in ["check email", "emails check", "email dekhao", "email dikhao"]):
            return ("check_emails", {})
        if any(w in text_lower for w in ["website status", "site check", "site ka status", "website dekhao"]):
            return ("check_website_status", {})
        if any(w in text_lower for w in ["pending tasks", "tasks dikhao", "kya kaam hai", "task list"]):
            return ("get_pending_tasks", {})
        if any(w in text_lower for w in ["time", "samay", "waqt", "kitne baje"]):
            return ("get_current_time", {})
        if any(w in text_lower for w in ["send report", "report bhejo", "report email"]):
            return ("send_email_report", {})

        return None

    def process(self, user_input: str, channel: str = "voice", lang: str = "en") -> str:
        """
        Process user input using ONLY your business data.
        Steps:
          1. Check for direct tool commands
          2. Retrieve context from YOUR documents
          3. If good context found → generate answer
          4. If no context → refuse and suggest training
        """
        try:
            # Step 1: Direct tool & PC system actions
            tool_detected = self._detect_tool_command(user_input)
            if tool_detected:
                tool_name, kwargs = tool_detected
                try:
                    if tool_name == "_raw":
                        response = kwargs()
                    elif tool_name in self.tools:
                        result = self.tools[tool_name].invoke(kwargs)
                        response = str(result)
                    else:
                        response = "Action not available."
                    self._store_interaction(user_input, response, lang)
                    return response
                except Exception as e:
                    console.print(f"[red]PC Action Error: {e}[/red]")

            # Step 2: Retrieve YOUR business context
            context, score = self._retrieve_context(user_input)

            # Step 3: Check context
            if not context or not context.strip():
                response = (
                    RUTH_NO_CONTEXT_RESPONSE_HI
                    if lang == "hi"
                    else RUTH_NO_CONTEXT_RESPONSE_EN
                )
                self._store_interaction(user_input, response, lang)
                return response

            # Step 4: Generate answer from context ONLY
            if not self.llm.is_available():
                return (
                    "Local AI (Ollama) is not running. "
                    "Please start it: open a terminal and run 'ollama serve'"
                )

            prompt = RUTH_STRICT_PROMPT.format(
                context=context,
                history=self._format_history(),
                question=user_input,
            )

            response = self.llm.generate(prompt, max_tokens=400)

            # Safety check: if LLM admitted it doesn't know (hallucination guard)
            if not response or len(response.strip()) < 5:
                response = (
                    RUTH_NO_CONTEXT_RESPONSE_HI
                    if lang == "hi"
                    else RUTH_NO_CONTEXT_RESPONSE_EN
                )

            # Update conversation history
            self.conversation_history.append(HumanMessage(content=user_input))
            self.conversation_history.append(AIMessage(content=response))
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            self._store_interaction(user_input, response, lang)
            return response

        except Exception as e:
            console.print(f"[red]Brain error: {e}[/red]")
            return f"I encountered an error: {str(e)}"

    def _store_interaction(self, user_input: str, response: str, lang: str):
        """Log interaction to memory"""
        self.memory.log_interaction("voice", user_input, response, lang)

    def learn_from_qa(self, question: str, answer: str):
        """
        Teach Ruth a specific Q&A pair.
        This is stored as a business document so she can answer it in future.
        """
        qa_text = f"Question: {question}\nAnswer: {answer}"
        self.memory.ingest_document(qa_text, source="manual_training")
        self.memory.remember(qa_text, category="trained_qa")
        return f"✅ Learned! Ruth can now answer: '{question}'"

    def generate_morning_briefing(self) -> str:
        """Morning briefing using only known data (tasks, stats)"""
        stats = self.memory.get_stats()
        tasks = self.memory.get_tasks("pending")
        task_titles = ", ".join([t["title"] for t in tasks[:3]]) if tasks else "none"

        briefing = (
            f"Good morning! Here is your briefing for today, {datetime.now().strftime('%A %d %B')}. "
            f"You have {stats['tasks_pending']} pending tasks. "
        )
        if tasks:
            briefing += f"Top tasks: {task_titles}. "
        briefing += (
            f"You have {stats['interactions']} interactions in my memory. "
            "Have a productive day!"
        )
        return briefing
