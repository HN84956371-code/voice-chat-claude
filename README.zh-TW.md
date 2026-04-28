# Voice Chat with Claude

**繁體中文** | **[English](README.md)**

用語音跟 Claude 對話。Claude 回覆後自動朗讀答案。隨時說**「等等」**切換到文字輸入模式——貼上檔案路徑、程式碼或指令——按 Enter 送出後自動回到語音模式。

## 功能特色

- **語音對話循環** — 說話 → Claude 思考 → 朗讀回覆 → 繼續聆聽
- **混合輸入** — 說「等等」暫停語音，貼上任何內容（檔案路徑、程式碼片段、複雜指令），按 Enter 送出，自動回到語音
- **中英雙語辨識** — Whisper 精準處理中英混合語音（不再把 Opus 聽成 OPPO）
- **智慧朗讀** — 自動去除 Markdown 格式（表格、粗體、程式碼區塊），只朗讀前 100 字，完整回覆顯示在螢幕上
- **輕量設計** — 單一 Python 檔案，無框架依賴

## 前置需求

- **Python 3.10+**
- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** — 已安裝並完成登入（`claude` 指令可在終端機使用）
- **麥克風** — 內建或外接皆可
- **ffmpeg** — Whisper 需要（[安裝指南](https://github.com/openai/whisper#setup)）

## 安裝

```bash
git clone https://github.com/YOUR_USERNAME/voice-chat-claude.git
cd voice-chat-claude
pip install -r requirements.txt
```

### PyAudio 安裝問題排除

PyAudio 在 Windows 上安裝常遇到問題。如果 `pip install PyAudio` 失敗：

```bash
# 方法一：pipwin
pip install pipwin
pipwin install pyaudio

# 方法二：下載 .whl 檔
# 從 https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio 下載對應版本
pip install PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl
```

macOS：`brew install portaudio && pip install pyaudio`

Ubuntu/Debian：`sudo apt install portaudio19-dev && pip install pyaudio`

## 使用方式

```bash
python -u voice_chat.py
```

Windows 使用者也可以雙擊 `start.bat` 啟動。

### 語音指令

| 你說的話 | 程式反應 |
|---------|---------|
| *（任何中文或英文）* | 送至 Claude，朗讀回覆 |
| 「等等」/「暫停」/「等一下」/「停一下」/ "pause" / "wait" | 切換到文字輸入模式 |
| 「結束」/「離開」/「退出」/「關閉」/ "bye" / "exit" | 結束程式 |
| Ctrl+C | 強制結束 |

### 文字輸入模式

說出暫停詞後，畫面會出現 `>>` 提示符號。你可以：

- **貼上檔案路徑** — Claude 會讀取並處理該檔案
- **貼上程式碼片段** — 搭配指令一起送出
- **輸入任何文字指令**
- **多行輸入** — 每行按 Enter，最後打一個空行（直接按 Enter）送出
- **輸入「取消」** — 放棄本次輸入，直接回到語音模式

送出後 Claude 回覆，自動回到語音模式。

## 設定

| 環境變數 | 預設值 | 說明 |
|---------|-------|------|
| `VOICE_CHAT_PROJECT_DIR` | 當前目錄 | Claude CLI 的工作目錄（決定載入哪個專案的記憶） |

### 可調整的程式常數（在 `voice_chat.py` 中）

| 常數 | 預設值 | 說明 |
|------|-------|------|
| `TTS_VOICE` | `zh-TW-HsiaoChenNeural` | Edge TTS 語音（[完整清單](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#text-to-speech)） |
| `TTS_MAX_CHARS` | `100` | 朗讀字數上限（完整回覆仍會顯示在螢幕上） |
| `PAUSE_WORDS` | 等等、暫停、等一下... | 觸發文字輸入模式的關鍵字 |

## 運作原理

```
啟動 → 靜音校準 2 秒 → [Ready!]
  ↓
聆聽（麥克風）→ Whisper 語音辨識 → 文字
  ↓
判斷關鍵字：
  ├─ 結束詞 → 說掰掰 → 結束程式
  ├─ 暫停詞 → 文字輸入模式 → 送出 → Claude → 朗讀 → 回到語音
  └─ 一般語音 → Claude CLI（-p）→ 朗讀前 100 字 → 回到語音
```

**語音辨識（STT）：** Whisper `base` 模型（離線運作，首次使用下載約 140MB）。若未安裝 Whisper，自動退回 Google Speech Recognition。

**語音合成（TTS）：** Microsoft Edge TTS（免費、線上、高品質台灣女聲）。朗讀前會自動清除 Markdown 格式。

**AI 後端：** Claude Code CLI 的 pipe 模式（`claude -p`）。每次送出為獨立呼叫——語音工具本身不維護對話歷史（由 Claude Code 管理上下文）。

## 授權

[MIT](LICENSE)
