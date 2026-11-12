"""
Ruth Quick Setup Script
Run this once to install all dependencies.
"""
import subprocess
import sys
import os

def run(cmd, description):
    print(f"\n⏳ {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode == 0:
        print(f"✅ Done: {description}")
    else:
        print(f"⚠️  Warning: {description} had issues (may still work)")
    return result.returncode == 0

print("=" * 55)
print("  RUTH SETUP — Installing Dependencies")
print("=" * 55)

# Upgrade pip first
run(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")

# Install in groups (handle failures gracefully)
packages = [
    # Core AI
    ("google-generativeai langchain langchain-google-genai langgraph langchain-community",
     "Installing AI/LLM packages"),

    # Voice
    ("openai-whisper sounddevice numpy scipy",
     "Installing Speech-to-Text (Whisper)"),

    # TTS
    ("edge-tts pygame",
     "Installing Text-to-Speech"),

    # Memory
    ("chromadb sentence-transformers",
     "Installing vector memory (ChromaDB)"),

    # Email
    ("google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client",
     "Installing Gmail API"),

    # Utilities
    ("python-dotenv schedule langdetect rich pydantic httpx requests beautifulsoup4 aiofiles python-dateutil colorama",
     "Installing utilities"),

    # Wake word (optional)
    ("pvporcupine",
     "Installing wake word engine (optional)"),
]

failed = []
for pkg, desc in packages:
    success = run(f"{sys.executable} -m pip install {pkg}", desc)
    if not success:
        failed.append(desc)

print("\n" + "=" * 55)
if failed:
    print(f"⚠️  Some packages had issues: {', '.join(failed)}")
    print("   Ruth will still work, some features may be limited.")
else:
    print("✅ All dependencies installed successfully!")

print("\n📋 NEXT STEPS:")
print("  1. Run: python run_ruth.py --setup")
print("  2. Fill in your .env file (Gemini API key, email, website URL)")
print("  3. Run: python run_ruth.py --text    (test without mic first)")
print("  4. Run: python run_ruth.py           (full voice mode)")
print("=" * 55)

