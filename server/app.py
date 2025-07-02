# app.py
from flask import Flask, jsonify
import os

app = Flask(__name__)

SERVER_ID = os.environ.get("SERVER_ID", "unknown")

@app.get("/home")
def home():
    # Matches spec: “Hello from Server: <ID>”  :contentReference[oaicite:0]{index=0}
    return jsonify(message=f"Hello from Server: {SERVER_ID}",
                   status="successful"), 200

@app.get("/heartbeat")
def heartbeat():
    # Empty body but 200 OK is fine  :contentReference[oaicite:1]{index=1}
    return ("", 200)

if __name__ == "__main__":
    # Flask looks at PORT env var; default 5000 per spec
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
