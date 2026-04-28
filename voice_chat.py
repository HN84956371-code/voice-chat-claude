"""
Voice Chat with Claude - fully automatic loop
Double-click 語音對話.bat to start
Say '等等' to pause and switch to text input mode
"""

import subprocess
import asyncio
import tempfile
import os
import sys
import re
import speech_recognition as sr
import edge_tts
import pygame

TTS_VOICE = "zh-TW-HsiaoChenNeural"
PAUSE_WORDS = ["等等", "暫停", "等一下", "停一下", "pause", "wait"]

def p(msg):
    print(msg, flush=True)


def text_input_mode():
    """Collect text input until user presses Enter on an empty line or sends a single line."""
    p("\n" + "=" * 50)
    p("  📝 文字輸入模式")
    p("  貼上路徑、文字、指令，按 Enter 送出")
    p("  多行輸入：每行按 Enter，最後空行送出")
    p("  輸入 '取消' 直接回語音模式")
    p("=" * 50)
    lines = []
    while True:
        try:
            line = input(">> ")
        except EOFError:
            break
        if line.strip() == "取消":
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


def listen(recognizer, mic):
    p("\n========== Speak now! ==========")
    with mic as source:
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=60)
        except sr.WaitTimeoutError:
            return None

    p("[Recognizing...]")
    if USE_WHISPER:
        try:
            return recognizer.recognize_whisper(audio, model="base", language="zh")
        except Exception as e:
            p(f"[Whisper error: {e}, trying Google...]")
    try:
        return recognizer.recognize_google(audio, language="zh-TW")
    except sr.UnknownValueError:
        p("[Could not recognize, try again]")
        return None
    except sr.RequestError as e:
        p(f"[STT error: {e}]")
        return None

import shutil

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
PROJECT_DIR = os.environ.get("VOICE_CHAT_PROJECT_DIR", os.getcwd())


def ask_claude(text):
    cmd = [CLAUDE_CMD, "-p", text, "--output-format", "text"]
    result = subprocess.run(cmd, capture_output=True, timeout=120, shell=True, cwd=PROJECT_DIR)
    out = result.stdout.decode("utf-8", errors="replace").strip()
    return out

TTS_MAX_CHARS = 100

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


def speak(text):
    try:
        cleaned = clean_for_tts(text)
        if not cleaned:
            return
        if len(cleaned) > TTS_MAX_CHARS:
            cleaned = cleaned[:TTS_MAX_CHARS] + "……後面還有，請看螢幕"
        tmp = os.path.join(tempfile.gettempdir(), "claude_voice_reply.mp3")
        pygame.mixer.music.unload()
        asyncio.run(edge_tts.Communicate(cleaned, TTS_VOICE, rate="+0%").save(tmp))
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(200)
        pygame.mixer.music.unload()
    except Exception as e:
        p(f"[TTS error: {e}, skipping voice]")

def main():
    p("=" * 50)
    p("  Voice Chat with Claude")
    p("  Speak -> Claude replies -> auto read aloud")
    p("  Say 'bye' or press Ctrl+C to stop")
    p("=" * 50)

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    p("[Calibrating 2 seconds... stay quiet]")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    ambient = recognizer.energy_threshold
    recognizer.energy_threshold = ambient * 0.8
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 2.0
    stt_engine = "Whisper (base)" if USE_WHISPER else "Google STT"
    p(f"[Ambient: {ambient:.0f}, Threshold: {recognizer.energy_threshold:.0f}, STT: {stt_engine}]")

    pygame.mixer.init()

    p("\n[Ready! Say '等等' to switch to text input]")

    while True:
        try:
            text = listen(recognizer, mic)
            if text is None:
                p("[No speech detected, listening again...]")
                continue

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

            p("[Claude thinking...]")
            reply = ask_claude(text)
            if not reply:
                p("[No reply]")
                continue

            p(f"\nClaude: {reply}\n")
            speak(reply)
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
