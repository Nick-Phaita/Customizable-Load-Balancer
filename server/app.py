import os
from flask import Flask, jsonify

app = Flask(__name__)

# Picked up from docker-compose or `docker run -e SERVER_ID=<id>`
SERVER_ID = os.getenv("SERVER_ID", "unknown")


@app.get("/home")
def home():
    """Return a friendly ID so the load balancer can tell replicas apart."""
    return jsonify(
        {
            "message": f"Hello from Server: {SERVER_ID}",
            "status": "successful",
        }
    ), 200


@app.get("/heartbeat")
def heartbeat():
    """Light-weight health-check used by the load balancer."""
    return "", 200


if __name__ == "__main__":
    # 0.0.0.0 => accept traffic from outside the container
    app.run(host="0.0.0.0", port=5000)
