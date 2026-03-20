# devLens

> Privacy-first search engine for developers

devLens is a CLI tool built on top of a self-hosted SearXNG instance. It intelligently filters and ranks search results (official docs > GitHub > StackOverflow > blogs) and uses AI to synthesize direct answers from multiple sources — right in your terminal.

## Prerequisites

devLens requires a running [SearXNG](https://github.com/searxng/searxng-docker) instance. Set one up locally:

```bash
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker
docker compose up -d
```

## Installation

```bash
pip install devlens
```

Or install from source:

```bash
git clone https://github.com/Arya-shivam/devLens.git
cd devLens
pip install -e .
```

## Quick Start

```bash
# General developer search (with AI-powered answers)
dlens "python reverse linked list"

# General internet search (bypasses dev filters)
dlens web "what is QUIC?"

# Error search
dlens error "TypeError: cannot unpack non-iterable NoneType"

# Package lookup
dlens pkg httpx
```

## Piping and Stdin

devLens automatically falls back to error parsing if invoked via a pipe:

```bash
cat error.log | dlens
python myapp.py 2>&1 | dlens
```

## AI Features

devLens uses [OpenRouter](https://openrouter.ai/) to read top search results and generate direct answers. Set your API key in the config:

```bash
dlens --no-ai "query"   # Disable AI, show raw results
```

## Configuration

Settings are stored in `~/.devlens/config.toml`:

```toml
[search]
engine_url = "http://localhost:8080"
default_limit = 8

[ai]
openrouter_api_key = "sk-or-..."
```

## License

MIT
