"""
Voice Chat with Claude v3.2
Double-click start.bat to start
Say '等等' / '打字' / '暫停' to pause and switch to text input mode
"""

import subprocess
import asyncio
import tempfile
import os
import sys
import re
import time
import shutil
import speech_recognition as sr
import edge_tts
import pygame

TTS_VOICE = "zh-TW-HsiaoChenNeural"
SENTENCE_END = re.compile(r'(?<=[。！？!?\n])')
COMMA_SPLIT = re.compile(r'(?<=[，、；,;])')
TTS_CHUNK_MAX = 200
QUIT_RE = re.compile(r'結束|離開|退出|關閉|\b(bye|exit|quit)\b', re.I)
PAUSE_RE = re.compile(
    r'等等|暫停|等一下|停一下|等一等|停一停|打字|用打的|文字模式|我要貼|貼上'
    r'|\b(pause|wait|type|text)\b', re.I)

VOICE_SYSTEM_PROMPT = (
    "[語音對話模式] 你的回覆會被 TTS 朗讀出來。規則："
    "1) 絕對不要用 emoji 或表情符號（👏😄❤️等全部禁止）"
    "2) 不要用 Markdown 格式（不要用 **粗體**、# 標題、- 列表）"
    "3) 用口語化的繁體中文，像在跟朋友聊天一樣"
    "4) 想表達開心就說「哈哈」，想鼓掌就說「太棒了」，用語氣詞不用符號"
    "5) 回覆簡潔有重點，適合用聽的，不要太長"
)

def p(msg):
    print(msg, flush=True)


def text_input_mode():
    p("\n" + "=" * 50)
    p("  text input mode")
    p("  paste text/path/command, Enter to send")
    p("  multi-line: Enter after each line, empty line to submit")
    p("  type 'cancel' to go back to voice")
    p("=" * 50)
    lines = []
    while True:
        try:
            line = input(">> ")
        except EOFError:
            break
        if line.strip() in ("取消", "cancel"):
            return None
        if line == "" and lines:
            break
        if line == "" and not lines:
            continue
        lines.append(line)
    return "\n".join(lines) if lines else None


USE_WHISPER = False
try:
    import whisper as _whisper_check
    USE_WHISPER = True
    del _whisper_check
except ImportError:
    pass


def _english_ratio(text):
    if not text:
        return 0
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    return ascii_letters / len(text)


def listen(recognizer, mic):
    p("\n========== Speak now! ==========")
    with mic as source:
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=90)
        except sr.WaitTimeoutError:
            return None

    t0 = time.time()
    p("[Recognizing...]")

    zh_text = None
    try:
        zh_text = recognizer.recognize_google(audio, language="zh-TW")
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        p(f"[STT error: {e}]")
        return None
    p(f"[Google STT: {time.time()-t0:.1f}s]")

    if zh_text and _english_ratio(zh_text) > 0.1 and USE_WHISPER:
        t1 = time.time()
        p(f"[EN ratio {_english_ratio(zh_text):.0%}, Whisper re-checking...]")
        try:
            en_text = recognizer.recognize_whisper(audio, model="base", language="en")
            if en_text and en_text.strip():
                p(f"[Whisper EN: {en_text.strip()} ({time.time()-t1:.1f}s)]")
                return f"{zh_text}（英文部分：{en_text.strip()}）"
        except Exception as e:
            p(f"[Whisper fallback failed: {e}]")

    if zh_text:
        return zh_text

    try:
        return recognizer.recognize_google(audio, language="en-US")
    except sr.UnknownValueError:
        p("[Could not recognize, try again]")
        return None
    except sr.RequestError:
        return None


# ── Claude CLI ──────────────────────────────────────────────

def _find_claude_cmd():
    found = shutil.which("claude")
    if found:
        return found
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        candidate = os.path.join(appdata, "npm", "claude.cmd")
        if os.path.isfile(candidate):
            return candidate
    return "claude"


CLAUDE_CMD = _find_claude_cmd()
_script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.environ.get("VOICE_CHAT_PROJECT_DIR",
                             os.path.join(_script_dir, "voice_project"))
os.makedirs(PROJECT_DIR, exist_ok=True)

VOICE_MODEL = os.environ.get("VOICE_CHAT_MODEL", "claude-haiku-4-5-20251001")


def _make_startupinfo():
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def ask_claude(text):
    cmd = [CLAUDE_CMD, "-p", "--output-format", "text",
           "--model", VOICE_MODEL]
    prompt = VOICE_SYSTEM_PROMPT + "\n\n" + text
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd, input=prompt.encode("utf-8"), capture_output=True,
            timeout=180, cwd=PROJECT_DIR, startupinfo=_make_startupinfo()
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip()
            p(f"[Claude CLI error {result.returncode}: {err[:300]}]")
            return ""
        out = result.stdout.decode("utf-8", errors="replace").strip()
        p(f"[Claude replied in {time.time()-t0:.1f}s]")
        return out
    except FileNotFoundError:
        p("[claude CLI not found]")
        return ""
    except subprocess.TimeoutExpired:
        p(f"[Claude timed out after {time.time()-t0:.0f}s]")
        return ""


def _split_sentences(text):
    parts = SENTENCE_END.split(text)
    return [s for s in parts if s.strip()]


# ── TTS ─────────────────────────────────────────────────────

_EMOJI_RE = re.compile(
    "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F\U0000200D]+")


