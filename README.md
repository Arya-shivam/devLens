# 🔍 devLens

> Privacy-first search engine for developers — right in your terminal.

devLens is a CLI tool built on a self-hosted [SearXNG](https://github.com/searxng/searxng-docker) instance. It ranks results by developer relevance (official docs → GitHub → StackOverflow → blogs), reads the top pages, and uses AI to give you a direct answer — no ads, no tracking.

---

## Table of Contents

- [Installation](#installation)
- [Search (`dlens s`)](#-search--dlens-s)
- [Web Search (`dlens web`)](#-web-search--dlens-web)
- [Error Search (`dlens error`)](#-error-search--dlens-error)
- [Package Lookup (`dlens pkg`)](#-package-lookup--dlens-pkg)
- [Shortcuts (`dlens save` / `dlens look`)](#-shortcuts)
- [Piping Errors](#-piping-errors)
- [Configuration](#%EF%B8%8F-configuration)

---

## Installation

### From PyPI

```bash
pip install devlens-cli
```

### From Source

```bash
git clone https://github.com/Arya-shivam/devLens.git
cd devLens
pip install -e .
```

### Prerequisites

devLens needs a running SearXNG instance for search:

```bash
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker
docker compose up -d
```

By default, devLens connects to `http://localhost:8080`. Change this in [Configuration](#%EF%B8%8F-configuration).

---

## 🔎 Search · `dlens s`

The main command. Searches with developer-focused ranking and drops you into an interactive REPL.

```bash
dlens s "python asyncio gather"
```

**What you see:**

```
  🔍 devLens  ·  5 results  ·  0.4s

  1  asyncio.gather — Python docs                    · Docs
     docs.python.org  · https://docs.python.org/3/library/asyncio-task.html
     Run awaitable objects concurrently. If any awaitable is a coroutine...

  2  How to use asyncio.gather — Stack Overflow       · Stack Overflow
     stackoverflow.com  · https://stackoverflow.com/questions/...
     234 votes · The key difference between gather and wait is...

  3  asyncio best practices — GitHub                  · GitHub
     github.com  · https://github.com/python/cpython/...
     CPython source for asyncio.tasks — gather implementation.

  ── o <n> open · s summarize · / <query> search · q quit ──

  >
```

**Interactive commands:**

| You type | What happens |
|----------|-------------|
| `1` or `o 1` | Opens result 1 in your default browser |
| `o 3` | Opens result 3 in your browser |
| `s` | AI reads the top pages and gives you a synthesized answer |
| `/ new query` | Starts a new search without leaving the session |
| `q` or `Ctrl+C` | Quit |

### Options

```bash
dlens s "fastapi middleware" --open 2     # skip interactive, open result 2 directly
dlens s "rust ownership" --lang rust      # filter by language
dlens s "react hooks" --source docs       # filter: docs, github, stackoverflow
dlens s "python decorators" --json        # output raw JSON (for scripting)
dlens s "async python" --no-ai            # disable AI classification
dlens s "flask routes" --limit 5          # show only 5 results
```

---

## 🌐 Web Search · `dlens web`

General internet search — no developer-specific filtering or ranking. Good for non-code questions.

```bash
dlens web "what is QUIC protocol"
dlens web "best mechanical keyboards 2026"
dlens web "coffee shops near tokyo station"
```

Same interactive REPL as `dlens s`. Same `--open`, `--json`, `--limit` options.

---

## 🐛 Error Search · `dlens error`

Paste an error message and devLens finds solutions. Optimized for StackOverflow and GitHub Issues.

```bash
dlens error "TypeError: cannot unpack non-iterable NoneType object"
dlens error "ECONNREFUSED 127.0.0.1:5432" --lang node
dlens error "segfault at 0x0" --source stackoverflow
```

### Options

```bash
dlens error "ModuleNotFoundError: No module named 'cv2'" --lang python
dlens error "error[E0382]: borrow of moved value" --lang rust --open 1
```

---

## 📦 Package Lookup · `dlens pkg`

Find docs, repos, and registry pages for any package.

```bash
dlens pkg httpx                      # searches PyPI, GitHub, docs
dlens pkg httpx --lang python        # adds language context
dlens pkg tokio --lang rust          # finds crates.io + docs.rs
dlens pkg express --lang node        # finds npmjs.com + GitHub
```

---

## ⚡ Shortcuts

Save commands you'll forget. Find them later with fuzzy search.

### Save a command

```bash
dlens save "<command>" "<memorable tag>" [--cat <category>]
```

**Examples:**

```bash
dlens save "git log --oneline --graph --all --decorate" "pretty git log" --cat git
dlens save "docker system prune -af --volumes" "nuke docker" --cat docker
dlens save "ffmpeg -i input.mp4 -vcodec h264 -acodec aac -crf 23 output.mp4" "compress video for web" --cat ffmpeg
dlens save "ssh -L 5432:localhost:5432 user@server" "tunnel postgres" --cat ssh
dlens save "curl -s https://api.github.com/repos/:owner/:repo/releases/latest | jq '.tag_name'" "latest github release" --cat curl
```

### Find a command · `dlens look`

Fuzzy matches your tags — doesn't need to be exact:

```bash
dlens look "git graph"             # → finds "pretty git log"
dlens look "docker clean"          # → finds "nuke docker"
dlens look "video compress"        # → finds "compress video for web"
dlens look "postgres tunnel"       # → finds "tunnel postgres"
```

**What you see:**

```
  1  pretty git log  [git]  (match: 52%)
     git log --oneline --graph --all --decorate
     used 0x · last used never · id 1aec7efe

  ── c copy · r run · e edit · d delete · q quit ──

  >
```

**Interactive commands:**

| You type | What happens |
|----------|-------------|
| `c` or `c 1` | Copy command to clipboard |
| `r` or `r 1` | Execute the command immediately |
| `e` or `e 1` | Edit the command or tag |
| `d` or `d 1` | Delete (asks for confirmation) |
| `q` | Quit |

### List all shortcuts

```bash
dlens shortcuts                    # grouped by category
dlens shortcuts --cat git          # show only git shortcuts
dlens shortcuts --top              # sort by most used
dlens shortcuts --recent           # sort by last used
```

**Output:**

```
  devLens shortcuts  · 3 saved

  docker
  ── nuke docker                    docker system prune -af --volumes

  ffmpeg
  ── compress video for web         ffmpeg -i input.mp4 -vcodec h264 ...

  git
  ── pretty git log                 git log --oneline --graph --all --decorate
```

### Delete shortcuts

```bash
dlens rm "git graph"               # fuzzy find → confirm → delete
dlens rm --cat docker              # delete all docker shortcuts
dlens rm --all                     # nuclear option (confirms first)
```

---

## 🔀 Piping Errors

Pipe stderr from any command directly into devLens:

```bash
python myapp.py 2>&1 | dlens          # pipe a crash
cargo build 2>&1 | dlens              # pipe Rust compiler errors
cat error.log | dlens                  # pipe a log file
npm run build 2>&1 | dlens            # pipe Node errors
```

devLens auto-detects the error, searches for solutions, and gives an AI-generated answer.

---

## ⚙️ Configuration

Settings live in `~/.devlens/config.toml`:

```toml
[search]
engine_url = "http://localhost:8080"    # your SearXNG instance
default_limit = 8                       # results per search

[ai]
openrouter_api_key = "sk-or-..."       # for AI answers (get one at openrouter.ai)

[browser]
command = "firefox"                     # optional: override default browser
# command = "open -a Arc"              # macOS example
```

Shortcuts are stored separately in `~/.devlens/shortcuts.json` — human-readable, easy to back up or sync.

---

## All Commands at a Glance

| Command | What it does |
|---------|-------------|
| `dlens s "query"` | Dev search (interactive) |
| `dlens web "query"` | General web search |
| `dlens error "message"` | Error/stacktrace search |
| `dlens pkg <name>` | Package lookup |
| `dlens save "cmd" "tag"` | Save a command shortcut |
| `dlens look "fuzzy tag"` | Fuzzy find a saved shortcut |
| `dlens shortcuts` | List all saved shortcuts |
| `dlens rm "tag"` | Delete a shortcut |
| `dlens --version` | Print version |

---

## License

MIT
