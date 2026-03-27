"""
Quick test for Qwen2.5-72B-Instruct via HuggingFace Inference API.
Run from the project root:  python test_kimi.py
"""
import os, requests
from dotenv import load_dotenv

load_dotenv(r"C:\Users\KAVISH\supplyshield_final\.env", override=False)

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
HF_MODEL = "Qwen/Qwen2.5-7B-Instruct:together"
HF_URL   = "https://router.huggingface.co/v1/chat/completions"

if not HF_TOKEN:
    print("ERROR: HUGGINGFACE_API_TOKEN not set in .env")
    exit(1)

print(f"Model   : {HF_MODEL}")
print(f"Token   : {HF_TOKEN[:8]}...")
print(f"Endpoint: {HF_URL}")
print("-" * 60)
print("Sending test prompt...")

resp = requests.post(
    HF_URL,
    headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
    json={
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": "You are a procurement risk analyst. Reply concisely."},
            {"role": "user",   "content": "In one sentence, what is the main supply chain risk of sourcing from Russia?"},
        ],
        "max_tokens": 80,
        "temperature": 0.3,
    },
    timeout=45,
)

print(f"HTTP status : {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    print(f"Response    : {text}")
    print("\nQwen2.5-72B is working correctly.")
elif resp.status_code == 401:
    print("ERROR 401 — HF token is invalid or expired.")
elif resp.status_code == 403:
    print("ERROR 403 — model access denied. May require HF Pro.")
elif resp.status_code == 503:
    print("ERROR 503 — model is loading (cold start). Wait ~20s and retry.")
elif resp.status_code == 429:
    print("ERROR 429 — rate limit hit. Wait a minute and retry.")
else:
    print(f"Unexpected response:\n{resp.text[:500]}")
