import time, subprocess, requests

LB_URL        = "http://localhost:5000"
CHECK_INTERVAL= 1    # second
TIMEOUT       = 60   # seconds

def get_replicas():
    return requests.get(f"{LB_URL}/rep").json()["message"]["replicas"]

def kill_container(name):
    subprocess.run(["docker","kill", name], check=True)
    print(f"Killed container {name}")

def wait_for_replacement(old_name, expected_n):
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        reps = get_replicas()
        # once old is gone and count is correct, we’ve true recovery
        if old_name not in reps and len(reps) == expected_n:
            print("Replaced", old_name, "→", reps)
            return True
        time.sleep(CHECK_INTERVAL)
    print("❌ No replacement within timeout")
    return False

if __name__ == "__main__":
    initial = get_replicas()
    print("Initial replicas:", initial)

    to_kill = initial[0]
    kill_container(to_kill)

    wait_for_replacement(to_kill, len(initial))
