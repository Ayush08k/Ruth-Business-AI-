"""
Ruth Website Monitor
- Uptime monitoring every 5 minutes
- SSL certificate expiry check
- Response time tracking
- Instant alert if site goes down
"""
import asyncio
import ssl
import socket
from datetime import datetime, timedelta
from urllib.parse import urlparse
from typing import Optional

import httpx
from rich.console import Console

from ruth.config import config

console = Console()


class WebsiteManager:
    """
    Monitors your website health and performance.
    Sends alerts via Ruth if anything goes wrong.
    """

    def __init__(self, url: str = None):
        self.url = url or config.WEBSITE_URL
        self._last_status = None
        self._consecutive_failures = 0

    def is_configured(self) -> bool:
        return bool(self.url and self.url != "https://your-website.com")

    async def health_check(self) -> dict:
        """Full health check of the website"""
        if not self.is_configured():
            return {"online": None, "error": "Website URL not configured"}

        result = {
            "url": self.url,
            "online": False,
            "status_code": None,
            "response_time_ms": None,
            "checked_at": datetime.now().isoformat(),
            "error": None,
        }

        try:
            start = datetime.now()
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.get(self.url)

            elapsed_ms = (datetime.now() - start).total_seconds() * 1000
            result["online"] = response.status_code < 500
            result["status_code"] = response.status_code
            result["response_time_ms"] = round(elapsed_ms, 1)
            self._consecutive_failures = 0

        except httpx.TimeoutException:
            result["error"] = "Request timed out (>10 seconds)"
            self._consecutive_failures += 1
        except httpx.ConnectError:
            result["error"] = "Cannot connect to server"
            self._consecutive_failures += 1
        except Exception as e:
            result["error"] = str(e)
            self._consecutive_failures += 1

        self._last_status = result
        return result

    def check_ssl_expiry(self) -> dict:
        """Check SSL certificate expiry"""
        if not self.is_configured():
            return {"error": "Not configured"}

        try:
            parsed = urlparse(self.url)
            hostname = parsed.hostname
            port = parsed.port or 443

            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    expiry_str = cert["notAfter"]
                    expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                    days_left = (expiry - datetime.now()).days

                    return {
                        "valid": True,
                        "expires": expiry.strftime("%d %B %Y"),
                        "days_left": days_left,
                        "warning": days_left < 30,
                        "critical": days_left < 7,
                    }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def get_status_text(self) -> str:
        """Get human-readable website status"""
        status = asyncio.run(self.health_check())

        if status.get("online") is None:
            return "Website URL not configured yet."

        if status["online"]:
            rt = status.get("response_time_ms", 0)
            speed = "fast" if rt < 500 else "slow" if rt > 2000 else "normal"
            text = (
                f"✅ Your website is ONLINE\n"
                f"   Response time: {rt}ms ({speed})\n"
                f"   Status code: {status['status_code']}"
            )
        else:
            text = (
                f"🚨 WARNING: Your website appears to be DOWN!\n"
                f"   Error: {status.get('error', 'Unknown')}\n"
                f"   Checked at: {status['checked_at']}"
            )

        # Add SSL info
        ssl_info = self.check_ssl_expiry()
        if ssl_info.get("days_left") is not None:
            if ssl_info["critical"]:
                text += f"\n🚨 SSL CRITICAL: Expires in {ssl_info['days_left']} days!"
            elif ssl_info["warning"]:
                text += f"\n⚠️ SSL Warning: Expires in {ssl_info['days_left']} days"

        return text

    async def run_monitor(self, alert_callback=None):
        """
        Continuous monitoring loop.
        Calls alert_callback(message) when site goes down or comes back.
        """
        if not self.is_configured():
            console.print("[yellow]⚠️  Website monitor: URL not configured[/yellow]")
            return

        console.print(f"[green]🌐 Monitoring: {self.url}[/green]")

        while True:
            status = await self.health_check()
            was_down = self._last_status and not self._last_status.get("online")

            if not status["online"]:
                console.print(f"[red]🚨 Site DOWN: {status.get('error')}[/red]")
                if alert_callback and self._consecutive_failures == 1:
                    alert_callback(
                        f"🚨 ALERT: Your website is DOWN!\n"
                        f"Error: {status.get('error')}\n"
                        f"Time: {datetime.now().strftime('%I:%M %p')}"
                    )
            elif was_down:
                # Site came back online
                console.print("[green]✅ Site is back online![/green]")
                if alert_callback:
                    alert_callback("✅ Good news! Your website is back online.")

            await asyncio.sleep(config.WEBSITE_CHECK_INTERVAL)

