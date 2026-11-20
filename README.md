# Hack the Cloud: Think Like a Hacker, Defend Like an Engineer

Hands-on lab for the DevFest Siliguri 2026 talk. You will attack **ShopBot**, a deliberately
vulnerable AI support agent, steal a fake cloud credential, then switch on defenses and watch the
same attacks fail.

> **Everything is fake and local.** No Google Cloud account, no billing, no real credentials.
> The lab only listens on `127.0.0.1`. Never use these techniques on systems you do not own or
> have written permission to test.

Slides: [`slides/hack-the-cloud.pptx`](slides/hack-the-cloud.pptx)

## What you will do

1. Start a small stack of three containers on your own laptop.
2. Attack the agent three ways: prompt injection, a poisoned tool, and hidden instructions in a web page.
3. Steal a fake service-account token from a fake GCP metadata server.
4. Scan the tool server for the problems you just exploited.
5. Switch on three defenses (prompt filter, tool policy, egress allowlist) and see which one stops which attack.

Time needed: about 15 minutes for the main lab, plus 10 to 20 minutes of setup if you do it at home.

## What runs

| Container | Role |
|---|---|
| `shopbot` | The agent. A deterministic mock "LLM" that behaves like a gullible model, so there is nothing to download and it behaves the same on every laptop |
| `mcp` | An MCP-style tool server with a vulnerable `fetch_url` tool and a poisoned tool description |
| `metadata` | A fake GCP metadata server that returns a fake token and a flag |

---

## Part 1: Install the prerequisites

You need three things: **Docker (with Compose)**, **make**, and **curl** (plus **git** to clone). You also need about 1 GB of free disk space.
Do this **before** the session, on good Wi-Fi.

### macOS

1. Install Docker Desktop from <https://www.docker.com/products/docker-desktop/> (or with Homebrew: `brew install --cask docker`).
2. Open **Docker Desktop** once and wait until it says it is running.
3. Install the command line tools, which give you `make` and `git` (`curl` is already installed):
   ```bash
   xcode-select --install
   ```

### Windows

`make` is not available in plain PowerShell, so use **WSL 2** (Ubuntu). Run every lab command inside the Ubuntu terminal.

1. Open PowerShell **as Administrator** and install WSL with Ubuntu, then restart when asked:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Install Docker Desktop from <https://www.docker.com/products/docker-desktop/>.
3. In Docker Desktop go to **Settings > Resources > WSL integration** and switch on **Ubuntu**.
4. Open the **Ubuntu** app from the Start menu and install the tools:
   ```bash
   sudo apt update && sudo apt install -y make curl git
   ```

### Linux (Debian / Ubuntu)

1. Install Docker Engine and the Compose plugin by following <https://docs.docker.com/engine/install/> for your distribution.
2. Install the other tools:
   ```bash
   sudo apt update && sudo apt install -y make curl git
   ```
3. Let your user run Docker without `sudo`, then log out and back in:
   ```bash
   sudo usermod -aG docker "$USER"
   ```

### Check that everything works

Run these. Each should print a version number and none should print an error:

```bash
docker --version
docker compose version
make --version
curl --version
git --version
docker run --rm hello-world
```

If `docker run --rm hello-world` fails with "Cannot connect to the Docker daemon", Docker is not running. Start Docker Desktop (or your Docker service) and try again.

---

## Part 2: Get the lab and build it

```bash
git clone https://github.com/1mr0-tech/GNIT-workshop.git
cd GNIT-workshop
make preflight
```

`make preflight` downloads the small Python base image (about 50 MB) and builds the lab once. Doing it now means the session itself needs no internet.

---

## Part 3: Run the lab

All commands run from inside the `GNIT-workshop` folder.

### Step 1: Start the lab

```bash
make up
```

You should end with:

```
Lab is up on http://127.0.0.1:8080
```

Check that ShopBot answers:

```bash
make chat MSG='What can you do?'
```

Expected output:

```
defenses: filter=off policy=off egress=off

ShopBot: I can look up orders and fetch pages for you.
```

The `defenses:` line shows which defense layers are on. They are all off for now. You can also try a normal question:

```bash
make chat MSG='Where is order 1001?'
```

### Step 2: Attack ShopBot and steal the flag

ShopBot has a tool called `fetch_url` that can fetch any URL. The fake GCP metadata server is reachable from inside the lab, just like the real one is from inside a real cloud workload.

**Attack A: direct prompt injection**

```bash
make attack
```

Look at the `tool_call` and `tool_result` lines. ShopBot fetched the fake metadata server and gave you its service-account token. Your goal is to see this in the reply:

```
"flag": "FLAG{metadata_is_not_a_secret_store}"
```

**Attack B: tool poisoning (an innocent question)**

```bash
make attack-poisoned
```

You only asked about the return policy. The hidden `<IMPORTANT>` text inside the `fetch_url` tool description told the agent to also fetch the token. The user never typed anything malicious.

**Attack C: indirect prompt injection**

```bash
make attack-indirect
```

The agent reads a web page that has hidden instructions inside it, and obeys them.

To see what each service did behind the scenes:

```bash
make logs
```

### Step 3: Scan the tool server

```bash
make scan
```

You should see findings like these:

```
[HIGH] fetch_url: hidden instructions in description (<IMPORTANT> block)
[HIGH] fetch_url: tells the model to hide its actions
[MED ] fetch_url: description points at a cloud metadata endpoint
[MED ] fetch_url: accepts a URL and arbitrary headers (SSRF risk)
```

