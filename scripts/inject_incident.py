from __future__ import annotations

import argparse
import os

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=["rag_slow", "tool_fail", "cost_spike"])
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.getenv("LAB_PORT", "8000")),
                        help="Cổng app (mặc định env LAB_PORT hoặc 8000)")
    args = parser.parse_args()

    base_url = f"http://127.0.0.1:{args.port}"
    path = f"/incidents/{args.scenario}/disable" if args.disable else f"/incidents/{args.scenario}/enable"
    r = httpx.post(f"{base_url}{path}", timeout=10.0)
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
