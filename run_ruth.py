"""
╔══════════════════════════════════════════════╗
║           RUTH — AI BUSINESS ASSISTANT        ║
║         Your Personal Jarvis, Online          ║
╚══════════════════════════════════════════════╝

Main entry point. Run this to start Ruth.
Usage:
    python run_ruth.py           → Voice mode (default)
    python run_ruth.py --text    → Text/keyboard mode
    python run_ruth.py --setup   → First-time setup
    python run_ruth.py --train   → Training mode (upload docs)
"""
import sys
import os
import threading
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ruth.config import config
from ruth.memory import RuthMemory
from ruth.agent import RuthAgent
from ruth.voice import RuthListener, TextInputMode, RuthSpeaker
from ruth.integrations import EmailManager, WebsiteManager
from ruth.reporting import ReportEngine
from ruth.tools import init_tools
from ruth.training import RuthTrainer

console = Console()


def print_banner():
    """Print Ruth's startup banner"""
    banner = Text()
    banner.append("⚡ RUTH", style="bold white")
    banner.append(" — AI Business Assistant\n", style="dim white")
    banner.append("Your personal Jarvis. Always learning. Always ready.", style="italic cyan")

    console.print(Panel(banner, border_style="cyan", padding=(1, 4)))


def setup_mode():
    """Interactive first-time setup"""
    console.print("\n[bold cyan]🛠️  RUTH SETUP WIZARD[/bold cyan]\n")

    # Create .env if doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        import shutil
        shutil.copy(".env.example", ".env")
        console.print("[green]✅ Created .env file[/green]")

    console.print("\n[yellow]Please fill in your .env file with:[/yellow]")
    console.print("  1. GEMINI_API_KEY    → https://aistudio.google.com/app/apikey (FREE)")
    console.print("  2. REPORT_EMAIL      → Your email address")
    console.print("  3. WEBSITE_URL       → Your website URL")
    console.print("  4. PICOVOICE_ACCESS_KEY → https://console.picovoice.ai (FREE tier)\n")

    console.print("[dim]Gmail setup (for email reading):[/dim]")
    console.print("  1. Go to: https://console.cloud.google.com")
    console.print("  2. Create project → Enable Gmail API")
    console.print("  3. Create OAuth2 credentials → Download as 'credentials.json'")
    console.print("  4. Place credentials.json in the ruth/ folder\n")

    console.print("[green]After filling .env, run: python run_ruth.py[/green]")


def training_mode(trainer):
    """Interactive training mode"""
    console.print("\n[bold cyan]🎓 RUTH TRAINING MODE[/bold cyan]")
    console.print("[dim]Teach Ruth about YOUR business — she will ONLY answer from this data[/dim]\n")

    while True:
        console.print("[bold]What do you want to teach Ruth?[/bold]")
        console.print("[1] Upload a document (PDF, Word, TXT)")
        console.print("[2] Add a Q&A pair (most reliable method)")
        console.print("[3] Load Q&A from JSON file")
        console.print("[4] Scrape your website automatically")
        console.print("[5] Add a contact (client, vendor, etc.)")
        console.print("[6] Add business information (hours, prices, etc.)")
        console.print("[7] View training stats")
        console.print("[8] Exit training\n")

        choice = input("Choice (1-8): ").strip()

        if choice == "1":
            path = input("File path: ").strip().strip('"')
            result = trainer.upload_document(path)
            console.print(f"[green]{result}[/green]")

        elif choice == "2":
            console.print("[dim]Example — Q: 'What is your return policy?' A: 'We offer 30-day returns.'[/dim]")
            q = input("Question: ").strip()
            a = input("Answer: ").strip()
            if q and a:
                result = trainer.add_qa_pair(q, a)
                console.print(f"[green]{result}[/green]")

        elif choice == "3":
            path = input("JSON file path: ").strip().strip('"')
            result = trainer.load_qa_from_json(path)
            console.print(f"[green]{result}[/green]")

        elif choice == "4":
            url = input(f"Website URL (Enter for {config.WEBSITE_URL}): ").strip() or config.WEBSITE_URL
            max_p = input("Max pages to scrape (default 20): ").strip()
            result = trainer.scrape_website(url, int(max_p) if max_p.isdigit() else 20)
            console.print(f"[green]{result}[/green]")

        elif choice == "5":
            name = input("Name: ").strip()
            email = input("Email (optional): ").strip()
            phone = input("Phone (optional): ").strip()
            rel = input("Relationship (e.g., client, vendor, staff): ").strip()
            notes = input("Notes (optional): ").strip()
            result = trainer.add_contact(name, email, phone, rel, notes)
            console.print(f"[green]{result}[/green]")

        elif choice == "6":
            topic = input("Topic (e.g., 'business hours', 'pricing', 'location'): ").strip()
            info = input("Information: ").strip()
            result = trainer.add_business_info(topic, info)
            console.print(f"[green]{result}[/green]")

        elif choice == "7":
            console.print(trainer.get_training_stats())

        elif choice == "8":
            console.print("[cyan]Training session ended. Ruth's knowledge has been saved![/cyan]")
            break