This is a tiny pattern-based scanner so you can read how it works (`app/scan.py`). Real scanners (MCP-Scan / Snyk Agent Scan, Cisco mcp-scanner) do much more but are noisy, so always review findings by hand. Which findings would you fix first?

### Step 4: Turn the defenses on

```bash
make defend
make attack
```

Expected: the attack is stopped by the **prompt filter**:

```
BLOCKED by prompt filter: injection pattern in message
```

Now try a rephrased attack that avoids the words the filter looks for:

```bash
make attack-alias
```

Expected: it slips past the filter and is stopped by the **tool policy**:

```
BLOCKED by tool policy: custom headers not allowed for fetch_url
```

Now try the other attacks with everything on:

```bash
make attack-poisoned
make attack-indirect
```

### Step 5: See what each layer covers

Turn on one layer at a time and run all four attacks each time (`attack`, `attack-alias`, `attack-poisoned`, `attack-indirect`):

```bash
make defend LAYERS=filter
make defend LAYERS=policy
make defend LAYERS=egress
```

| Layer | Where it runs | What it does |
|---|---|---|
| `filter` | ShopBot | Blocks known injection patterns in the **user's message** |
| `policy` | ShopBot | Drops hidden instructions from tool descriptions, denies custom headers on `fetch_url` |
| `egress` | Tool server | `fetch_url` may only reach approved hosts |

Questions to answer for yourself:
- Which layer stops the most attacks on its own?
- Why does the filter miss the poisoned tool and the indirect injection?
- Why is one layer not enough?

### Step 6: Stretch challenges

Finished early? Try these.

1. **Bypass the filter.** Reword the attack so the filter misses it. Which layer still stops you?
2. **Break the egress rule.** Turn on only `egress` (`make defend LAYERS=egress`) and find another way to reach the fake metadata server. Hint: look at what other endpoints ShopBot itself serves, and what the tool does after it fetches a URL.
3. **Fix the tool.** Edit `app/mcp_server.py` so `fetch_url` is safe even when `egress` is the only layer on. Rebuild with `docker compose up -d --build` and re-run every attack.
4. **Red-team it.** Point [garak](https://github.com/NVIDIA/garak) or [promptfoo](https://github.com/promptfoo/promptfoo) at ShopBot (`POST http://127.0.0.1:8080/chat` with body `{"message": "..."}`) and compare what it finds with your manual attacks.

### Cleaning up

```bash
make undefend    # switch all defenses off
make down        # stop the containers
make reset       # stop and restore the original state
```

---

## Command cheat sheet

| Command | What it does |
|---|---|
| `make preflight` | Pull the base image and build (do this once, before the session) |
| `make up` | Start the lab |
| `make chat MSG='...'` | Send a message to ShopBot |
| `make attack` | Direct prompt injection aimed at the metadata server |
| `make attack-alias` | The same attack, reworded to dodge the filter |
| `make attack-poisoned` | An innocent question; the poisoned tool does the rest |
| `make attack-indirect` | Hidden instructions inside a page the agent reads |
| `make scan` | Scan the tool server's descriptions |
| `make defend [LAYERS="filter policy egress"]` | Switch defenses on |
| `make undefend` | Switch all defenses off |
| `make status` | Show which defenses are on |
| `make logs` | Show the last log lines from every service |
| `make down` / `make reset` | Stop the lab / stop and restore the original state |

## How the lab maps to real Google Cloud

| In the lab | On Google Cloud |
|---|---|
| Fake metadata server | The real metadata server hands tokens to any caller in a workload. Keep credentials out of the agent's reach, for example with [Agent Compute Engine](https://cloud.google.com/blog/topics/ai-infrastructure/introducing-agent-compute-engine-and-expanded-agent-governance) |
| Egress allowlist | VPC egress controls and Agent Gateway outbound policy |
| Tool policy | [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) policy, or open source [agentgateway](https://agentgateway.dev) with CEL-based RBAC |
| Prompt filter | Model Armor. One layer, not the fix |
| `make scan` | MCP-Scan / Snyk Agent Scan, Cisco mcp-scanner |
| One identity per agent | Agent Identity (SPIFFE), or open source SPIRE |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running. Start Docker Desktop (or your Docker service) |
| `make: command not found` | Install `make` (see Part 1). On Windows, run inside the Ubuntu (WSL) terminal |
| `curl: (52) Empty reply from server` right after `make up` | ShopBot is still starting. Wait two seconds and retry |
| `make up` says ShopBot did not come up | Run `make logs`. Port 8080 may already be in use. Stop whatever is using it |
| `permission denied` talking to Docker on Linux | Add your user to the `docker` group (see Part 1), then log out and back in |
| Changes to `app/*.py` do not show up | Rebuild: `docker compose up -d --build` |
| Something is stuck | `make reset`, then `make up` |

## Repository layout

```
.
├── README.md            this guide
├── Makefile             all the commands above
├── docker-compose.yml   the three containers
├── Dockerfile           one small Python image, used by all three
├── app/
│   ├── shopbot.py       the vulnerable agent and its defense layers
│   ├── mcp_server.py    the tool server with the poisoned fetch_url
│   ├── metadata_server.py  the fake GCP metadata server
│   ├── scan.py          the tiny tool scanner
│   └── common.py        shared defense-switch loader
├── state/defense.json   which defense layers are on
└── slides/              the talk slides
```

## License and use

For education only. All credentials, tokens and flags in this repo are fake.
