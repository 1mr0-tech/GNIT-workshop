# Hack the Cloud CTF: attack and defend an AI agent

Capture-the-flag lab for the DevFest Siliguri 2026 talk *Hack the Cloud: Think Like a Hacker, Defend Like an Engineer*.

You will hack **ShopBot**, a deliberately vulnerable AI support agent running on a fake GCP project, from a web interface in your browser. There are **8 challenges and 950 points**: leak secrets, poison a tool, steal a cloud credential, beat the defenses, then become the defender.

> **Everything is fake and local.** No Google Cloud account, no billing, no real credentials.
> The lab only listens on `127.0.0.1`. Never use these techniques on systems you do not own or
> have written permission to test.

Slides: [`slides/hack-the-cloud.pptx`](slides/hack-the-cloud.pptx)

## What runs

| Service | Role |
|---|---|
| `shopbot` | The agent and the CTF web interface. A deterministic mock "LLM" that behaves like a gullible model, so there is nothing to download and it behaves the same on every laptop |
| `mcp` | An MCP-style tool server with a vulnerable `fetch_url` tool |
| `metadata` | A fake GCP metadata server that hands out fake tokens and flags |

---

## Part 1: Choose your setup

Pick **one**. Path A and Path B need no Docker, no WSL and no restart.

| | Path A: Codespaces | Path B: Python only | Path C: Docker |
|---|---|---|---|
| Install | Nothing (runs in your browser) | Python 3 (about 100 MB, no restart) | Docker + make |
| Works on | Any laptop with a browser | Windows, macOS, Linux | macOS, Linux (Windows needs WSL 2) |
| Needs | A free GitHub account, internet | Nothing else | Docker running |
| Start command | `python3 lab.py up` | `python lab.py up` (`python3` on macOS/Linux) | `make up` |
| Recommended for | Windows students, locked-down laptops | Most people | People who already use Docker |

**If you are on Windows and do not already have Docker, use Path A or Path B.** Docker Desktop on Windows needs WSL 2 and usually a restart, which is why this lab does not require it.

### Path A: GitHub Codespaces (nothing to install)

1. Sign in at <https://github.com> (create a free account if you need one).
2. Open <https://codespaces.new/1mr0-tech/GNIT-workshop> and click **Create new codespace**.
3. Wait about a minute for VS Code to open in your browser. Use the **Terminal** at the bottom.
4. Check Python and you are done:
   ```bash
   python3 --version
   ```
5. Continue with Part 2 below. In a Codespace, run every command with `python3 lab.py ...`. When the lab starts, VS Code shows a pop-up for port 8080: click **Open in Browser**. (If you miss it, open the **Ports** tab and click the globe icon next to 8080.)
6. When you finish, stop it so it does not use your free monthly allowance: click the Codespaces name in the bottom-left corner, then **Stop current codespace**.

### Path B: Python only (Windows, macOS, Linux)

**1. Install Python 3.8 or newer** (skip if `python --version` / `python3 --version` already works).

- **Windows:** download the installer from <https://www.python.org/downloads/>. On the first screen tick **Add python.exe to PATH**, then click **Install Now**. No restart is needed. Or, in PowerShell: `winget install Python.Python.3.12`.
- **macOS:** run `python3 --version`. If it is missing, install from <https://www.python.org/downloads/> or run `brew install python`.
- **Linux:** run `python3 --version`. If it is missing: `sudo apt update && sudo apt install -y python3`.

**2. Get the lab.** Either of these works:

- With git: `git clone https://github.com/1mr0-tech/GNIT-workshop.git`
- Without git: on the repository page click **Code > Download ZIP**, then unzip it.

**3. Open a terminal in the lab folder.**

- Windows: open the unzipped folder in File Explorer, click the address bar, type `cmd` and press Enter. Or open PowerShell and `cd` into the folder.
- macOS/Linux: `cd GNIT-workshop`

**4. Check it works:**

```bash
python lab.py help
```

(Use `python3` instead of `python` on macOS/Linux. On Windows, if `python` opens the Microsoft Store or says "not found", use `py lab.py help` instead, or reinstall Python and tick "Add python.exe to PATH".)

You should see the list of commands. Continue with Part 2 below.

### Path C: Docker + make

Only use this if you already have Docker. Do it **before** the session on good Wi-Fi.

