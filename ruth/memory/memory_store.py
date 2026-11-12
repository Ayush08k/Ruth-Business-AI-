"""
Ruth Memory System
- ChromaDB for semantic/vector memory (long-term recall)
- SQLite for structured data (preferences, contacts, tasks)
All stored locally on disk.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer
from rich.console import Console

from ruth.config import config

console = Console()


class RuthMemory:
    """
    Persistent, local memory for Ruth.
    Remembers everything — conversations, preferences, contacts, facts.
    No data leaves your machine.
    """

    def __init__(self):
        # Vector memory (semantic search)
        self.chroma = chromadb.PersistentClient(path=str(config.MEMORY_DIR))
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # Collections
        self.episodes = self.chroma.get_or_create_collection("episodes")
        self.contacts = self.chroma.get_or_create_collection("contacts")
        self.website_facts = self.chroma.get_or_create_collection("website")
        self.business_docs = self.chroma.get_or_create_collection("business_docs")

        # Structured memory (SQLite)
        self._init_sqlite()

        console.print("[green]✅ Memory system loaded[/green]")

    def _init_sqlite(self):
        """Initialize local SQLite database"""
        self.db = sqlite3.connect(str(config.DB_PATH))
        self.db.row_factory = sqlite3.Row
        cur = self.db.cursor()

        cur.executescript("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                relationship TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                channel TEXT,
                user_input TEXT,
                ruth_response TEXT,
                lang TEXT DEFAULT 'en',
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id TEXT PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                classification TEXT,
                handled_at TEXT,
                action_taken TEXT
            );
        """)
        self.db.commit()

    # ─── Episodic Memory (conversations, events) ───────────────────────────

    def remember(self, text: str, category: str = "general", metadata: dict = None):
        """Store any interaction or fact in vector memory"""
        metadata = metadata or {}
        vec = self.encoder.encode(text).tolist()
        self.episodes.add(
            embeddings=[vec],
            documents=[text],
            ids=[str(uuid.uuid4())],
            metadatas=[{"category": category, "timestamp": datetime.now().isoformat(), **metadata}]
        )

    def recall(self, query: str, n: int = 5, category: str = None) -> list[str]:
        """Retrieve semantically relevant memories"""
        vec = self.encoder.encode(query).tolist()
        where = {"category": category} if category else None
        try:
            results = self.episodes.query(
                query_embeddings=[vec],
                n_results=min(n, self.episodes.count() or 1),
                where=where
            )
            return results["documents"][0] if results["documents"] else []
        except Exception:
            return []

    # ─── Preference Learning ─────────────────────────────────────────────

    def learn_preference(self, key: str, value: str):
        """Learn a preference from correction or instruction"""
        self.db.execute(
            "INSERT OR REPLACE INTO preferences VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
        self.db.commit()
        self.remember(f"Preference: {key} = {value}", category="preference")

    def get_preference(self, key: str) -> Optional[str]:
        row = self.db.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_all_preferences(self) -> dict:
        rows = self.db.execute("SELECT key, value FROM preferences").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ─── Contact Management ───────────────────────────────────────────────

    def add_contact(self, name: str, email: str = None, phone: str = None,
                    relationship: str = None, notes: str = None):
        contact_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self.db.execute(
            "INSERT OR REPLACE INTO contacts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (contact_id, name, email, phone, relationship, notes, now, now)
        )
        self.db.commit()
        # Also add to vector memory for natural language lookup
        desc = f"Contact: {name}. Email: {email}. Phone: {phone}. Relationship: {relationship}. Notes: {notes}"
        vec = self.encoder.encode(desc).tolist()
        self.contacts.add(
            embeddings=[vec], documents=[desc],
            ids=[contact_id], metadatas=[{"name": name, "email": email or ""}]
        )
        return contact_id

    def find_contact(self, query: str) -> list[dict]:
        """Find contact by name, email, or description"""
        vec = self.encoder.encode(query).tolist()
        try:
            results = self.contacts.query(query_embeddings=[vec], n_results=3)
            return results["metadatas"][0] if results["metadatas"] else []
        except Exception:
            return []

    # ─── Task Management ─────────────────────────────────────────────────

    def add_task(self, title: str, description: str = None,
                 priority: str = "normal", due_date: str = None) -> str:
        task_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, 'pending', ?, ?, ?, NULL)",
            (task_id, title, description, priority, due_date, datetime.now().isoformat())
        )
        self.db.commit()
        return task_id

    def get_tasks(self, status: str = "pending") -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, due_date ASC",
            (status,)
        ).fetchall()
        return [dict(r) for r in rows]

    def complete_task(self, task_id: str):
        self.db.execute(
            "UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
            (datetime.now().isoformat(), task_id)
        )
        self.db.commit()

    # ─── Interaction Logging ──────────────────────────────────────────────

    def log_interaction(self, channel: str, user_input: str,
                        ruth_response: str, lang: str = "en"):
        self.db.execute(
            "INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), channel, user_input,
             ruth_response, lang, datetime.now().isoformat())
        )
        self.db.commit()
        # Also remember in vector store
        self.remember(
            f"User said: {user_input} | Ruth replied: {ruth_response}",
            category="conversation",
            metadata={"channel": channel, "lang": lang}
        )

    def get_recent_interactions(self, n: int = 10) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── Business Document Ingestion (RAG) ───────────────────────────────

    def ingest_document(self, text: str, source: str = "unknown", chunk_size: int = 500):
        """Add a business document to Ruth's knowledge base"""
        # Split into chunks
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

        for i, chunk in enumerate(chunks):
            vec = self.encoder.encode(chunk).tolist()
            self.business_docs.add(
                embeddings=[vec],
                documents=[chunk],
                ids=[f"{source}_{i}_{uuid.uuid4().hex[:8]}"],
                metadatas=[{"source": source, "chunk": i}]
            )
        console.print(f"[green]📚 Ingested {len(chunks)} chunks from '{source}'[/green]")

    def recall_from_docs(self, query: str, n: int = 3) -> list[str]:
        """Search business documents for relevant context"""
        vec = self.encoder.encode(query).tolist()
        try:
            results = self.business_docs.query(query_embeddings=[vec], n_results=n)
            return results["documents"][0] if results["documents"] else []
        except Exception:
            return []

    def get_stats(self) -> dict:
        return {
            "episodes": self.episodes.count(),
            "contacts": self.db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
            "tasks_pending": self.db.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='pending'"
            ).fetchone()[0],
            "interactions": self.db.execute(
                "SELECT COUNT(*) FROM interactions"
            ).fetchone()[0],
            "preferences": self.db.execute(
                "SELECT COUNT(*) FROM preferences"
            ).fetchone()[0],
        }

