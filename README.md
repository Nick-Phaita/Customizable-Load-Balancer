# Customizable-Load-Balancer

## Project Overview

This project consists of a customizable load-balancing platform that directs asynchronous HTTP traffic from multiple clients across a dynamic pool of server replicas. At its core is a consistent-hashing ring that ensures even request distribution, while runtime endpoints let you seamlessly add or remove replicas. An optional self-healing mode automatically detects and replaces failed instances, keeping your service running smoothly. All components are packaged as Docker containers and orchestrated via Docker Compose—mirroring the patterns used in large-scale caching layers, database clusters, and traffic management systems.

Key features:
- **Asynchronous request routing** among `N` server containers
- **Consistent hashing** (M=2048 slots, K=100 virtual nodes) for even distribution
- **Dynamic scaling** endpoints to add or remove replicas at runtime
- **Self-healing** mode to detect failed replicas and respawn them automatically
- **Analysis scripts** to measure distribution fairness, scalability, and recovery behavior

## Repository Structure

```
.
├── analysis/                   # Analysis scripts & results
│   ├── a1_experiment.py        # A-1: N=3 distribution bar chart
│   ├── a2_experiment.py        # A-2: avg load vs N line chart
│   ├── a3_experiment.py        # A-3: self-healing demo
│   ├── a4_experiment.py        # A-4: (optional) custom-hash experiments
│   ├── requirements.txt        # Python deps for analysis
│   └── results/                # Generated PNGs
├── load_balancer/              # Task 2 & 3 code
│   ├── app.py                  # Flask load-balancer
│   ├── consistent_hash.py      # Consistent-hash ring
│   ├── Dockerfile
│   └── requirements.txt
├── server/                     # Task 1 code
│   ├── app.py                  # Flask “simple server”
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml          # Bring up servers + LB
```

## Prerequisites

- Windows 11 (PowerShell) or any OS with bash  
- Docker Desktop (Engine & Compose)  
- Python 3.12+

## Setup

Clone the repo:

```bash
git clone https://github.com/Nick-Phaita/Customizable-Load-Balancer.git
cd load-balancer-assignment
```

(Optional) Create & activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Task 1: Simple Server

Build and run a single server container:

```powershell
# Build the image
docker build -t simple-server ./server

# Run one instance as "s1"
docker run -d --name s1 -p 5000:5000 -e SERVER_ID=S1 simple-server

# Test it
curl http://localhost:5000/home
curl -i http://localhost:5000/heartbeat
```

## Task 2: Consistent Hash Ring

Inspect the ring’s slot → server mapping:

```bash
python load_balancer/consistent_hash.py
```

## Task 3: Load Balancer

Bring up 3 servers + LB via Docker Compose (self-healing OFF by default):

```powershell
docker compose up -d --build
```

Check replicas:

```bash
curl http://localhost:5000/rep
```

**Add replicas:**

```powershell
Invoke-RestMethod -Uri http://localhost:5000/add -Method Post -Body (@{ n = 3; hostnames = @('server4','server5','server6') } | ConvertTo-Json) -ContentType 'application/json' 
```

**Remove replicas:**

```powershell
Invoke-RestMethod -Uri http://localhost:5000/rm   -Method Delete -Body (@{ n=3; hostnames=@('server4','server5','server6') } | ConvertTo-Json)   -ContentType 'application/json'
```

### Self-Healing Demo (A-3)

1. Stop the stack:

    ```powershell
    docker compose down
    ```

2. In `docker-compose.yml`, set:

    ```yaml
    environment:
      - ENABLE_HEAL=true
    ```

3. Bring up again:

    ```powershell
    docker compose up -d --build
    ```

4. Kill one server:

    ```powershell
    docker kill server1
    ```

5. Watch it respawn (~5 s):

    ```bash
    docker ps
    curl http://localhost:5000/rep
    ```

## Task 4: Analysis & Testing

**Before running experiments**, ensure analysis dependencies are installed:
```bash
pip install -r analysis/requirements.txt
```

All analysis scripts drive the LB’s API and produce PNG charts in `analysis/results/`. Ensure stack is up (self-healing OFF):

```powershell
docker compose down
docker compose up -d --build
```

- **A-1: N=3 distribution**

    ```bash
    python analysis/a1_experiment.py
    ```

- **A-2: avg load vs N (2…6)**

    ```bash
    python analysis/a2_experiment.py
    ```

- **A-3: self-healing demo** (as above)

    ```bash
    python analysis/a3_experiment.py
    ```

## Testing

- **Manual**: hit endpoints via `curl` or PowerShell `Invoke-RestMethod`.  
- **Automated**: analysis scripts double as test harnesses.

## Deployment

All services run under Docker Compose:

```bash
docker compose up -d --build
```

Tear everything down (including orphans):

```bash
docker compose down --remove-orphans
```

## Additional Materials

- `analysis/results/`: bar & line charts for each experiment.  

## Contributors

- [Nick Maina](https://github.com/Nick-Phaita)
- [Leon Omondi](https://github.com/Ond1mo)
- [Conslata Barasa](https://github.com/Con5lata)
- [Tracey Kyalo](https://github.com/Mwende-Kyalo)


---