1. **Install Docker and make.**
   - **macOS:** install Docker Desktop from <https://www.docker.com/products/docker-desktop/>, open it once and wait until it is running. Then run `xcode-select --install` for `make` and `git`.
   - **Linux (Debian/Ubuntu):** follow <https://docs.docker.com/engine/install/> for Docker Engine and the Compose plugin. Then `sudo apt update && sudo apt install -y make curl git`, and `sudo usermod -aG docker "$USER"` (log out and back in).
   - **Windows:** Docker Desktop needs WSL 2 and usually a restart. Use Path A or B instead unless you already have it working.
2. **Check:**
   ```bash
   docker --version
   docker compose version
   make --version
   docker run --rm hello-world
   ```
   If the last command says "Cannot connect to the Docker daemon", start Docker Desktop (or your Docker service).
3. **Get the lab and build it** (downloads a 50 MB image, so do it before the session):
   ```bash
   git clone https://github.com/1mr0-tech/GNIT-workshop.git
   cd GNIT-workshop
   make preflight
   ```
   Continue with Part 2 below, using `make ...` instead of `python lab.py ...`.

---

## Part 2: Start the lab

Run these inside the `GNIT-workshop` folder. Use the row for your path (on macOS and Linux write `python3` instead of `python`).

| | Path A / B (Python) | Path C (Docker) |
|---|---|---|
| Start | `python lab.py up` | `make up` |
| Open the CTF | `python lab.py open` (or visit the address below) | open the address below |
| Stop | `python lab.py down` | `make down` |
| Reset score and defenses | `python lab.py reset` | `make reset` |

When it starts you should see:

```
Lab is up. Open http://127.0.0.1:8080 in your browser.
```

Open **<http://127.0.0.1:8080>**. You should see the CTF: a chat window on the left and the challenge board on the right.

---

## Part 3: Play the CTF

### Find your way around

- **Chat with ShopBot (left).** Everything you type goes to the agent. Under each reply, the **Agent trace** shows what the agent actually did: tool calls in yellow, tool results in green, defenses that blocked something in red. The trace is your best friend.
- **Challenges (right).** Eight challenges. Flags look like `FLAG{...}`. Paste one into **Submit flag** to score.
- **Defenses.** Three switches (prompt filter, tool policy, egress allowlist), plus the **Verify defenses** button for the final challenge.
- **Tools.** What the tool server tells the model. Customers never see this, but the model does.
- **Scanner.** A tiny pattern-based tool scanner. Run it and ask yourself which findings are real.

### Rules

- Flags only come from the lab itself. Reading the source code to spoil flags defeats the point (reading it to understand *how* it works is encouraged for the later challenges).
- **Hints cost 10 points each**, and a challenge never pays less than half. Try before you buy.
- Some flags depend on the defense configuration you are in when you attack. The flag proves you did it the right way.
- Stuck or messed up? **Reset lab** in the page footer clears your score and switches the defenses off.

### The challenges

| # | Challenge | Category | Points | Your mission |
|---|---|---|---|---|
| 1 | Loose Lips | Recon | 50 | ShopBot has a secret tucked into its instructions. Make it reveal them |
| 2 | Read The Fine Print | Tools | 50 | The model reads tool descriptions that customers never see. Find the flag hiding in one |
| 3 | Token Heist | Injection | 100 | Defenses off. Make ShopBot hand you the service-account token from the metadata server |
| 4 | Innocent Question | Injection | 100 | Defenses off. Get a flag without typing anything malicious. Only ask a normal question |
| 5 | Don't Trust The Page | Injection | 150 | Defenses off. Make ShopBot obey instructions hidden inside a web page it reads |
| 6 | Speed Bump | Bypass | 150 | Turn on **only** the prompt filter, then still steal the token |
| 7 | The Open Door | Bypass | 200 | Turn on **only** the egress allowlist, then still reach the metadata server |
| 8 | Blue Team | Defense | 150 | Switch on at least two layers so every attack fails, then click **Verify defenses** |

Suggested order: 1, 2, then 3, 4, 5, then the bypasses (6, 7), and finish with 8.

### Useful background

- ShopBot can call two tools: `lookup_order` and `fetch_url`. `fetch_url` reads any URL you give it.
- Inside the lab, ShopBot can reach a **fake GCP metadata server** at `http://metadata.google.internal/computeMetadata/v1/`, just like a real cloud workload can reach the real one. The real server hands out access tokens for the workload's service account.
- ShopBot serves a few web pages of its own, such as `http://shopbot:8080/docs/returns`. It can fetch those too.
- Try the example chips under the chat box to see normal behavior first.

### What the three defense layers do

| Layer | Where it runs | What it does |
|---|---|---|
| Prompt filter | ShopBot | Blocks known injection patterns in the **user's message** |
| Tool policy | ShopBot | Drops hidden instructions from tool descriptions, denies custom headers on `fetch_url` |
| Egress allowlist | Tool server | `fetch_url` may only reach approved hosts |

