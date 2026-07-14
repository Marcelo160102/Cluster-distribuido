"""Benchmark de rendimiento del clúster (Fase 4).

Uso:
    python tests/benchmark.py [url] [n_requests] [concurrency]

Ejemplo:
    python tests/benchmark.py https://localhost 200 10
"""
import asyncio
import json
import statistics
import sys
import time
import uuid

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://localhost"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
C = int(sys.argv[3]) if len(sys.argv) > 3 else 10
API_KEY = "cluster-demo-key-2026"

PAYLOAD = {
    "data": json.dumps({
        "extension": "999",
        "protocol": "SIP",
        "ip_address": "10.0.0.99",
        "status": "online",
        "user_agent": "Benchmark",
    })
}


async def bench_get(client: httpx.AsyncClient, results: list):
    t0 = time.perf_counter()
    try:
        r = await client.get(f"{BASE_URL}/data", headers={"X-API-Key": API_KEY})
        lat = (time.perf_counter() - t0) * 1000
        results.append(lat)
        return r.status_code
    except Exception:
        return None


async def bench_post(client: httpx.AsyncClient, results: list):
    t0 = time.perf_counter()
    try:
        r = await client.post(
            f"{BASE_URL}/data",
            json=PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        lat = (time.perf_counter() - t0) * 1000
        results.append(lat)
        return r.status_code
    except Exception:
        return None


def print_stats(label: str, latencies: list[float], ok: int, total: int):
    if not latencies:
        print(f"  {label}: 0/0 exitoso")
        return
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    avg = statistics.mean(latencies)
    duration_s = (sum(latencies) / 1000) / C  # approx wall time
    rps = ok / duration_s if duration_s > 0 else 0
    print(f"  {label}:")
    print(f"    Requests:    {ok}/{total} exitosos")
    print(f"    Latencia ms: p50={p50:.1f}  p95={p95:.1f}  p99={p99:.1f}  avg={avg:.1f}")
    print(f"    Throughput:  {rps:.0f} req/s")


async def main():
    print(f"=== Benchmark del Clúster ===")
    print(f"URL:      {BASE_URL}")
    print(f"Requests: {N}")
    print(f"Workers:  {C}")
    print()

    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # --- GET /data ---
        print("--- GET /data ---")
        get_results = []
        tasks = [bench_get(client, get_results) for _ in range(N)]
        statuses = await asyncio.gather(*tasks)
        ok = sum(1 for s in statuses if s == 200)
        print_stats("GET", get_results, ok, N)

        # --- POST /data ---
        print("--- POST /data ---")
        post_results = []
        tasks = [bench_post(client, post_results) for _ in range(N)]
        statuses = await asyncio.gather(*tasks)
        ok = sum(1 for s in statuses if s == 200)
        print_stats("POST", post_results, ok, N)

    print()
    print("Benchmark completado.")


if __name__ == "__main__":
    asyncio.run(main())
