"""
Pull phi3:mini model directly via Ollama API (server already running)
"""
import requests
import json
import sys
import time

OLLAMA_URL = "http://localhost:11434"

print("=" * 55)
print("  Downloading phi3:mini for Ruth")
print("  Size: ~2.3GB | One-time download")
print("=" * 55)

# Check server
try:
    r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"\n✅ Ollama server running")
    if models:
        print(f"   Existing models: {', '.join(models)}")
    
    # Check if phi3 already downloaded
    if any("phi3" in m for m in models):
        print("\n✅ phi3:mini already downloaded! Ruth is ready.")
        print("\nNext step: cd d:\\Ruth && python run_ruth.py --train")
        sys.exit(0)

except Exception as e:
    print(f"\n❌ Ollama server not reachable: {e}")
    print("   Please start Ollama first (it should be in your system tray)")
    sys.exit(1)

# Pull model via streaming API
print(f"\n⬇️  Downloading phi3:mini...")
print("   (This runs in background — check Ollama system tray for progress)")
print("   Press Ctrl+C to stop watching — download continues in background\n")

try:
    with requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"name": "phi3:mini", "stream": True},
        stream=True,
        timeout=3600,
    ) as resp:
        last_pct = -1
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                status = data.get("status", "")
                total = data.get("total", 0)
                completed = data.get("completed", 0)
                
                if total and completed:
                    pct = int((completed / total) * 100)
                    if pct != last_pct and pct % 5 == 0:
                        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                        gb_done = completed / 1024**3
                        gb_total = total / 1024**3
                        print(f"  [{bar}] {pct}% — {gb_done:.1f}/{gb_total:.1f} GB", end="\r")
                        last_pct = pct
                elif status and status != "pulling manifest":
                    if "success" in status.lower():
                        print(f"\n\n✅ {status}")
                    elif last_pct < 0:
                        print(f"  Status: {status}")
            except Exception:
                pass

    print("\n\n" + "=" * 55)
    print("✅ phi3:mini downloaded! Ruth's brain is ready.")
    print("\n📋 Next steps:")
    print("  1. Train Ruth: cd d:\\Ruth && python run_ruth.py --train")
    print("     → Choose option 4 to scrape your website")
    print("  2. Start Ruth: python run_ruth.py --text")
    print("=" * 55)

except KeyboardInterrupt:
    print("\n\n⚠️  Stopped watching. Download may still be running in background.")
    print("Run this script again to check progress.")
except Exception as e:
    print(f"\n❌ Error: {e}")