When you finish, think about: which layer stopped the most attacks on its own? Why did the filter miss some? Why is one layer never enough?

### Optional: terminal commands

You do not need these to play. They are for debugging and for automating attacks:

| Command (Python) | What it does |
|---|---|
| `python lab.py chat "hello"` | Talk to ShopBot from the terminal (Docker: `make chat MSG='hello'`) |
| `python lab.py defend [filter] [policy] [egress]` | Switch layers on (all three if you name none; Docker: `make defend LAYERS="filter policy"`) |
| `python lab.py undefend` / `status` / `logs` / `scan` | Defenses off / show state / show service logs / run the scanner |

---

## How the lab maps to real Google Cloud

| In the lab | On Google Cloud |
|---|---|
| Fake metadata server | The real metadata server hands tokens to any caller in a workload. Keep credentials out of the agent's reach, for example with [Agent Compute Engine](https://cloud.google.com/blog/topics/ai-infrastructure/introducing-agent-compute-engine-and-expanded-agent-governance) |
| Egress allowlist | VPC egress controls and Agent Gateway outbound policy |
| Tool policy | [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) policy, or open source [agentgateway](https://agentgateway.dev) with CEL-based RBAC |
| Prompt filter | Model Armor. One layer, not the fix |
| Scanner tab | MCP-Scan / Snyk Agent Scan, Cisco mcp-scanner |
| One identity per agent | Agent Identity (SPIFFE), or open source SPIRE |

## Troubleshooting

| Problem | Fix |
|---|---|
| The page does not load | Is the lab running? Run `python lab.py up` (or `make up`). Then open <http://127.0.0.1:8080> |
| `python` is not found, or opens the Microsoft Store (Windows) | Use `py lab.py ...`, or reinstall Python and tick **Add python.exe to PATH** |
| `python` not found (macOS/Linux) | Use `python3 lab.py ...` |
| Port 8080 is already in use | Use another port. macOS/Linux: `SHOPBOT_PORT=8090 python3 lab.py up`. Windows PowerShell: `$env:SHOPBOT_PORT=8090; python lab.py up`. Docker: `SHOPBOT_PORT=8090 make up`. Then open `http://127.0.0.1:8090` |
| `Something is already listening on port ...` | Run `python lab.py down`, or pick other ports as above |
| ShopBot says it cannot be reached | The lab stopped. Start it again with `python lab.py up` |
| `python lab.py up` says the lab did not come up | Read the log lines it prints, or run `python lab.py logs` |
| Score or defenses look wrong | Click **reset lab** in the page footer, or run `python lab.py reset` |
| (Docker) `Cannot connect to the Docker daemon` | Docker is not running. Start Docker Desktop or your Docker service |
| (Docker) `make: command not found` | Install `make`, or use Path A or B |
| (Docker) changes to `app/*` do not show up | Rebuild: `docker compose up -d --build` |
| (Docker, Linux) `permission denied` talking to Docker | Add your user to the `docker` group, then log out and back in |

## About the Docker-free mode

`lab.py` starts the same three servers as small background Python processes on your machine, bound to `127.0.0.1` only. A tiny shim (`app/localnet.py`) maps the lab's host names (`shopbot`, `mcp`, `metadata.google.internal`) to localhost **inside the lab's own processes**. It does not change your hosts file, DNS or any system setting, and it ignores system HTTP proxies so lab traffic stays on your machine. `python lab.py down` stops everything.

## Repository layout

```
.
├── README.md            this guide
├── lab.py               runs the lab with just Python (no Docker, no make)
├── Makefile             the same commands for Docker users
├── docker-compose.yml   the three containers (Docker path)
├── Dockerfile           one small Python image, used by all three
├── .devcontainer/       one-click GitHub Codespaces setup
├── app/
│   ├── shopbot.py          the vulnerable agent, its defense layers and the web API
│   ├── web/index.html      the CTF web interface
│   ├── ctf.py              challenges, flag checking and scoring
│   ├── mcp_server.py       the tool server with the poisoned fetch_url
│   ├── metadata_server.py  the fake GCP metadata server
│   ├── scan.py             the tiny tool scanner
│   ├── common.py           shared settings
│   └── localnet.py         maps host names to localhost in Docker-free mode
├── state/               created at runtime: defense switches and your score
└── slides/              the talk slides
```

## License and use

For education only. All credentials, tokens and flags in this repo are fake.
