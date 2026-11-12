"""
Ruth Report Engine
- Morning briefing (voice + email)
- Email check summaries
- Weekly business summary
- On-demand reports
"""
import asyncio
import schedule
import threading
import time
from datetime import datetime

from rich.console import Console

from ruth.config import config

console = Console()


class ReportEngine:
    """
    Scheduled and on-demand reports for Ruth.
    Delivers via voice and/or email.
    """

    def __init__(self, memory, email_manager, website_manager, speaker, brain):
        self.memory = memory
        self.email = email_manager
        self.website = website_manager
        self.speaker = speaker
        self.brain = brain
        self._scheduler_thread = None

    def compile_report_data(self) -> dict:
        """Compile all data needed for a report"""
        # Tasks
        tasks = self.memory.get_tasks("pending")

        # Email summary
        emails = []
        email_count = 0
        if self.email.is_connected():
            emails = self.email.get_unread_emails(20)
            email_count = len(emails)

        # Website status
        site_status = asyncio.run(self.website.health_check())
        site_up = site_status.get("online", None)

        # Memory stats
        stats = self.memory.get_stats()

        return {
            "date": datetime.now().strftime("%A, %d %B %Y"),
            "time": datetime.now().strftime("%I:%M %p"),
            "email_count": email_count,
            "urgent_count": 0,  # Will be classified by brain
            "tasks_pending": len(tasks),
            "tasks": tasks[:5],
            "site_up": site_up,
            "response_time": f"{site_status.get('response_time_ms', 0):.0f}ms",
            "email_highlights": emails[:5],
            "insights": self._generate_simple_insights(email_count, len(tasks), site_up),
        }

    def _generate_simple_insights(self, emails: int, tasks: int, site_up) -> str:
        insights = []
        if emails > 10:
            insights.append(f"You have {emails} unread emails — might need dedicated email time today.")
        if tasks > 5:
            insights.append(f"{tasks} tasks pending — consider prioritizing today.")
        if site_up is False:
            insights.append("⚠️ Website issue detected — urgent attention needed!")
        if not insights:
            insights.append("Everything looks good today! Stay focused and productive.")
        return " ".join(insights)

    def morning_briefing(self):
        """7 AM — Spoken morning briefing + email report"""
        console.print("[bold cyan]📢 Generating morning briefing...[/bold cyan]")
        data = self.compile_report_data()

        # Voice briefing
        voice_text = (
            f"Good morning! Today is {data['date']}. "
            f"You have {data['email_count']} unread emails. "
        )
        if data['site_up'] is True:
            voice_text += "Your website is online. "
        elif data['site_up'] is False:
            voice_text += "Warning! Your website appears to be down. "

        voice_text += (
            f"You have {data['tasks_pending']} pending tasks. "
            f"{data['insights']} Have a great day!"
        )

        self.speaker.speak(voice_text, lang="en")

        # Email the full report
        if self.email.is_connected():
            self.email.send_daily_report(data)

    def email_check(self):
        """Every 2 hours — Email check notification"""
        if not self.email.is_connected():
            return
        emails = self.email.get_unread_emails(5)
        if emails:
            count = len(emails)
            console.print(f"[dim]📧 {count} new email(s) checked[/dim]")

    def start_scheduler(self):
        """Start background scheduling thread"""
        briefing_time = config.MORNING_BRIEFING_TIME

        schedule.every().day.at(briefing_time).do(self.morning_briefing)
        schedule.every(config.EMAIL_CHECK_INTERVAL_HOURS).hours.do(self.email_check)

        def run():
            console.print(f"[dim]⏰ Scheduler running (briefing at {briefing_time})[/dim]")
            while True:
                schedule.run_pending()
                time.sleep(60)

        self._scheduler_thread = threading.Thread(target=run, daemon=True)
        self._scheduler_thread.start()

