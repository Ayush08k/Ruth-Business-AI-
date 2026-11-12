"""
Ruth Tool Definitions
All actions Ruth can take — email, website, tasks, reminders, etc.
"""
from datetime import datetime
from typing import Optional
from langchain.tools import tool
from ruth.tools.pc_control import SystemController

# ─── PC & Desktop Control Tools ──────────────────────────────────────────

@tool
def open_app(app_name: str) -> str:
    """Launch any application on the PC (e.g. Chrome, Notepad, Calculator, VS Code, Spotify)."""
    return SystemController.open_application(app_name)

@tool
def search_online(query: str, platform: str = "google") -> str:
    """Search Google or YouTube in browser for query."""
    return SystemController.search_web(query, platform)

@tool
def type_into_active_window(text: str) -> str:
    """Type text into whatever text field or window is currently active."""
    return SystemController.type_text(text)

@tool
def press_hotkey(hotkey: str) -> str:
    """Press keyboard key or shortcut like 'enter', 'esc', 'ctrl+c', 'ctrl+v', 'alt+f4'."""
    return SystemController.press_key(hotkey)

@tool
def click_screen(x: Optional[int] = None, y: Optional[int] = None) -> str:
    """Click mouse at current position or specified x, y coordinate."""
    return SystemController.click_mouse(x, y)

@tool
def volume_control(action: str) -> str:
    """Adjust volume: 'up', 'down', 'mute', 'play', 'pause'."""
    return SystemController.control_media(action)

@tool
def take_pc_screenshot() -> str:
    """Capture screenshot of the PC screen."""
    return SystemController.take_screenshot()


# ─── These are populated at runtime by the agent ──────────────────────────
_memory = None
_email_manager = None
_website_manager = None


def init_tools(memory, email_manager, website_manager):
    global _memory, _email_manager, _website_manager
    _memory = memory
    _email_manager = email_manager
    _website_manager = website_manager


# ─── Memory Tools ─────────────────────────────────────────────────────────

@tool
def remember_preference(key: str, value: str) -> str:
    """Store a user preference or instruction for future use."""
    if _memory:
        _memory.learn_preference(key, value)
    return f"Got it! I've remembered: {key} = {value}"


@tool
def recall_memory(query: str) -> str:
    """Search Ruth's memory for relevant past information."""
    if _memory:
        memories = _memory.recall(query, n=5)
        return "\n".join(memories) if memories else "No relevant memories found."
    return "Memory not available."


@tool
def add_task(title: str, description: str = "", priority: str = "normal", due_date: str = "") -> str:
    """Add a task to the task list."""
    if _memory:
        task_id = _memory.add_task(title, description, priority, due_date or None)
        return f"Task added: '{title}' (ID: {task_id[:8]})"
    return "Task manager not available."


@tool
def get_pending_tasks() -> str:
    """Get all pending tasks."""
    if _memory:
        tasks = _memory.get_tasks("pending")
        if not tasks:
            return "No pending tasks."
        lines = [f"📋 Pending Tasks ({len(tasks)}):"]
        for t in tasks:
            due = f" | Due: {t['due_date']}" if t.get("due_date") else ""
            lines.append(f"  [{t['priority'].upper()}] {t['title']}{due}")
        return "\n".join(lines)
    return "Task manager not available."


@tool
def add_contact(name: str, email: str = "", phone: str = "",
                relationship: str = "", notes: str = "") -> str:
    """Add or update a contact in Ruth's memory."""
    if _memory:
        _memory.add_contact(name, email or None, phone or None, relationship or None, notes or None)
        return f"Contact saved: {name}"
    return "Memory not available."


# ─── Email Tools ──────────────────────────────────────────────────────────

@tool
def check_emails() -> str:
    """Read and summarize unread emails."""
    if _email_manager:
        return _email_manager.get_summary()
    return "Email not configured yet."


@tool
def send_email_report() -> str:
    """Generate and send a full business report to the owner's email."""
    if _email_manager:
        return _email_manager.send_daily_report()
    return "Email not configured yet."


@tool
def draft_email_reply(to: str, subject: str, context: str) -> str:
    """Draft an email reply. Ruth will compose it based on context."""
    if _email_manager:
        return _email_manager.draft_reply(to, subject, context)
    return "Email not configured yet."


# ─── Website Tools ────────────────────────────────────────────────────────

@tool
def check_website_status() -> str:
    """Check if the website is online and get response time."""
    if _website_manager:
        import asyncio
        status = asyncio.run(_website_manager.health_check())
        if status.get("online"):
            return (f"✅ Website is ONLINE\n"
                    f"   Response time: {status.get('response_time_ms', 0):.0f}ms\n"
                    f"   Status: {status.get('status_code', 200)}")
        else:
            return f"🚨 Website is DOWN! Error: {status.get('error', 'Unknown')}"
    return "Website monitor not configured yet."


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %d %B %Y, %I:%M %p")


@tool
def get_weather(city: str = "your city") -> str:
    """Get weather information for a city."""
    # Simple free weather API - no key needed
    import httpx
    try:
        resp = httpx.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return resp.text.strip()
    except Exception:
        return "Weather service unavailable right now."


# ─── All tools exported ───────────────────────────────────────────────────

ALL_TOOLS = [
    open_app,
    search_online,
    type_into_active_window,
    press_hotkey,
    click_screen,
    volume_control,
    take_pc_screenshot,
    remember_preference,
    recall_memory,
    add_task,
    get_pending_tasks,
    add_contact,
    check_emails,
    send_email_report,
    draft_email_reply,
    check_website_status,
    get_current_time,
    get_weather,
]

