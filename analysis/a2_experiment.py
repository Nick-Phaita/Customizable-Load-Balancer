# analysis/a2_experiment.py

import requests
from collections import Counter
import matplotlib.pyplot as plt

LB_URL = "http://localhost:5000"
TOTAL  = 10_000

# reuse one session (one TCP connection)
session = requests.Session()

def ensure_replicas(n):
    r = session.get(f"{LB_URL}/rep")
    r.raise_for_status()
    current = r.json()["message"]["N"]
    if current < n:
        session.post(f"{LB_URL}/add", json={"n": n - current}).raise_for_status()
    elif current > n:
        session.delete(f"{LB_URL}/rm", json={"n": current - n}).raise_for_status()

def run_for_n(n):
    ensure_replicas(n)
    counts = Counter()
    for _ in range(TOTAL):
        try:
            r = session.get(f"{LB_URL}/home")
            r.raise_for_status()
            sid = r.json()["message"].split(":")[-1].strip()
            counts[sid] += 1
        except:
            pass
    return counts

def main():
    Ns   = list(range(2, 7))
    avgs = []

    for n in Ns:
        counts = run_for_n(n)
        avg    = sum(counts.values()) / len(counts)
        avgs.append(avg)
        print(f"N={n} → avg requests/server = {avg:.2f}")

    plt.figure()
    plt.plot(Ns, avgs, marker="o")
    plt.title("A-2: Average Load vs N")
    plt.xlabel("Number of Replicas (N)")
    plt.ylabel("Average Requests per Server")
    plt.tight_layout()
    plt.savefig("analysis/results/a2_avg_load_vs_N.png")
    print("Chart saved to analysis/results/a2_avg_load_vs_N.png")

if __name__ == "__main__":
    main()
