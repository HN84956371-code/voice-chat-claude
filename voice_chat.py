"""
Voice Chat with Claude v3.0 — streaming edition
Double-click 語音對話.bat to start
Say '等等' to pause and switch to text input mode

v3.0: Haiku for speed, thinking cue, sentence-by-sentence streaming TTS
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
PAUSE_WORDS = ["等等", "暫停", "等一下", "停一下", "pause", "wait"]
SENTENCE_END = re.compile(r'(?<=[。！？!?\n])')
TTS_CHUNK_MAX = 200

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

VOICE_MODEL = os.environ.get("VOICE_CHAT_MODEL", "claude-haiku-4-5-20251001")


def _make_startupinfo():
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def ask_claude(text):
    cmd = [CLAUDE_CMD, "-p", text, "--output-format", "text",
           "--model", VOICE_MODEL]
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, timeout=180,
            shell=True, cwd=PROJECT_DIR, startupinfo=_make_startupinfo()
        )
        out = result.stdout.decode("utf-8", errors="replace").strip()
        p(f"[Claude replied in {time.time()-t0:.1f}s]")
        return out
    except subprocess.TimeoutExpired:
        p(f"[Claude timed out after {time.time()-t0:.0f}s]")
        return "Sorry, timed out. Please try again or simplify the question."


def _split_sentences(text):
    parts = SENTENCE_END.split(text)
    return [s for s in parts if s.strip()]


# ── TTS ─────────────────────────────────────────────────────

def clean_for_tts(text):
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
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            edge_tts.Communicate(text, TTS_VOICE, rate=rate).save(output_path)
        )
    finally:
        loop.close()


_THINKING_CUE_PATH = os.path.join(tempfile.gettempdir(), "claude_thinking_cue.mp3")


def _ensure_thinking_cue():
    if not os.path.exists(_THINKING_CUE_PATH):
        p("[Generating thinking cue...]")
        _run_tts_to_file("嗯…讓我想想", _THINKING_CUE_PATH, rate="+10%")


def play_thinking_cue():
    try:
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
        tmp = os.path.join(tempfile.gettempdir(), "claude_voice_reply.mp3")
        pygame.mixer.music.unload()
        _run_tts_to_file(cleaned, tmp)
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(200)
        pygame.mixer.music.unload()
    except Exception as e:
        p(f"[TTS error: {e}]")


def ask_and_speak_stream(text):
    t0 = time.time()
    reply = ask_claude(text)
    if not reply:
        stop_thinking_cue()
        return ""

    stop_thinking_cue()
    sentences = _split_sentences(reply)
    p(f"[Speaking {len(sentences)} chunks]")

    for idx, sentence in enumerate(sentences):
        cleaned = clean_for_tts(sentence)
        if not cleaned:
            continue
        if len(cleaned) > TTS_CHUNK_MAX:
            cleaned = cleaned[:TTS_CHUNK_MAX]
        try:
            tmp = os.path.join(tempfile.gettempdir(),
                               f"claude_chunk_{idx % 2}.mp3")
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)
            pygame.mixer.music.unload()

            _run_tts_to_file(cleaned, tmp)
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
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
    p("  Voice Chat with Claude v3.0")
    p("  Streaming TTS + Haiku speed")
    p("  Say 'bye' or Ctrl+C to stop")
    p("=" * 50)

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    p("[Calibrating 2 seconds... stay quiet]")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    ambient = recognizer.energy_threshold
    recognizer.energy_threshold = ambient * 0.8
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

    p("\n[Ready! Say 'wait' to switch to text input]")
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

            quit_words = ["結束", "離開", "退出", "關閉", "bye", "exit", "quit"]
            if any(w in text.lower() for w in quit_words):
                p("\nBye!")
                speak("掰掰，下次再聊！")
                break

            if any(w in text for w in PAUSE_WORDS):
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
                stop_thinking_cue()
                p("[No reply]")
                continue

            p(f"\nClaude: {reply}\n")
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
