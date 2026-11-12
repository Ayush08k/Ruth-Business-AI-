"""
Ruth Training Module — Enhanced
================================
Train Ruth with YOUR data only.
  - Upload documents (PDF, Word, TXT, MD)
  - Add Q&A pairs directly
  - Add website content
  - Scrape your website automatically
  - Ruth will ONLY answer from this trained data
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

from ruth.memory import RuthMemory
from ruth.config import config

console = Console()


class RuthTrainer:
    """
    Train Ruth exclusively on YOUR business data.
    Every piece of data you add = what Ruth can answer.
    She will NOT answer from general knowledge — only from this.
    """

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".json"}

    def __init__(self, memory: RuthMemory):
        self.memory = memory
        self._training_log = Path(config.RUTH_DATA_DIR) / "training_log.json"
        self._log = self._load_log()

    def _load_log(self) -> list:
        if self._training_log.exists():
            return json.loads(self._training_log.read_text())
        return []

    def _save_log(self, entry: dict):
        self._log.append({**entry, "timestamp": datetime.now().isoformat()})
        self._training_log.write_text(json.dumps(self._log, indent=2))

    # ─── Document Upload ─────────────────────────────────────────────────

    def upload_document(self, file_path: str, source_name: str = None) -> str:
        """Upload a document for Ruth to learn from"""
        path = Path(file_path)
        if not path.exists():
            return f"❌ File not found: {file_path}"
        if path.suffix not in self.SUPPORTED_EXTENSIONS:
            return f"❌ Unsupported type: {path.suffix}. Use: {', '.join(self.SUPPORTED_EXTENSIONS)}"

        source = source_name or path.stem
        text = self._extract_text(path)

        if not text or len(text.strip()) < 10:
            return f"❌ Could not extract text from {path.name}"

        self.memory.ingest_document(text, source=source)
        self._save_log({"type": "document", "source": source, "size": len(text)})
        return f"✅ Ruth learned from '{path.name}' — {len(text)} characters ingested"

    def upload_folder(self, folder_path: str) -> str:
        """Upload all documents from a folder"""
        folder = Path(folder_path)
        if not folder.is_dir():
            return f"❌ Not a folder: {folder_path}"

        files = [f for f in folder.rglob("*") if f.suffix in self.SUPPORTED_EXTENSIONS]
        if not files:
            return f"❌ No supported files found in {folder_path}"

        results = []
        for file in track(files, description="Training Ruth..."):
            results.append(self.upload_document(str(file)))
        return "\n".join(results)

    # ─── Q&A Training ────────────────────────────────────────────────────

    def add_qa_pair(self, question: str, answer: str) -> str:
        """
        Directly teach Ruth a question and its answer.
        This is the most reliable way to train her.
        Example:
            question = "What are your business hours?"
            answer   = "We are open Monday to Saturday, 9 AM to 6 PM IST."
        """
        qa_text = (
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Keywords: {question}"
        )
        self.memory.ingest_document(qa_text, source="qa_training")
        self.memory.remember(qa_text, category="trained_qa")
        self._save_log({"type": "qa", "question": question[:100]})
        return f"✅ Trained: '{question[:60]}...'" if len(question) > 60 else f"✅ Trained: '{question}'"

    def add_qa_batch(self, qa_pairs: list[dict]) -> str:
        """
        Add multiple Q&A pairs at once.
        Input: [{"q": "question", "a": "answer"}, ...]
        """
        results = []
        for pair in track(qa_pairs, description="Training Q&A pairs..."):
            result = self.add_qa_pair(pair.get("q", ""), pair.get("a", ""))
            results.append(result)
        return f"✅ Added {len(results)} Q&A pairs to Ruth's knowledge"

    def load_qa_from_json(self, file_path: str) -> str:
        """
        Load Q&A pairs from a JSON file.
        Format: [{"q": "...", "a": "..."}, ...]
        """
        path = Path(file_path)
        if not path.exists():
            return f"❌ File not found: {file_path}"
        try:
            pairs = json.loads(path.read_text(encoding="utf-8"))
            return self.add_qa_batch(pairs)
        except Exception as e:
            return f"❌ Error reading JSON: {e}"

    # ─── Website Scraper ─────────────────────────────────────────────────

    def scrape_website(self, url: str = None, max_pages: int = 20) -> str:
        """
        Automatically scrape YOUR website and train Ruth on its content.
        Ruth will then be able to answer questions about your site.
        """
        url = url or config.WEBSITE_URL
        if not url or url == "https://your-website.com":
            return "❌ Website URL not configured. Set WEBSITE_URL in .env"

        console.print(f"[cyan]🌐 Scraping website: {url}[/cyan]")
        return asyncio.run(self._scrape_async(url, max_pages))

    async def _scrape_async(self, base_url: str, max_pages: int) -> str:
        visited = set()
        to_visit = [base_url]
        scraped_pages = 0
        total_chars = 0

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            while to_visit and scraped_pages < max_pages:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Extract meaningful text
                    for tag in soup(["script", "style", "nav", "footer", "iframe"]):
                        tag.decompose()

                    text = soup.get_text(separator="\n", strip=True)
                    text = "\n".join(line for line in text.splitlines() if len(line.strip()) > 20)

                    if len(text) > 100:
                        page_name = url.replace(base_url, "").strip("/") or "homepage"
                        self.memory.ingest_document(text, source=f"website_{page_name}")
                        total_chars += len(text)
                        scraped_pages += 1
                        console.print(f"  [green]✓[/green] {url} ({len(text)} chars)")

                    # Find more pages on the same domain
                    from urllib.parse import urljoin, urlparse
                    for link in soup.find_all("a", href=True):
                        href = urljoin(base_url, link["href"])
                        if urlparse(href).netloc == urlparse(base_url).netloc:
                            if href not in visited and href not in to_visit:
                                to_visit.append(href)

                except Exception as e:
                    console.print(f"  [dim red]✗ {url}: {e}[/dim red]")

        self._save_log({
            "type": "website_scrape",
            "url": base_url,
            "pages": scraped_pages,
            "chars": total_chars,
        })
        return (
            f"✅ Scraped {scraped_pages} pages from {base_url}\n"
            f"   {total_chars:,} characters added to Ruth's knowledge base\n"
            f"   Ruth can now answer questions about your website!"
        )

    # ─── Business Facts ───────────────────────────────────────────────────

    def add_business_info(self, topic: str, info: str) -> str:
        """Add a specific business fact or policy"""
        text = f"Business Information — {topic}:\n{info}"
        self.memory.ingest_document(text, source=f"business_{topic.replace(' ', '_').lower()}")
        self._save_log({"type": "business_info", "topic": topic})
        return f"✅ Learned about: {topic}"

    def add_contact(self, name: str, email: str = "", phone: str = "",
                    relationship: str = "", notes: str = "") -> str:
        self.memory.add_contact(name, email, phone, relationship, notes)
        # Also add to document store for question answering
        contact_text = (
            f"Contact: {name}\n"
            f"Email: {email}\nPhone: {phone}\n"
            f"Relationship: {relationship}\nNotes: {notes}"
        )
        self.memory.ingest_document(contact_text, source=f"contact_{name.replace(' ', '_')}")
        return f"✅ Contact saved: {name}"

    # ─── Training Stats ───────────────────────────────────────────────────

    def get_training_stats(self) -> str:
        """Show what Ruth knows so far"""
        stats = self.memory.get_stats()
        log_types = {}
        for entry in self._log:
            t = entry.get("type", "unknown")
            log_types[t] = log_types.get(t, 0) + 1

        lines = [
            "📊 Ruth's Knowledge Base Stats:",
            f"  📄 Document chunks: {stats['episodes']}",
            f"  👤 Contacts: {stats['contacts']}",
            f"  💬 Interactions: {stats['interactions']}",
            f"  ⚙️  Preferences: {stats['preferences']}",
            "",
            "📋 Training History:",
        ]
        for t, count in log_types.items():
            lines.append(f"  • {t}: {count}")

        if not log_types:
            lines.append("  No training done yet — run training mode to teach Ruth!")

        return "\n".join(lines)

    # ─── Text Extraction ─────────────────────────────────────────────────

    def _extract_text(self, path: Path) -> str:
        try:
            if path.suffix in {".txt", ".md"}:
                return path.read_text(encoding="utf-8", errors="ignore")
            elif path.suffix == ".pdf":
                try:
                    import PyPDF2
                    text = ""
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text += (page.extract_text() or "") + "\n"
                    return text
                except ImportError:
                    return ""
            elif path.suffix == ".docx":
                try:
                    import docx
                    doc = docx.Document(str(path))
                    return "\n".join([p.text for p in doc.paragraphs])
                except ImportError:
                    return ""
            elif path.suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    # Assume Q&A format
                    return "\n".join([
                        f"Q: {item.get('q','')}\nA: {item.get('a','')}"
                        for item in data if isinstance(item, dict)
                    ])
                return json.dumps(data, indent=2)
        except Exception as e:
            console.print(f"[red]Error reading {path}: {e}[/red]")
        return ""
