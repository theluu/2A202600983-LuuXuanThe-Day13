"""Kiểm tra Langfuse: (1) auth, (2) thật sự bắn được trace lên.

    python scripts/check_langfuse.py
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # nạp key từ .env (bắt buộc, nếu không get_client() không thấy key)

from langfuse import get_client

langfuse = get_client()

# --- Mức 1: auth (giống đoạn của thầy) ---
if langfuse.auth_check():
    print("[1] AUTH OK — key đúng, kết nối được Langfuse.")
else:
    print("[1] AUTH FAIL — sai key hoặc sai host. Dừng.")
    raise SystemExit(1)

# --- Mức 2: thật sự bắn 1 trace rồi đếm lại qua API ---
import httpx

HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
auth = (os.getenv("LANGFUSE_PUBLIC_KEY"), os.getenv("LANGFUSE_SECRET_KEY"))


def count() -> int:
    r = httpx.get(f"{HOST}/api/public/traces", params={"limit": 1}, auth=auth, timeout=15)
    r.raise_for_status()
    return r.json().get("meta", {}).get("totalItems", 0)


before = count()
with langfuse.start_as_current_span(name="connectivity-test") as span:
    span.update_trace(name="connectivity-test", tags=["smoke-test"])
langfuse.flush()          # ép gửi ngay
time.sleep(6)             # chờ Langfuse nhận
after = count()

print(f"[2] traces trước={before}  sau={after}")
if after > before:
    print("    ✓ BẮN LÊN ĐƯỢC — trace mới đã hiện trên Langfuse.")
else:
    print("    ✗ CHƯA thấy trace mới (chờ thêm vài giây / kiểm tra lại project).")
print(f"    Mở xem: {HOST}")
