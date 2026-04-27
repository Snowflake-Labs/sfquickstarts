author: Chanin Nantasenamat
id: create-shareable-cortex-code-session-replays-with-cortex-replay
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai
language: en
summary: Convert Cortex Code session transcripts into self-contained interactive HTML replays that you can share, embed, and present using cortex-replay.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Create Shareable Cortex Code Session Replays with cortex-replay
<!-- ------------------------ -->
## Overview

Cortex Code is Snowflake's AI coding assistant that helps you write code, query data, and build applications directly from the command line. Every session you run is automatically saved as a JSON transcript on your machine. But what if you want to share a session with a teammate, embed it in documentation, or present it in a talk?

[cortex-replay](https://github.com/dataprofessor/cortex-replay) is a CLI tool that converts those Cortex Code session JSON transcripts into self-contained, interactive HTML replays. Adapted from [claude-replay](https://github.com/es617/claude-replay) by [es617](https://github.com/es617), cortex-replay builds on that foundation with Cortex Code-specific parsing, turn-based navigation, multi-theme support, and automatic secret redaction. The output is a single HTML file with no external dependencies that anyone can open in a browser. It features turn-by-turn navigation, animated playback, syntax-highlighted code blocks, keyboard shortcuts, theme support, and secret redaction.

### What You'll Learn
- How to find and list your Cortex Code session transcripts
- How to generate interactive HTML replays from sessions
- How to use player controls, keyboard shortcuts, and turn navigation
- How to apply built-in and custom themes to style replays
- How to add bookmarks to mark key moments in a session
- How to filter sessions to include only specific turns
- How to redact secrets and sensitive information automatically
- How to embed replays in blogs, documentation, and presentations

### What You'll Build
A fully interactive, self-contained HTML replay of a Cortex Code session that you can open in any browser, share with colleagues, or embed in a webpage. See a [live example](https://dataprofessor.github.io/cortex-replay/).

![](assets/screencast.gif)

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/cortex-code?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) installed and configured
- [Node.js](https://nodejs.org/) v18 or later
- At least one completed Cortex Code session (the tool needs a session transcript to convert)

<!-- ------------------------ -->
## Install cortex-replay

### Install from GitHub

Install cortex-replay globally so it is available as a command anywhere on your system:

```bash
npm install -g github:dataprofessor/cortex-replay
```

Verify the installation by viewing the help:

```bash
cortex-replay --help
```

### Install from Source

If you prefer to install from source or want to contribute:

```bash
git clone https://github.com/dataprofessor/cortex-replay.git
cd cortex-replay
npm install -g .
```

<!-- ------------------------ -->
## Find Your Sessions

Cortex Code automatically saves every session as a JSON file in `~/.snowflake/cortex/conversations/`. Each file is named with a unique session ID. A special `.last-session` file points to the most recently used session.

### List Available Sessions

To see all available sessions with their IDs, dates, and turn counts:

```bash
cortex-replay --list-sessions
```

This scans your conversations directory and displays a table of sessions. Use this to find the session ID you want to replay.

### Locate a Specific Session

Each session file follows the naming pattern:

```
~/.snowflake/cortex/conversations/<session-id>.json
```

You can also point cortex-replay at any JSON file directly by passing the file path as the first argument (covered in the next section).

<!-- ------------------------ -->
## Generate a Replay

### Basic Usage

Generate a replay by passing a session ID (from `--list-sessions`) as the first argument. You don't need the full UUID — the first 4–6 characters are usually enough for cortex-replay to find a unique match:

```bash
cortex-replay 6868f -o replay.html
```

Here `6868f` is the first 5 characters of the full session ID `6868f059-3b8a-423d-8a51-ef0397c7f469`. That's all cortex-replay needs to find a unique match.

By default, cortex-replay outputs to stdout. Use `-o` to write to a file.

### Specify Output Path

Control where the HTML file is saved:

```bash
cortex-replay 6868f -o ~/Desktop/my-replay.html
```

### Use a Custom Input File

If your session JSON is not in the default Cortex Code directory, pass the file path directly as the first argument:

```bash
cortex-replay /path/to/session.json -o replay.html
```

### Add a Custom Title

Override the default title shown in the replay header:

```bash
cortex-replay 6868f --title "Building a Data Pipeline"
```

### View the Replay

Open the generated HTML file in any browser. You can double-click the file in your file manager, open it from the terminal, or copy-paste the file path into your browser's address bar:

```bash
open replay.html
```

The replay is fully self-contained with all CSS, JavaScript, and session data inlined into a single file. No server or internet connection is needed — it works directly from your filesystem.

<!-- ------------------------ -->
## Navigate the Player

The generated HTML replay is a fully interactive player. Here is how to navigate it.

### Player Controls

The player has a control bar at the bottom of the screen with these controls:

| Control | Description |
|---------|-------------|
| Previous/Next buttons | Step backward or forward one block at a time |
| Turn Previous/Next buttons | Jump to the previous or next turn |
| Play/Pause button | Start or stop auto-playback |
| Speed selector | Choose playback speed (0.5x, 1x, 1.5x, 2x, 3x, 5x) |
| Progress bar | Multi-colored segmented bar showing your position; click to jump |

### Keyboard Shortcuts

The player supports keyboard navigation:

| Key | Action |
|-----|--------|
| `Space` or `k` | Play / Pause |
| `Right Arrow` or `l` | Next turn |
| `Left Arrow` or `h` | Previous turn |

### Turn Highlighting

Each turn in the replay has a unique color. As you navigate or scroll, the active turn is highlighted at full opacity with a colored left border and glow effect. Previous turns are shown at reduced opacity, and future turns are dimmed. The multi-colored progress bar at the bottom reflects these turn colors, so you can see the session structure at a glance.

### Scroll-Based Navigation

You can also navigate by simply scrolling. The player automatically detects which turn you are viewing and updates the progress bar and highlighting to match. This works seamlessly with both tall turns that fill the viewport and short single-line turns.

<!-- ------------------------ -->
## Apply Themes

cortex-replay includes six built-in themes and supports fully custom themes.

### Built-in Themes

Apply a theme with the `--theme` flag:

```bash
cortex-replay 6868f --theme tokyo-night
```

Available built-in themes:

| Theme | Description |
|-------|-------------|
| `snowflake` | Default Snowflake brand colors (dark blue background) |
| `tokyo-night` | Popular dark theme with vibrant accents |
| `monokai` | Classic warm dark theme |
| `solarized-dark` | Ethan Schoonover's precision dark palette |
| `github-light` | Clean light theme matching GitHub's style |
| `dracula` | Popular dark theme with purple and pink accents |

### Custom Themes

Create a JSON file with any combination of the 16 CSS variables:

```json
{
  "bg": "#1a1b26",
  "bg-surface": "#24283b",
  "bg-hover": "#2f3349",
  "text": "#c0caf5",
  "text-dim": "#565f89",
  "text-bright": "#ffffff",
  "accent": "#7aa2f7",
  "accent-dim": "#3d59a1",
  "green": "#9ece6a",
  "blue": "#7aa2f7",
  "orange": "#ff9e64",
  "red": "#f7768e",
  "cyan": "#7dcfff",
  "border": "#3b4261",
  "tool-bg": "#1f2335",
  "thinking-bg": "#1a1b2e"
}
```

You only need to include the variables you want to override. Apply it with:

```bash
cortex-replay 6868f --theme-file my-theme.json
```

<!-- ------------------------ -->
## Add Bookmarks

Bookmarks let you mark key moments in a session so viewers can jump directly to them. This is useful for long sessions where you want to highlight important steps.

### Define Bookmarks

Pass bookmark labels keyed to turn numbers using the `--mark` flag:

```bash
cortex-replay 6868f \
  --mark "1:Setup" \
  --mark "5:Data Loading" \
  --mark "12:Model Training" \
  --mark "18:Results"
```

The format is `turn_number:label`. Turn numbers are 1-based.

### Using Bookmarks in the Player

Bookmarks appear as a dropdown menu in the player controls. Click any bookmark to jump directly to that turn. This is especially valuable for sessions with dozens of turns where you want to guide viewers to the highlights.

<!-- ------------------------ -->
## Filter Turns

For long sessions, you may want to include only a subset of turns in the replay.

### Select Specific Turns

Use the `--turns` flag to include a range of turns (1-based):

```bash
cortex-replay 6868f --turns 5-15
```

This includes turns 5 through 15 in the replay.

### Practical Use Cases

Filtering is useful when you want to:
- Extract a specific workflow from a long exploratory session
- Remove false starts or tangential conversations
- Create a focused tutorial from a longer session
- Reduce file size for embedding

<!-- ------------------------ -->
## Redact Secrets

cortex-replay automatically scans session content for sensitive information and redacts it before generating the HTML.

### Automatic Redaction

By default, the tool detects and replaces the following categories of secrets:

| Pattern | Example |
|---------|---------|
| Private keys | `-----BEGIN RSA PRIVATE KEY-----` |
| AWS access keys | `AKIAIOSFODNN7EXAMPLE` |
| Anthropic API keys | `sk-ant-api03-...` |
| OpenAI / generic sk- keys | `sk-proj-...`, `sk-...` |
| Generic key- prefixed secrets | `key-abcdef...` |
| Bearer tokens | `Authorization: Bearer ...` |
| JWT / PAT tokens | `eyJhbGciOiJ...eyJzdWIi...` |
| Connection strings | `postgres://user:pass@host/db`, `snowflake://...` |
| Snowflake tokens | `masterToken=...`, `sessionToken=...` |
| Key-value secrets | `password=...`, `api_key=...`, `secret_key=...` |
| Environment variables | `PASSWORD=...`, `TOKEN=...`, `SNOWFLAKE_PASSWORD=...` |
| Hex tokens | 40+ character hexadecimal strings |

Each detected secret is replaced with `[REDACTED]` in the output.

### Skip Redaction

If you are working in a controlled environment and want to skip the redaction step:

```bash
cortex-replay 6868f --no-redact
```

Use this with caution. Always review the output before sharing if you skip redaction.

<!-- ------------------------ -->
## Customize Output

### Set Playback Speed

Override the default playback speed multiplier:

```bash
cortex-replay 6868f --speed 2
```

The default is 1.0. Higher values mean faster auto-playback.

### Include Session Metadata

The replay header automatically shows the session ID. When combined with `--title`, both the custom title and session ID are displayed.

### Combine Options

All options can be combined freely:

```bash
cortex-replay 6868f \
  --title "Building a RAG Pipeline" \
  --theme tokyo-night \
  --turns 1-20 \
  --mark "1:Setup" \
  --mark "8:Indexing" \
  --mark "15:Querying" \
  --speed 2 \
  -o rag-pipeline-replay.html
```

<!-- ------------------------ -->
## Embed Replays

The generated HTML is a single self-contained file with no external dependencies, making it straightforward to embed in other contexts.

### Embed in a Webpage

Use an iframe to embed the replay in any HTML page:

```html
<iframe
  src="my-replay.html"
  width="100%"
  height="700"
  style="border: 1px solid #ccc; border-radius: 8px;"
></iframe>
```

### Embed in Documentation

For documentation platforms that support HTML embedding (e.g., Notion, Confluence, GitHub Pages), upload the HTML file and reference it via iframe or direct link.

### Share Directly

Since the output is a single HTML file with everything inlined (CSS, JavaScript, content), you can share it through any channel:

- Attach to an email or Slack message
- Upload to cloud storage and share a link
- Host on GitHub Pages or any static file host
- Include in a ZIP alongside other project artifacts

<!-- ------------------------ -->
## CLI Reference

Here is the complete list of all cortex-replay CLI options:

| Flag | Description |
|------|-------------|
| `<session-id>` | Partial session ID to look up (positional argument) |
| `-o, --output FILE` | Output HTML file (default: stdout) |
| `--last` | Use the most recent session |
| `--list-sessions` | List available sessions and exit |
| `--session-dir DIR` | Session directory (default: `~/.snowflake/cortex/conversations`) |
| `--turns N-M` | Only include turns N through M |
| `--from TIMESTAMP` | Start time filter (ISO 8601) |
| `--to TIMESTAMP` | End time filter (ISO 8601) |
| `--speed N` | Initial playback speed multiplier (default: 1.0) |
| `--title TEXT` | Page title (default: from session title) |
| `--no-thinking` | Hide thinking blocks by default |
| `--no-tool-calls` | Hide tool call blocks by default |
| `--no-redact` | Skip automatic secret redaction |
| `--theme NAME` | Built-in theme (default: snowflake) |
| `--theme-file FILE` | Custom theme JSON file |
| `--mark "N:Label"` | Add a bookmark at turn N (repeatable) |
| `--bookmarks FILE` | JSON file with bookmarks `[{turn, label}]` |
| `--user-label NAME` | Label for user messages (default: User) |
| `--assistant-label NAME` | Label for assistant messages (default: Cortex Code) |
| `--no-compress` | Embed raw JSON instead of compressed |
| `--list-themes` | List available built-in themes and exit |
| `-h, --help` | Show help |

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully learned how to convert Cortex Code sessions into interactive HTML replays using cortex-replay. You can now generate shareable replays, navigate them with keyboard shortcuts and player controls, apply themes, add bookmarks, filter turns, and embed replays in your documentation and presentations.

### What You Learned
- How to install cortex-replay and find your Cortex Code session transcripts
- How to generate self-contained HTML replays with custom titles and output paths
- How to navigate replays using player controls, keyboard shortcuts, and scrolling
- How to apply built-in themes and create custom themes with 16 CSS variables
- How to add bookmarks for quick navigation in long sessions
- How to filter specific turns to create focused replays
- How automatic secret redaction protects sensitive information
- How to embed and share replays across different platforms

### Related Resources

Documentation:
- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
- [cortex-replay on GitHub](https://github.com/dataprofessor/cortex-replay)
- [Live Demo](https://dataprofessor.github.io/cortex-replay/)

Acknowledgments:
- [claude-replay](https://github.com/es617/claude-replay) by [es617](https://github.com/es617) - The original project that cortex-replay was adapted from
