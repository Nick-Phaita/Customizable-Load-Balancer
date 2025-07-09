from flask import Flask, jsonify, request
import random, os, requests, docker, threading, time
from consistent_hash import ConsistentHashRing

app = Flask(__name__)
client = docker.from_env()
ring   = ConsistentHashRing()

# ── Configuration ───────────────────────────────────────────────
NETWORK         = os.getenv("LB_NETWORK", "lb_network")
PROJECT_LABEL   = os.getenv("LB_PROJECT")
SERVICE_LABEL   = os.getenv("LB_SERVICE")
ENABLE_HEAL     = os.getenv("ENABLE_HEAL", "false").lower() == "true"
HEALTH_INTERVAL = int(os.getenv("HEALTH_INTERVAL", "5"))
INITIAL_SERVERS = ["server1", "server2", "server3"]
TARGET_N        = len(INITIAL_SERVERS)

# ── Boot strap the ring ──────────────────────────────────────────
for srv in INITIAL_SERVERS:
    ring.add_server(srv)

# ── Endpoints ────────────────────────────────────────────────────
@app.route("/rep", methods=["GET"])
def replicas():
    s = ring.servers()
    return jsonify({"message": {"N": len(s), "replicas": s}, "status": "successful"}), 200

@app.route("/add", methods=["POST"])
def add_servers():
    data      = request.get_json() or {}
    n         = data.get("n", 0)
    hostnames = data.get("hostnames", [])
    existing  = set(ring.servers())
    new_hosts = []

    # validation
    if not isinstance(n, int) or n < 1:
        return jsonify({"message":"<Error> 'n' must be a positive integer","status":"failure"}),400
    if len(hostnames) > n:
        return jsonify({"message":"<Error> Too many hostnames provided","status":"failure"}),400

    # honor provided names
    for h in hostnames:
        if h in existing:
            return jsonify({"message":f"<Error> Server {h} already exists","status":"failure"}),400
        new_hosts.append(h)

    # auto–generate the rest
    while len(new_hosts) < n:
        h = f"server{random.randint(1000,9999)}"
        if h not in existing and h not in new_hosts:
            new_hosts.append(h)

    # spawn & label
    for h in new_hosts:
        labels = {}
        if PROJECT_LABEL:
            labels["com.docker.compose.project"] = PROJECT_LABEL
        if SERVICE_LABEL:
            labels["com.docker.compose.service"] = SERVICE_LABEL

        client.containers.run(
            "server:latest",
            name=h,
            detach=True,
            network=NETWORK,
            environment={"SERVER_ID": h},
            labels=labels
        )
        ring.add_server(h)

    s = ring.servers()
    return jsonify({"message":{"N":len(s),"replicas":s},"status":"successful"}),200

@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data      = request.get_json() or {}
    n         = data.get("n")
    hostnames = data.get("hostnames", [])
    current   = ring.servers()

    # validation
    if not isinstance(n, int) or n < 1 or n > len(current):
        return jsonify({"message":"<Error> 'n' out of range","status":"failure"}),400
    if len(hostnames) > n:
        return jsonify({"message":"<Error> Too many hostnames provided","status":"failure"}),400

    to_remove = []
    for h in hostnames:
        if h not in current:
            return jsonify({"message":f"<Error> Server {h} does not exist","status":"failure"}),400
        to_remove.append(h)

    import random as _rand
    candidates = [s for s in current if s not in to_remove]
    while len(to_remove) < n:
        choice = _rand.choice(candidates)
        candidates.remove(choice)
        to_remove.append(choice)

    for h in to_remove:
        try:
            c = client.containers.get(h)
            c.stop(); c.remove()
        except docker.errors.NotFound:
            pass
        ring.remove_server(h)

    s = ring.servers()
    return jsonify({"message":{"N":len(s),"replicas":s},"status":"successful"}),200

@app.route("/<path:path>", methods=["GET"])
def proxy(path):
    rid    = random.randint(100000,999999)
    target = ring.get_server(rid)
    try:
        resp = requests.get(f"http://{target}:5000/{path}")
    except:
        return jsonify({"message":f"<Error> Could not reach {target}","status":"failure"}),502
    if resp.status_code != 200:
        return jsonify({"message":f"<Error> '/{path}' not found","status":"failure"}),400
    return (resp.content, resp.status_code, resp.headers.items())

# ── Toggleable Self-Healer ────────────────────────────────────────
def health_check_loop():
    while True:
        current = list(ring.servers())
        for srv in current:
            try:
                requests.get(f"http://{srv}:5000/heartbeat", timeout=2)
            except:
                ring.remove_server(srv)
                try:
                    client.containers.get(srv).remove(force=True)
                except:
                    pass
        # respawn until TARGET_N
        while len(ring.servers()) < TARGET_N:
            new_name = f"server{random.randint(1000,9999)}"
            if new_name in ring.servers(): 
                continue
            labels = {}
            if PROJECT_LABEL:
                labels["com.docker.compose.project"] = PROJECT_LABEL
            if SERVICE_LABEL:
                labels["com.docker.compose.service"] = SERVICE_LABEL
            labels["com.docker.compose.oneoff"] = "True"

            client.containers.run(
                "server:latest",
                name=new_name,
                detach=True,
                network=NETWORK,
                environment={"SERVER_ID": new_name},
                labels=labels
            )
            ring.add_server(new_name)
        time.sleep(HEALTH_INTERVAL)

if __name__ == "__main__":
    if ENABLE_HEAL:
        threading.Thread(target=health_check_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