def clean_for_tts(text):
    text = _EMOJI_RE.sub('', text)
    text = re.sub(r'\|[^\n]*\|', '', text)
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_`|>#~]', '', text)
    text = re.sub(r'\n{2,}', '。', text)
    text = re.sub(r'\n', '，', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def _run_tts_to_file(text, output_path, rate="+0%"):
    asyncio.run(
        edge_tts.Communicate(text, TTS_VOICE, rate=rate).save(output_path)
    )


_PID = os.getpid()
_THINKING_CUE_PATH = os.path.join(tempfile.gettempdir(),
                                   f"claude_thinking_cue_{_PID}.mp3")


def _ensure_thinking_cue():
    if os.path.exists(_THINKING_CUE_PATH) and os.path.getsize(_THINKING_CUE_PATH) > 0:
        return
    p("[Generating thinking cue...]")
    try:
        tmp = _THINKING_CUE_PATH + ".tmp"
        _run_tts_to_file("嗯…讓我想想", tmp, rate="+10%")
        os.replace(tmp, _THINKING_CUE_PATH)
    except Exception as e:
        p(f"[Thinking cue failed (non-fatal): {e}]")


def play_thinking_cue():
    try:
        if not os.path.exists(_THINKING_CUE_PATH):
            return
        pygame.mixer.music.load(_THINKING_CUE_PATH)
        pygame.mixer.music.play()
    except Exception:
        pass


def stop_thinking_cue():
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        pass


def speak(text):
    try:
        cleaned = clean_for_tts(text)
        if not cleaned:
            return
        if len(cleaned) > TTS_CHUNK_MAX:
            cleaned = cleaned[:TTS_CHUNK_MAX]
        tmp = os.path.join(tempfile.gettempdir(),
                           f"claude_voice_reply_{_PID}.mp3")
        pygame.mixer.music.unload()
        _run_tts_to_file(cleaned, tmp)
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(200)
        pygame.mixer.music.unload()
    except Exception as e:
        p(f"[TTS error: {e}]")


def _play_tts_chunk(cleaned, idx):
    tmp = os.path.join(tempfile.gettempdir(),
                       f"claude_chunk_{_PID}_{idx % 2}.mp3")
    _run_tts_to_file(cleaned, tmp)
    while pygame.mixer.music.get_busy():
        pygame.time.wait(50)
    pygame.mixer.music.unload()
    pygame.mixer.music.load(tmp)
    pygame.mixer.music.play()


def ask_and_speak_stream(text):
    t0 = time.time()
    reply = ask_claude(text)
    stop_thinking_cue()
    if not reply:
        return ""

    p(f"\nClaude: {reply}\n")

    sentences = _split_sentences(reply)
    p(f"[Speaking {len(sentences)} chunks]")

    idx = 0
    for sentence in sentences:
        cleaned = clean_for_tts(sentence)
        if not cleaned:
            continue
        if len(cleaned) > TTS_CHUNK_MAX:
            subs = [s for s in COMMA_SPLIT.split(cleaned) if s.strip()]
            if not subs:
                subs = [cleaned[:TTS_CHUNK_MAX]]
        else:
            subs = [cleaned]
        for sub in subs:
            if not sub.strip():
                continue
            try:
                _play_tts_chunk(sub.strip(), idx)
                idx += 1
            except Exception as e:
                p(f"[TTS chunk error: {e}]")

    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)
    try:
        pygame.mixer.music.unload()
    except Exception:
        pass

    return reply


# ── Main ────────────────────────────────────────────────────

def main():
    p("=" * 50)
    p("  Voice Chat with Claude v3.2")
    p("  Sentence TTS + Haiku speed")
    p("  Say 'bye' or Ctrl+C to stop")
    p("  Say '等等'/'打字'/'暫停' to type/paste")
    p("=" * 50)

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    p("[Calibrating 2 seconds... stay quiet]")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    ambient = recognizer.energy_threshold
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.2
    recognizer.non_speaking_duration = 1.0
    recognizer.phrase_threshold = 0.3
    stt_engine = ("Google zh-TW + Whisper EN fallback" if USE_WHISPER
                  else "Google STT (zh+en)")
    p(f"[Ambient: {ambient:.0f}, Threshold: {recognizer.energy_threshold:.0f},"
      f" STT: {stt_engine}]")
    p(f"[Pause: {recognizer.pause_threshold}s | Model: {VOICE_MODEL}]")

    pygame.mixer.init()
    _ensure_thinking_cue()

    p("\n[Ready! Say '等等'/'打字'/'暫停' to switch to text input]")
    p("[Auto text mode after 3 silent rounds]")

    silent_count = 0
    MAX_SILENT = 3

    while True:
        try:
            text = listen(recognizer, mic)
            if text is None:
                silent_count += 1
                p(f"[No speech detected ({silent_count}/{MAX_SILENT})]")
                if silent_count >= MAX_SILENT:
                    p("\n[Auto switching to text mode]")
                    typed = text_input_mode()
                    silent_count = 0
                    if typed is None:
                        p("[Back to voice mode]")
                        speak("好，繼續說")
                        continue
                    p(f"\n[Text input]: {typed}")
                    text = typed
                else:
                    continue
            else:
                silent_count = 0

            p(f"\nYou: {text}")

            if QUIT_RE.search(text):
                p("\nBye!")
                speak("掰掰，下次再聊！")
                break

            if PAUSE_RE.search(text):
                speak("好，你打字給我看")
                typed = text_input_mode()
                if typed is None:
                    p("[Cancelled, back to voice]")
                    speak("好，繼續說")
                    continue
                p(f"\n[Text input]: {typed}")
                text = typed

            play_thinking_cue()
            p("[Claude thinking...]")

            t0 = time.time()
            reply = ask_and_speak_stream(text)
            p(f"[Total: {time.time()-t0:.1f}s]")

            if not reply:
                p("[No reply]")
                continue

            p("[Back to voice mode]")

        except KeyboardInterrupt:
            p("\n\nStopped.")
            break
        except Exception as e:
            p(f"\n[Error: {e}]")
            continue

    pygame.mixer.quit()


if __name__ == "__main__":
    main()
