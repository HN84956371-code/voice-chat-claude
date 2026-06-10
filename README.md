# Voice Chat with Claude

**[繁體中文說明](README.zh-TW.md)** | English

Talk to Claude with your voice. Claude replies are read aloud **sentence-by-sentence** — you see the full text first, then hear it spoken one sentence at a time. Say **"wait"**, **"打字"**, or **"等等"** anytime to switch to text input — paste file paths, code, or instructions — then press Enter to return to voice mode automatically.

## What's New in v3.2.1

- **Haiku model** — defaults to `claude-haiku-4-5-20251001`, 3-5x faster responses
- **Thinking cue** — plays "hmm, let me think..." immediately after hearing you, no more dead silence
- **Sentence-by-sentence TTS** — splits reply into sentences and reads each aloud in sequence
- **Voice-optimized replies** — system prompt tells Claude to use spoken Chinese, no emoji, no Markdown
- **Safer command detection** — only short voice phrases (≤10 chars) trigger quit/pause; typed text never triggers commands
- **Faster turn detection** — silence threshold reduced from 2.5s to 1.2s

## Features

- **Conversation loop** — speak → thinking cue → Claude replies → sentence-by-sentence TTS → listen again
- **Mixed input** — say "等等" / "打字" / "暫停" to pause voice and type/paste anything (file paths, code snippets, complex instructions), press Enter to submit, auto-returns to voice
- **Bilingual STT** — Google STT primary, Whisper fallback for English content above 35%
- **Smart TTS** — strips Markdown, emoji, and formatting before speaking; plays each sentence, shows full reply on screen
- **Lightweight** — single Python file, no framework

## Prerequisites

- **Python 3.10+**
- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** — installed and authenticated (`claude` available in PATH)
- **Microphone** — built-in or external
- **ffmpeg** — required by Whisper ([install guide](https://github.com/openai/whisper#setup))

## Install

```bash
git clone https://github.com/HN84956371-code/voice-chat-claude.git
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

Or on Windows, double-click `start.bat`.

### Voice commands

| You say | What happens |
|---------|-------------|
| *(anything)* | Sent to Claude, reply read aloud sentence by sentence |
| "等等" / "打字" / "暫停" / "wait" / "pause" | Switch to text input mode |
| "bye" / "exit" / "結束" / "離開" | End session |
| Ctrl+C | Force quit |

### Text input mode

When you say a pause word, a `>>` prompt appears. You can:

- Paste a file path — Claude will read and process it
- Paste code snippets with instructions
- Type any text command
- Multi-line: press Enter after each line, then an empty line to submit
- Type `cancel` or `取消` to go back to voice without sending

After submitting, Claude replies and you're back in voice mode.

## Configuration

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `VOICE_CHAT_PROJECT_DIR` | Current directory | Working directory for Claude CLI (determines which project memory is loaded) |
| `VOICE_CHAT_MODEL` | `claude-haiku-4-5-20251001` | Claude model (can override to opus/sonnet) |

### Tunable constants in `voice_chat.py`

| Constant | Default | Description |
|----------|---------|-------------|
| `TTS_VOICE` | `zh-TW-HsiaoChenNeural` | Edge TTS voice ([list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#text-to-speech)) |
| `TTS_CHUNK_MAX` | `200` | Max characters per TTS chunk |
| `PAUSE_RE` | 等等, 暫停, 打字, 貼上, ... | Words that trigger text input mode (voice ≤10 chars only) |

## How it works

```
Start → 2s silence calibration → pre-generate thinking cue → [Ready!]
  ↓
Listen (mic) → Google STT (+Whisper fallback) → text
  ↓
Route by keyword (voice ≤10 chars only, typed text skips this):
  ├─ quit word → goodbye → exit
  ├─ pause word → text input mode → submit → reply → sentence TTS → voice
  └─ normal → play "hmm, let me think..." → Claude CLI (text mode)
              → get full reply → split into sentences → TTS each → back to voice
```

**STT:** Google Speech Recognition zh-TW primary. Whisper `base` model fallback when English ratio > 35%.

**TTS:** Microsoft Edge TTS (free, online, high-quality). Each sentence is generated and played in sequence.

**AI:** Claude Code CLI in text mode (`claude -p --output-format text`). A voice system prompt is prepended to ensure spoken-friendly replies (no emoji, no Markdown). Each message is a standalone call.

## License

[MIT](LICENSE)
