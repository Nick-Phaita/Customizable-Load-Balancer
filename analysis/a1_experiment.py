import requests
import threading
from collections import Counter
import matplotlib.pyplot as plt

LB_URL = "http://localhost:5000"
TOTAL_REQUESTS = 10_000
THREADS = 100

def ensure_replicas(n):
    resp = requests.get(f"{LB_URL}/rep").json()
    current = resp["message"]["N"]
    if current < n:
        requests.post(f"{LB_URL}/add", json={"n": n - current}).raise_for_status()
    elif current > n:
        requests.delete(f"{LB_URL}/rm",  json={"n": current - n}).raise_for_status()

def run_experiment():
    ensure_replicas(3)
    counts = Counter()
    def worker(batch):
        for _ in range(batch):
            try:
                r = requests.get(f"{LB_URL}/home")
                if r.status_code == 200:
                    # "Hello from Server: <ID>"
                    sid = r.json()["message"].split(":")[-1].strip()
                    counts[sid] += 1
            except:
                pass

    batch = TOTAL_REQUESTS // THREADS
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, args=(batch,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Plot bar chart
    servers, values = zip(*sorted(counts.items()))
    plt.figure()
    plt.bar(servers, values)
    plt.title("A-1: Request Distribution (10k reqs, N=3)")
    plt.xlabel("Server ID")
    plt.ylabel("Request Count")
    plt.tight_layout()
    plt.savefig("analysis/results/a1_distribution_N3.png")
    print("Per-server counts:", dict(counts))

if __name__ == "__main__":
    run_experiment()
