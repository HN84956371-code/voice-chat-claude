# Voice Chat with Claude

**[繁體中文說明](README.zh-TW.md)** | English

Talk to Claude with your voice. Claude replies are **streamed sentence-by-sentence** — you hear the first sentence in seconds, not after the full response is generated. Say **"wait"** anytime to switch to text input — paste file paths, code, or instructions — then press Enter to return to voice mode automatically.

## What's New in v3.0

- **Haiku model** — defaults to `claude-haiku-4-5-20251001`, 3-5x faster responses
- **Thinking cue** — plays "hmm, let me think..." immediately after hearing you, no more dead silence
- **Streaming TTS** — reads reply sentence-by-sentence as Claude generates, first audio in 2-5 seconds
- **Faster turn detection** — silence threshold reduced from 2.5s to 1.2s

## Features

- **Streaming conversation loop** — speak → thinking cue → Claude streams → sentence-by-sentence TTS → listen again
- **Mixed input** — say "wait" to pause voice and type/paste anything (file paths, code snippets, complex instructions), press Enter to submit, auto-returns to voice
- **Bilingual STT** — Google STT primary, Whisper fallback for English content above 10%
- **Smart TTS** — strips Markdown (tables, bold, code blocks) before speaking; streams each sentence, shows full reply on screen
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

Or on Windows, double-click `語音對話.bat`.

### Voice commands

| You say | What happens |
|---------|-------------|
| *(anything)* | Sent to Claude, reply streamed & read aloud sentence by sentence |
| "wait" / "pause" / "等等" / "暫停" | Switch to text input mode |
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
| `PAUSE_WORDS` | 等等, 暫停, 等一下, ... | Words that trigger text input mode |

## How it works

```
Start → 2s silence calibration → pre-generate thinking cue → [Ready!]
  ↓
Listen (mic) → Google STT (+Whisper fallback) → text
  ↓
Route by keyword:
  ├─ quit word → goodbye → exit
  ├─ pause word → text input mode → submit → stream reply → sentence TTS → voice
  └─ normal → play "hmm, let me think..." → Claude CLI streaming
              → first sentence arrives → start TTS (generate & play in parallel)
              → back to voice
```

**STT:** Google Speech Recognition zh-TW primary. Whisper `base` model fallback when English ratio > 10%.

**TTS:** Microsoft Edge TTS (free, online, high-quality). In streaming mode, each sentence is generated and played as it arrives.

**AI:** Claude Code CLI in streaming mode (`claude -p --output-format stream-json`). Each message is a standalone call.

## License

[MIT](LICENSE)
