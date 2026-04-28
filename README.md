# Voice Chat with Claude

**[繁體中文說明](README.zh-TW.md)** | English

Talk to Claude with your voice. Claude replies and reads the answer aloud. Say **"wait"** anytime to switch to text input — paste file paths, code, or instructions — then press Enter to return to voice mode automatically.

## Features

- **Voice conversation loop** — speak → Claude thinks → reads reply aloud → listens again
- **Mixed input** — say "wait" to pause voice and type/paste anything (file paths, code snippets, complex instructions), press Enter to submit, auto-returns to voice
- **Bilingual STT** — Whisper handles Chinese + English mixed speech accurately
- **Smart TTS** — strips Markdown (tables, bold, code blocks) before speaking; reads first 100 chars, shows full reply on screen
- **Lightweight** — single Python file, no framework

## Prerequisites

- **Python 3.10+**
- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** — installed and authenticated (`claude` available in PATH)
- **Microphone** — built-in or external
- **ffmpeg** — required by Whisper ([install guide](https://github.com/openai/whisper#setup))

## Install

```bash
git clone https://github.com/YOUR_USERNAME/voice-chat-claude.git
cd voice-chat-claude
pip install -r requirements.txt
```

### PyAudio troubleshooting

PyAudio can be tricky to install on Windows. If `pip install PyAudio` fails:

```bash
# Option 1: pipwin
pip install pipwin
pipwin install pyaudio

# Option 2: download .whl from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl
```

On macOS: `brew install portaudio && pip install pyaudio`

On Ubuntu/Debian: `sudo apt install portaudio19-dev && pip install pyaudio`

## Usage

```bash
python -u voice_chat.py
```

Or on Windows, double-click `start.bat` (create your own from the example below).

### Voice commands

| You say | What happens |
|---------|-------------|
| *(anything)* | Sent to Claude, reply read aloud |
| "wait" / "pause" / "等等" / "暫停" | Switch to text input mode |
| "bye" / "exit" / "結束" / "離開" | End session |
| Ctrl+C | Force quit |

### Text input mode

When you say a pause word, a `>>` prompt appears. You can:

- Paste a file path — Claude will read and process it
- Paste code snippets with instructions
- Type any text command
- Multi-line: press Enter after each line, then an empty line to submit
- Type `取消` (cancel) to go back to voice without sending

After submitting, Claude replies and you're back in voice mode.

## Configuration

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `VOICE_CHAT_PROJECT_DIR` | Current directory | Working directory for Claude CLI (determines which project memory is loaded) |

### Tunable constants in `voice_chat.py`

| Constant | Default | Description |
|----------|---------|-------------|
| `TTS_VOICE` | `zh-TW-HsiaoChenNeural` | Edge TTS voice ([list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#text-to-speech)) |
| `TTS_MAX_CHARS` | `100` | Max characters read aloud (full reply always shown on screen) |
| `PAUSE_WORDS` | 等等, 暫停, 等一下, ... | Words that trigger text input mode |

## How it works

```
Start → 2s silence calibration → [Ready!]
  ↓
Listen (mic) → Whisper STT → text
  ↓
Route by keyword:
  ├─ quit word → goodbye → exit
  ├─ pause word → text input mode → submit → Claude → TTS → back to voice
  └─ normal → Claude CLI (-p) → TTS (first 100 chars) → back to voice
```

**STT:** Whisper `base` model (offline, ~140MB download on first run). Falls back to Google Speech Recognition if Whisper is not installed.

**TTS:** Microsoft Edge TTS (free, online, high-quality). Markdown is stripped before speaking.

**AI:** Claude Code CLI in pipe mode (`claude -p`). Each message is a standalone call — no conversation history is maintained in the voice tool itself (Claude Code manages its own context).

## License

[MIT](LICENSE)
