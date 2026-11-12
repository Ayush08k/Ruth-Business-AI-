"""
Ruth Voice Listener
- Wake word detection: "Hey Ruth"
- Speech-to-Text: Whisper (local, bilingual English + Hindi)
- Fallback: simple keyboard input mode
"""
import os
import io
import time
import threading
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import whisper
from rich.console import Console

console = Console()


class RuthListener:
    """
    Always-on voice listener for Ruth.
    Detects wake word 'Hey Ruth', then captures and transcribes command.
    Supports English and Hindi automatically.
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "float32"
    SILENCE_THRESHOLD = 0.01
    SILENCE_DURATION = 1.5   # seconds of silence to stop recording
    MAX_RECORD_SECONDS = 30

    def __init__(self):
        console.print("[yellow]⏳ Loading Whisper model (first time may take a moment)...[/yellow]")
        self.whisper_model = whisper.load_model("base")  # ~150MB, works with 4GB RAM
        self.wake_word = "hey ruth"
        self._running = False
        self._picovoice_available = False
        self._init_picovoice()
        console.print("[green]✅ Voice listener ready[/green]")

    def _init_picovoice(self):
        """Try to init Picovoice wake word engine (optional)"""
        try:
            import pvporcupine
            from ruth.config import config
            if config.PICOVOICE_ACCESS_KEY:
                self.porcupine = pvporcupine.create(
                    access_key=config.PICOVOICE_ACCESS_KEY,
                    keywords=["hey google"],  # closest built-in; use custom for 'hey ruth'
                )
                self._picovoice_available = True
                console.print("[green]✅ Wake word engine: Picovoice[/green]")
        except Exception as e:
            console.print(f"[yellow]ℹ️  Picovoice not available, using Whisper wake word detection[/yellow]")

    def listen_for_command(self, timeout: int = 10) -> tuple[str, str]:
        """
        Record audio until silence, then transcribe.
        Returns (transcribed_text, detected_language)
        """
        console.print("[cyan]🎙️  Listening...[/cyan]")
        audio_data = []
        silence_start = None

        def callback(indata, frames, time_info, status):
            volume = np.abs(indata).mean()
            audio_data.append(indata.copy())
            nonlocal silence_start
            if volume < self.SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
            else:
                silence_start = None

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=callback,
        ):
            start = time.time()
            while True:
                time.sleep(0.1)
                elapsed = time.time() - start
                if elapsed > timeout:
                    break
                if (silence_start and
                        time.time() - silence_start > self.SILENCE_DURATION and
                        len(audio_data) > 10):
                    break

        if not audio_data:
            return "", "en"

        audio_array = np.concatenate(audio_data, axis=0).flatten()
        return self._transcribe(audio_array)

    def _transcribe(self, audio_array: np.ndarray) -> tuple[str, str]:
        """Transcribe audio using Whisper (auto-detects language)"""
        try:
            result = self.whisper_model.transcribe(
                audio_array,
                language=None,          # auto-detect Hindi or English
                task="transcribe",
                fp16=False,             # safer on CPU
            )
            text = result.get("text", "").strip()
            lang = result.get("language", "en")
            console.print(f"[dim]Heard ({lang}): {text}[/dim]")
            return text, lang
        except Exception as e:
            console.print(f"[red]Transcription error: {e}[/red]")
            return "", "en"

    def _whisper_wake_word_check(self, audio_array: np.ndarray) -> tuple[bool, str, str]:
        """Use Whisper to detect wake word in audio clip and return (detected, text, lang)"""
        text, lang = self._transcribe(audio_array)
        cleaned = text.lower().strip()
        # Check variations of 'hey ruth' / 'ruth'
        wake_triggers = ["hey ruth", "hay ruth", "hi ruth", "hello ruth", "ruth", "रूथ", "हे रूथ"]
        detected = any(trigger in cleaned for trigger in wake_triggers)
        return detected, text, lang

    def run_wake_word_loop(self, on_command_callback):
        """
        Main loop: listen for 'Hey Ruth', then capture command.
        Calls on_command_callback(text, lang) when command is detected.
        """
        self._running = True
        console.print(f"[bold cyan]👂 Listening for wake word: '{self.wake_word}' (or just 'Ruth')...[/bold cyan]")

        CHUNK_DURATION = 3  # seconds per wake word check
        CHUNK_SAMPLES = self.SAMPLE_RATE * CHUNK_DURATION

        while self._running:
            try:
                # Record a short chunk to check for wake word
                audio_chunk = sd.rec(
                    CHUNK_SAMPLES,
                    samplerate=self.SAMPLE_RATE,
                    channels=self.CHANNELS,
                    dtype=self.DTYPE
                )
                sd.wait()
                audio_flat = audio_chunk.flatten()

                # Check if wake word was spoken
                detected, heard_text, lang = self._whisper_wake_word_check(audio_flat)
                if detected:
                    console.print(f"[bold green]🎙️  Wake word heard in: \"{heard_text}\"![/bold green]")

                    # Play activation sound
                    self._play_activation_beep()

                    # Check if user already spoke the whole command together in that chunk!
                    # e.g. "Hey Ruth what is my business website"
                    words = heard_text.lower()
                    for trig in ["hey ruth", "hay ruth", "hi ruth", "hello ruth", "ruth", "रूथ", "हे रूथ"]:
                        words = words.replace(trig, "")
                    leftover_command = words.strip()

                    if len(leftover_command.split()) >= 2:
                        console.print(f"[cyan]⚡ Direct command captured: {leftover_command}[/cyan]")
                        on_command_callback(leftover_command, lang)
                        continue

                    # Otherwise, record the subsequent command
                    console.print("[cyan]🎙️  Listening for command... speak now![/cyan]")
                    command_text, cmd_lang = self.listen_for_command(timeout=8)

                    if command_text and len(command_text.strip()) > 1:
                        clean = command_text
                        for trig in ["hey ruth", "hay ruth", "hi ruth", "hello ruth", "ruth"]:
                            clean = clean.lower().replace(trig, "")
                        clean = clean.strip()
                        if not clean:
                            clean = command_text
                        on_command_callback(clean, cmd_lang)
                    else:
                        console.print("[dim yellow]No command heard after wake word. Returning to stand-by.[/dim yellow]")

            except KeyboardInterrupt:
                self._running = False
            except Exception as e:
                console.print(f"[red]Listener error: {e}[/red]")
                time.sleep(1)

    def _play_activation_beep(self):
        """Play a short beep to signal Ruth is active"""
        try:
            duration = 0.15
            freq = 880
            t = np.linspace(0, duration, int(self.SAMPLE_RATE * duration))
            beep = (np.sin(2 * np.pi * freq * t) * 0.3).astype(np.float32)
            sd.play(beep, self.SAMPLE_RATE)
            sd.wait()
        except Exception:
            pass

    def stop(self):
        self._running = False


class TextInputMode:
    """
    Fallback text input mode — when microphone is not available.
    Lets you type commands to Ruth.
    """

    def run_input_loop(self, on_command_callback):
        """Simple text loop for testing without mic"""
        console.print("[yellow]⌨️  Text input mode (type commands, 'quit' to exit)[/yellow]")
        while True:
            try:
                text = input("\n[You]: ").strip()
                if text.lower() in ["quit", "exit", "bye"]:
                    break
                if text:
                    # Simple language detection
                    lang = "hi" if self._is_hindi(text) else "en"
                    on_command_callback(text, lang)
            except (KeyboardInterrupt, EOFError):
                break

    def _is_hindi(self, text: str) -> bool:
        """Check if text contains Hindi/Devanagari characters"""
        return any('\u0900' <= c <= '\u097F' for c in text)

