"""
Setup Ruth's local AI model via Ollama.
Run this ONCE after Ollama is installed.

This downloads phi3:mini — a smart small model that fits in 4GB RAM.
Size: ~2.3GB download (one-time only)
"""
import subprocess
import sys
import requests
import time

print("=" * 55)
print("  RUTH — Local AI Model Setup")
print("=" * 55)

# 1. Check if Ollama is running
print("\n⏳ Checking Ollama...")
max_tries = 5
for i in range(max_tries):
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        print("✅ Ollama is running!")
        break
    except Exception:
        if i == 0:
            print("   Ollama not responding. Starting it...")
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW
                           if sys.platform == "win32" else 0)
        time.sleep(3)
else:
    print("❌ Could not connect to Ollama.")
    print("   Please open a terminal and run: ollama serve")
    print("   Then run this script again.")
    sys.exit(1)

# 2. Check existing models
resp = requests.get("http://localhost:11434/api/tags", timeout=5)
existing = [m["name"] for m in resp.json().get("models", [])]
print(f"\n📦 Models already on your PC: {existing or 'none'}")

# 3. Choose and pull model
print("\n🤖 Recommended models for 4GB RAM:")
print("   [1] phi3:mini    (~2.3GB) ← RECOMMENDED — smartest small model")
print("   [2] gemma2:2b    (~1.6GB) ← Google's tiny model, less RAM")
print("   [3] llama3.2:1b  (~1.3GB) ← fastest, smallest, least smart")
print()

choice = input("Choose model (1/2/3, default=1): ").strip() or "1"
model_map = {"1": "phi3:mini", "2": "gemma2:2b", "3": "llama3.2:1b"}
model = model_map.get(choice, "phi3:mini")

if any(model.split(":")[0] in m for m in existing):
    print(f"✅ Model '{model}' already downloaded!")
else:
    print(f"\n⬇️  Downloading {model} (this may take a few minutes)...")
    print("   (This is a ONE-TIME download — Ruth will start instantly next time)")
    result = subprocess.run(["ollama", "pull", model], capture_output=False)
    if result.returncode == 0:
        print(f"\n✅ Model '{model}' ready!")
    else:
        print(f"\n❌ Failed to download model. Try manually: ollama pull {model}")
        sys.exit(1)

# 4. Update .env with selected model
env_path = ".env"
try:
    env_content = open(env_path).read()
    env_content = "\n".join([
        f"OLLAMA_MODEL={model}" if line.startswith("OLLAMA_MODEL=") else line
        for line in env_content.splitlines()
    ])
    open(env_path, "w").write(env_content)
    print(f"✅ Updated .env: OLLAMA_MODEL={model}")
except Exception as e:
    print(f"⚠️  Could not update .env: {e} — manually set OLLAMA_MODEL={model}")

print("\n" + "=" * 55)
print("✅ AI Model Setup Complete!")
print(f"   Model: {model}")
print("\n📋 NEXT STEPS:")
print("  1. Train Ruth: python run_ruth.py --train")
print("     → Add your website content, Q&A pairs, documents")
print("  2. Run Ruth:   python run_ruth.py --text")
print("=" * 55)

