"""
Ruth PC Automation & System Control Module
Full Windows capability:
 - Launch any app / program
 - Search Google / YouTube / Web
 - Type text, hotkeys, copy/paste
 - Click, double click, coordinates or UI window targets
 - Window management (maximize, minimize, close)
 - Media control (volume, play/pause)
"""
import os
import sys
import time
import subprocess
import webbrowser
import pyautogui
import pyperclip

# Safety settings for pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "browser": "msedge",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
    "task manager": "taskmgr.exe",
    "settings": "start ms-settings:",
    "spotify": "spotify",
    "code": "code",
    "vscode": "code",
    "paint": "mspaint.exe",
}

class SystemController:
    """Controls the local Windows PC based on voice/text commands"""

    @staticmethod
    def open_application(app_name: str) -> str:
        """Open any application or executable on the PC"""
        clean = app_name.lower().strip()
        cmd = APP_ALIASES.get(clean, clean)
        try:
            if clean in ["chrome", "google chrome"]:
                subprocess.Popen(["start", "chrome"], shell=True)
                return "Opening Chrome."
            elif clean in ["edge", "browser"]:
                subprocess.Popen(["start", "msedge"], shell=True)
                return "Opening browser."
            elif clean in ["whatsapp", "whatsapp desktop"]:
                subprocess.Popen(["start", "whatsapp:"], shell=True)
                return "Opening WhatsApp."
            elif clean in ["settings", "windows settings"]:
                subprocess.Popen(["start", "ms-settings:"], shell=True)
                return "Opening Windows Settings."
            elif cmd.startswith("start "):
                subprocess.Popen(cmd, shell=True)
                return f"Opening {app_name}."
            else:
                subprocess.Popen(f'start "" "{cmd}"', shell=True)
                return f"Opening {app_name}."
        except Exception:
            pass

        # Universal fallback: search Windows Start Menu and launch
        try:
            pyautogui.press("win")
            time.sleep(0.3)
            pyperclip.copy(app_name)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)
            pyautogui.press("enter")
            return f"Opening {app_name}."
        except Exception as ex:
            return f"Could not open {app_name}: {ex}"

    @staticmethod
    def close_current_window() -> str:
        """Close active window (Alt+F4)"""
        pyautogui.hotkey("alt", "f4")
        return "Closed active window."

    @staticmethod
    def search_web(query: str, platform: str = "google") -> str:
        """Search Google or YouTube directly in default browser"""
        query_clean = query.strip()
        if "youtube" in platform.lower():
            url = f"https://www.youtube.com/results?search_query={query_clean.replace(' ', '+')}"
        else:
            url = f"https://www.google.com/search?q={query_clean.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching for '{query_clean}' on {platform.title()}."

    @staticmethod
    def open_url(url: str) -> str:
        """Open any specific URL"""
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opening {url} in your browser."

    @staticmethod
    def type_text(text: str) -> str:
        """Type arbitrary text into whatever input is focused"""
        try:
            # Using clipboard allows typing special chars, emojis & Hindi
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return f"Typed: '{text}'"
        except Exception as e:
            return f"Failed to type: {e}"

    @staticmethod
    def press_key(key: str) -> str:
        """Press keyboard key or key combo (e.g. 'enter', 'tab', 'ctrl+c', 'win+d')"""
        k = key.lower().strip()
        if "+" in k:
            keys = [part.strip() for part in k.split("+")]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(k)
        return f"Pressed {key}."

    @staticmethod
    def click_mouse(x: int = None, y: int = None, clicks: int = 1, button: str = "left") -> str:
        """Click at current or specified coordinate, or double-click"""
        try:
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, clicks=clicks, button=button)
                return f"Clicked at coordinates ({x}, {y})."
            else:
                pyautogui.click(clicks=clicks, button=button)
                return f"Clicked {button} button."
        except Exception as e:
            return f"Click error: {e}"

    @staticmethod
    def double_click() -> str:
        """Double click at current position"""
        try:
            pyautogui.doubleClick()
            return "Double clicked."
        except Exception as e:
            return f"Double click error: {e}"

    @staticmethod
    def right_click() -> str:
        """Right click at current position"""
        try:
            pyautogui.rightClick()
            return "Right clicked."
        except Exception as e:
            return f"Right click error: {e}"

    @staticmethod
    def scroll(direction: str = "down", amount: int = 5) -> str:
        """Scroll active window"""
        try:
            clicks = -amount if direction == "down" else amount
            pyautogui.scroll(clicks * 100)
            return f"Scrolled {direction}."
        except Exception as e:
            return f"Scroll error: {e}"

    @staticmethod
    def take_screenshot(filename: str = "ruth_screen.png") -> str:
        """Take screenshot and save to disk"""
        save_path = os.path.join(os.getcwd(), filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return f"Screenshot saved to {save_path}"

    @staticmethod
    def control_media(action: str) -> str:
        """Control system volume and media playback"""
        act = action.lower().strip()
        if "up" in act:
            for _ in range(5): pyautogui.press("volumeup")
            return "Volume increased."
        elif "down" in act:
            for _ in range(5): pyautogui.press("volumedown")
            return "Volume decreased."
        elif "mute" in act:
            pyautogui.press("volumemute")
            return "Volume muted."
        elif "play" in act or "pause" in act:
            pyautogui.press("playpause")
            return "Toggled play/pause."
        elif "next" in act:
            pyautogui.press("nexttrack")
            return "Next track."
        return "Unknown media command."