def main():
    """Main Ruth startup"""
    args = sys.argv[1:]

    # Setup mode
    if "--setup" in args:
        setup_mode()
        return

    print_banner()

    # Validate config
    missing = config.validate()
    if missing and "OLLAMA_NOT_RUNNING" in missing:
        console.print("\n[red]❌ Ollama is not running![/red]")
        console.print("[yellow]  → Open a new terminal and run: ollama serve[/yellow]")
        console.print("[yellow]  → Then run Ruth again[/yellow]")
        console.print("\n[dim]If Ollama is not installed: https://ollama.com/download[/dim]")
        return

    # ─── Initialize all systems ─────────────────────────────────────────

    console.print("\n[cyan]Initializing Ruth systems...[/cyan]\n")

    # 1. Memory (always first)
    memory = RuthMemory()

    # 2. Integrations
    email_manager = EmailManager()
    website_manager = WebsiteManager()

    # 3. Register tools with integrations
    init_tools(memory, email_manager, website_manager)

    # 4. Brain (LLM Agent)
    brain = RuthAgent(memory)

    # 5. Voice
    speaker = RuthSpeaker()

    # 6. Reports
    reports = ReportEngine(memory, email_manager, website_manager, speaker, brain)

    # 7. Trainer
    trainer = RuthTrainer(memory)

    # Training mode
    if "--train" in args:
        training_mode(trainer)
        return

    # ─── Start background services ───────────────────────────────────────

    # Website monitor (background thread)
    if website_manager.is_configured():
        def run_monitor():
            def alert(msg):
                speaker.speak(msg, lang="en")
                console.print(f"[red]{msg}[/red]")
            asyncio.run(website_manager.run_monitor(alert_callback=alert))

        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()

    # Scheduled reports
    reports.start_scheduler()

    # ─── Print status ────────────────────────────────────────────────────

    stats = memory.get_stats()
    console.print(f"\n[bold green]╔══════════════════════════════════╗[/bold green]")
    console.print(f"[bold green]║   RUTH — Online & Ready          ║[/bold green]")
    console.print(f"[bold green]║   Voice: Jenny (English)         ║[/bold green]")
    console.print(f"[bold green]║   Voice: Swara (Hindi)           ║[/bold green]")
    console.print(f"[bold green]║   Memories: {stats['episodes']:<23}║[/bold green]")
    console.print(f"[bold green]║   Email: {'Connected ✅' if email_manager.is_connected() else 'Not configured  ':<23}║[/bold green]")
    console.print(f"[bold green]║   Website: {'Monitoring ✅' if website_manager.is_configured() else 'Not configured':<22}║[/bold green]")
    console.print(f"[bold green]╚══════════════════════════════════╝[/bold green]\n")

    # ─── Startup announcement ─────────────────────────────────────────────

    speaker.speak(
        "Hello! Ruth is online and ready. "
        f"You have {stats['tasks_pending']} pending tasks. "
        "Say Hey Ruth to give me a command.",
        lang="en"
    )

    # ─── Main Loop ───────────────────────────────────────────────────────

    def handle_command(text: str, lang: str):
        """Handle a voice or text command"""
        console.print(f"\n[bold]You ({lang}): {text}[/bold]")
        response = brain.process(text, channel="voice", lang=lang)
        console.print(f"[bold cyan]Ruth: {response}[/bold cyan]")
        speaker.speak(response, lang=lang)

    if "--text" in args:
        # Text/keyboard mode
        text_input = TextInputMode()
        text_input.run_input_loop(handle_command)
    else:
        # Voice mode — listen for "Hey Ruth"
        try:
            listener = RuthListener()
            listener.run_wake_word_loop(handle_command)
        except Exception as e:
            console.print(f"[yellow]Voice mode error: {e}[/yellow]")
            console.print("[yellow]Falling back to text mode. Type your commands:[/yellow]")
            text_input = TextInputMode()
            text_input.run_input_loop(handle_command)


if __name__ == "__main__":
    main()

