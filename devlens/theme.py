"""
devLens — centralised theme tokens.

Every colour, style, and layout constant used by the render layer lives here.
Change this file to reskin the entire CLI.
"""

THEME = {
    # ── Colour palette ────────────────────────────────────────────
    "primary":          "bright_white",
    "secondary":        "dim",              # metadata, hints, elapsed
    "accent":           "#00AFFF",          # prompt glyph, highlights
    "success":          "green",
    "warning":          "yellow",
    "error":            "red",

    # ── Source badge colours ───────────────────────────────────────
    "source": {
        "docs":           "#00AFFF",        # cyan
        "github":         "bright_white",
        "stackoverflow":  "yellow",
        "package":        "green",
        "web":            "dim",
        "blogs":          "magenta",
    },

    # ── Source badge labels ────────────────────────────────────────
    "source_labels": {
        "docs":           "docs",
        "github":         "github",
        "stackoverflow":  "stackoverflow",
        "package":        "package",
        "web":            "web",
        "blogs":          "blog",
    },

    # ── Shortcut category colours ─────────────────────────────────
    "category": {
        "git":      "bright_green",
        "docker":   "#00AFFF",
        "ffmpeg":   "bright_yellow",
        "curl":     "bright_magenta",
        "npm":      "red",
        "python":   "blue",
        "general":  "dim",
    },

    # ── Typography rules ──────────────────────────────────────────
    "title_style":      "bold bright_white",
    "index_style":      "dim",
    "url_style":        "dim",
    "snippet_style":    "dim",
    "hint_style":       "dim",
    "tagline_style":    "dim italic",
    "empty_style":      "dim italic",

    # ── Layout constraints ────────────────────────────────────────
    "max_width":        88,
    "indent":           "  ",
    "rule_width_pct":   0.60,          # 60% of max_width
    "snippet_max":      160,

    # ── Prompt ────────────────────────────────────────────────────
    "prompt_glyph":     "❯",
    "prompt_style":     "#00AFFF bold",

    # ── Spinner ───────────────────────────────────────────────────
    "spinner_style":    "dots2",
    "spinner_messages": [
        "searching docs...",
        "checking github...",
        "ranking results...",
    ],

    # ── Banner ────────────────────────────────────────────────────
    "logo": r"""
     _           _
  __| | _____   _| |    ___ _ __  ___
 / _` |/ _ \ \ / / |   / _ \ '_ \/ __|
| (_| |  __/\ V /| |__|  __/ | | \__ \
 \__,_|\___| \_/ |_____\___|_| |_|___/
""",
    "tagline":          "privacy-first search for developers",
}
