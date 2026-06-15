"""Sinh >=10 traces lên Langfuse và xác minh.

Yêu cầu: app đang chạy (uvicorn ... --port 8013) và .env có
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST.

    python scripts/generate_traces.py            # gửi 15 request rồi đếm traces
    python scripts/generate_traces.py 20         # gửi 20 request
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API = f"http://127.0.0.1:{os.getenv('LAB_PORT', '8013')}"
HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
PK = os.getenv("LANGFUSE_PUBLIC_KEY", "")
SK = os.getenv("LANGFUSE_SECRET_KEY", "")


def send(n: int) -> int:
    qs = [json.loads(l) for l in (ROOT / "data/sample_queries.jsonl").read_text().splitlines() if l.strip()]
    sent = 0
    with httpx.Client(timeout=30) as c:
        i = 0
        while sent < n:
            p = dict(qs[i % len(qs)])
            p["session_id"] = f"trace-demo-{sent:02d}"
            r = c.post(f"{API}/chat", json=p)
            r.raise_for_status()
            sent += 1
            i += 1
    return sent


def count_traces() -> int | None:
    if not (PK and SK):
        return None
    try:
        r = httpx.get(
            f"{HOST}/api/public/traces",
            params={"limit": 100},
            auth=(PK, SK),
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("meta", {}).get("totalItems") or len(data.get("data", []))
    except Exception as exc:  # noqa: BLE001
        print(f"  (không đếm được qua API: {exc})")
        return None


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    print(f"Gửi {n} request tới {API}/chat ...")
    sent = send(n)
    print(f"  đã gửi {sent} request.")
    print("Chờ Langfuse flush (8s) ...")
    time.sleep(8)
    total = count_traces()
    if total is None:
        print("Không có key để xác minh — mở dashboard Langfuse để kiểm tra thủ công.")
    else:
        ok = "✓" if total >= 10 else "✗ (chưa đủ 10)"
        print(f"Tổng số traces trên Langfuse: {total}  {ok}")
        print(f"Mở: {HOST}  -> project -> Tracing")
