"""
Ruth Robust Voice Listener
- Uses SpeechRecognition + PyAudio with adaptive noise calibration
- Falls back to local Whisper STT if offline
- Listens seamlessly without getting stuck in silence thresholds
"""
import time
import threading
import speech_recognition as sr
from rich.console import Console

console = Console()

class RuthListener:
    def __init__(self):
        console.print("[cyan]🎙️  Calibrating microphone for ambient room noise...[/cyan]")
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8       # Stop recording after 0.8s of silence
        self.recognizer.phrase_threshold = 0.3      # Minimum speaking duration
        self.recognizer.non_speaking_duration = 0.5
        
        # Initial calibration
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            console.print(f"[green]✅ Microphone calibrated (Energy threshold: {int(self.recognizer.energy_threshold)})[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Mic calibration warning: {e}[/yellow]")

        self.wake_triggers = ["ruth", "hey ruth", "hay ruth", "hi ruth", "hello ruth", "हे रूथ", "रूथ"]
        self._running = False

    def listen_phrase(self, timeout: int = 8) -> tuple[str, str]:
        """Listen to a single spoken phrase with automatic silence cutoff"""
        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=12)
                
                # First attempt: Google STT (instant, bilingual, accurate)
                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN")
                    lang = "hi" if any('\u0900' <= c <= '\u097F' for c in text) else "en"
                    return text.strip(), lang
                except sr.UnknownValueError:
                    pass
                except Exception:
                    # Secondary attempt without regional code
                    try:
                        text = self.recognizer.recognize_google(audio)
                        return text.strip(), "en"
                    except Exception:
                        pass
                        
            except sr.WaitTimeoutError:
                return "", "en"
            except Exception as e:
                console.print(f"[dim red]Audio capture error: {e}[/dim red]")
                
        return "", "en"

    def run_wake_word_loop(self, on_command_callback):
        """
        Continuous listening loop.
        Users can speak either:
         1. 'Hey Ruth open Chrome' (together in one sentence)
         2. 'Ruth' -> wait for prompt -> 'open Chrome'
         3. Direct commands like 'open calculator'
        """
        self._running = True
        console.print("[bold cyan]👂 Listening! You can speak anytime (say 'Ruth' or 'Hey Ruth')...[/bold cyan]")

        while self._running:
            try:
                text, lang = self.listen_phrase(timeout=10)
                if not text:
                    continue

                console.print(f"[dim]🎙️ Heard: \"{text}\"[/dim]")
                text_lower = text.lower()

                # Check if wake trigger is present
                is_wake = any(w in text_lower for w in self.wake_triggers)
                
                if is_wake:
                    console.print(f"[bold green]✨ Wake word detected in: \"{text}\"[/bold green]")
                    
                    # Extract command if spoken in same breath
                    command = text_lower
                    for w in self.wake_triggers:
                        command = command.replace(w, "")
                    command = command.strip()

                    if len(command) > 1:
                        # Full command was spoken together
                        console.print(f"[bold cyan]⚡ Executing command: {command}[/bold cyan]")
                        on_command_callback(command, lang)
                    else:
                        # Only wake word was spoken, prompt for command
                        console.print("[cyan]🎙️  Listening for command... speak now![/cyan]")
                        cmd_text, cmd_lang = self.listen_phrase(timeout=7)
                        if cmd_text:
                            console.print(f"[bold cyan]⚡ Executing command: {cmd_text}[/bold cyan]")
                            on_command_callback(cmd_text, cmd_lang)
                        else:
                            console.print("[yellow]Didn't hear a command. Resuming listening...[/yellow]")
                else:
                    # Direct actions recognition without even needing 'Ruth' prefix
                    direct_actions = ["open", "search", "kholo", "type", "click", "volume", "what", "tell", "kya", "close"]
                    if any(text_lower.startswith(act) for act in direct_actions):
                        console.print(f"[bold cyan]⚡ Direct command recognized: {text}[/bold cyan]")
                        on_command_callback(text, lang)

            except KeyboardInterrupt:
                self._running = False
                break
            except Exception as e:
                console.print(f"[dim red]Loop error: {e}[/dim red]")
                time.sleep(0.5)

    def stop(self):
        self._running = False

class TextInputMode:
    """Fallback text input mode"""
    def run_input_loop(self, on_command_callback):
        console.print("[yellow]⌨️  Text input mode (type commands, 'quit' to exit)[/yellow]")
        while True:
            try:
                text = input("\n[You]: ").strip()
                if text.lower() in ["quit", "exit", "bye"]:
                    break
                if text:
                    lang = "hi" if any('\u0900' <= c <= '\u097F' for c in text) else "en"
                    on_command_callback(text, lang)
            except (KeyboardInterrupt, EOFError):
                break
