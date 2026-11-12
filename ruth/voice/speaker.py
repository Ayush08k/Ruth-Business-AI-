"""
Ruth Voice Speaker
- Female voice output using Edge-TTS (free, no API key needed)
- English: Jenny Neural (warm female)
- Hindi: Swara Neural (female)
- Async audio generation + sync playback
"""
import asyncio
import os
import tempfile
import threading
from pathlib import Path

import edge_tts
from rich.console import Console

from ruth.config import config

console = Console()


class RuthSpeaker:
    """
    Ruth's voice output system.
    Uses Microsoft Edge TTS — high quality, completely free, female voices.
    """

    VOICES = {
        "en": "en-US-EmmaMultilingualNeural", # Warm, whispery, very gentle female voice
        "hi": "hi-IN-SwaraNeural",            # Soft Hindi female
        "en-in": "en-IN-NeerjaNeural",        # Gentle Indian-English
        "en-gb": "en-GB-SoniaNeural",         # Soft British English
    }

    # Ultra-soft, calm, gentle acoustic parameters
    RATE = "-7%"         # Slower, calm, unhurried pacing
    PITCH = "-5Hz"       # Deeper, warmer, softer pitch (removes high-frequency sharpness)
    VOLUME = "-15%"      # Quieter, intimate, conversational volume

    def __init__(self):
        self._temp_dir = Path(tempfile.mkdtemp())
        self._output_file = self._temp_dir / "ruth_speech.mp3"
        self._speaking = False
        self._init_pygame()
        console.print("[green]✅ Voice speaker ready (Edge-TTS Female)[/green]")

    def _init_pygame(self):
        """Initialize pygame mixer for audio playback"""
        try:
            import pygame
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self._pygame = pygame
            self._use_pygame = True
        except Exception as e:
            console.print(f"[yellow]pygame not available: {e}. Using system player.[/yellow]")
            self._use_pygame = False

    def speak(self, text: str, lang: str = "en"):
        """
        Convert text to speech and play it.
        Blocks until speech is complete.
        """
        if not text or not text.strip():
            return

        # Clean text for TTS (remove markdown, emojis, etc.)
        clean_text = self._clean_for_tts(text)
        voice = self.VOICES.get(lang, self.VOICES["en"])

        console.print(f"[dim magenta]🔊 Ruth ({lang}): {clean_text[:80]}{'...' if len(clean_text) > 80 else ''}[/dim magenta]")

        self._speaking = True
        try:
            # Generate audio
            asyncio.run(self._generate_audio(clean_text, voice))
            # Play audio
            self._play_audio()
        except Exception as e:
            console.print(f"[red]TTS error: {e}[/red]")
            # Fallback: print text
            console.print(f"[bold cyan]Ruth: {text}[/bold cyan]")
        finally:
            self._speaking = False

    def speak_async(self, text: str, lang: str = "en"):
        """Non-blocking speak — runs in background thread"""
        thread = threading.Thread(target=self.speak, args=(text, lang), daemon=True)
        thread.start()
        return thread

    async def _generate_audio(self, text: str, voice: str):
        """Generate MP3 audio using Edge TTS"""
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=self.RATE,
            pitch=self.PITCH,
            volume=self.VOLUME,
        )
        await communicate.save(str(self._output_file))

    def _play_audio(self):
        """Play the generated audio file"""
        if not self._output_file.exists():
            return

        if self._use_pygame:
            self._pygame.mixer.music.load(str(self._output_file))
            self._pygame.mixer.music.play()
            while self._pygame.mixer.music.get_busy():
                self._pygame.time.Clock().tick(10)
        else:
            # Fallback: system command
            os.system(f'start /wait "" "{self._output_file}"')

    def _clean_for_tts(self, text: str) -> str:
        """Remove markdown and special chars that sound bad in TTS"""
        import re
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)         # italic
        text = re.sub(r'`(.*?)`', r'\1', text)           # code
        text = re.sub(r'#+\s*', '', text)                # headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
        # Remove emoji (keep alphanumeric and punctuation)
        text = re.sub(r'[^\w\s\.,!?;:\-\'\"\(\)%]', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Limit length for TTS (split long responses)
        if len(text) > 500:
            text = text[:497] + "..."
        return text

    def is_speaking(self) -> bool:
        return self._speaking

    def stop(self):
        """Stop current speech"""
        if self._use_pygame and self._speaking:
            self._pygame.mixer.music.stop()
            self._speaking = False


class RuthVoice:
    """Combined voice interface (listener + speaker)"""

    def __init__(self):
        self.speaker = RuthSpeaker()

    def say(self, text: str, lang: str = "en"):
        """Speak text in the appropriate language"""
        self.speaker.speak(text, lang)

    def say_startup(self):
        """Ruth's startup announcement"""
        self.speaker.speak(
            "Hello! Ruth is online and ready. How can I help you today?",
            lang="en"
        )

