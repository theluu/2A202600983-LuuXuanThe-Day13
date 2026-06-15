import argparse
import concurrent.futures
import json
import os
import time
from pathlib import Path

import httpx

# Cổng lấy từ --port hoặc env LAB_PORT, mặc định 8000.
QUERIES = Path("data/sample_queries.jsonl")
BASE_URL = f"http://127.0.0.1:{os.getenv('LAB_PORT', '8000')}"


def send_request(client: httpx.Client, payload: dict) -> None:
    try:
        start = time.perf_counter()
        r = client.post(f"{BASE_URL}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        print(f"[{r.status_code}] {r.json().get('correlation_id')} | {payload['feature']} | {latency:.1f}ms")
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--port", type=int, default=int(os.getenv("LAB_PORT", "8000")),
                        help="Cổng app (mặc định env LAB_PORT hoặc 8000)")
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = f"http://127.0.0.1:{args.port}"
    print(f"-> {BASE_URL}/chat")

    lines = [line for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    
    with httpx.Client(timeout=30.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [executor.submit(send_request, client, json.loads(line)) for line in lines]
                concurrent.futures.wait(futures)
        else:
            for line in lines:
                send_request(client, json.loads(line))


if __name__ == "__main__":
    main()
