# Voice Chat with Claude

**繁體中文** | **[English](README.md)**

用語音跟 Claude 對話。Claude 回覆後**逐句朗讀**，完整文字先顯示在螢幕上，再一句一句唸給你聽。隨時說**「等等」**、**「打字」**或**「暫停」**切換到文字輸入模式——貼上檔案路徑、程式碼或指令——按 Enter 送出後自動回到語音模式。

## v3.2.1 更新

- **Haiku 模型** — 預設改用 `claude-haiku-4-5-20251001`，回覆速度快 3-5 倍
- **思考提示音** — 收到語音後立刻播放「嗯…讓我想想」，不再乾等
- **逐句 TTS** — 回覆拆句後依序朗讀，完整回覆同時顯示在螢幕上
- **語音優化回覆** — 系統提示詞要求 Claude 用口語中文，不用 emoji、不用 Markdown
- **更安全的指令偵測** — 只有短語音（≤10字）觸發退出/暫停；打字內容不會誤觸指令
- **更快的語音偵測** — 靜默閾值從 2.5 秒降到 1.2 秒

## 功能特色

- **對話循環** — 說話 → 思考提示音 → Claude 回覆 → 逐句朗讀 → 繼續聆聽
- **混合輸入** — 說「等等」/「打字」/「暫停」暫停語音，貼上任何內容（檔案路徑、程式碼片段、複雜指令），按 Enter 送出，自動回到語音
- **中英雙語辨識** — Google STT 為主，英文比例 >35% 時 Whisper 補判
- **智慧朗讀** — 自動去除 Markdown 格式、emoji 和表情符號，逐句播放，完整回覆顯示在螢幕上
- **輕量設計** — 單一 Python 檔案，無框架依賴

## 前置需求

- **Python 3.10+**
- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** — 已安裝並完成登入（`claude` 指令可在終端機使用）
- **麥克風** — 內建或外接皆可
- **ffmpeg** — Whisper 需要（[安裝指南](https://github.com/openai/whisper#setup)）

## 安裝

```bash
git clone https://github.com/HN84956371-code/voice-chat-claude.git
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
| *（任何中文或英文）* | 送至 Claude，逐句朗讀回覆 |
| 「等等」/「打字」/「暫停」/「貼上」/ "pause" / "wait" | 切換到文字輸入模式（語音≤10字才觸發） |
| 「結束」/「離開」/「退出」/「關閉」/ "bye" / "exit" | 結束程式 |
| Ctrl+C | 強制結束 |

### 文字輸入模式

說出暫停詞後，畫面會出現 `>>` 提示符號。你可以：

- **貼上檔案路徑** — Claude 會讀取並處理該檔案
- **貼上程式碼片段** — 搭配指令一起送出
- **輸入任何文字指令**
- **多行輸入** — 每行按 Enter，最後打一個空行（直接按 Enter）送出
- **輸入「取消」或「cancel」** — 放棄本次輸入，直接回到語音模式

送出後 Claude 回覆，自動回到語音模式。

## 設定

| 環境變數 | 預設值 | 說明 |
|---------|-------|------|
| `VOICE_CHAT_PROJECT_DIR` | `voice_project/` | Claude CLI 的工作目錄（決定載入哪個專案的記憶） |
| `VOICE_CHAT_MODEL` | `claude-haiku-4-5-20251001` | Claude 模型（可改為 opus/sonnet） |

### 可調整的程式常數（在 `voice_chat.py` 中）

| 常數 | 預設值 | 說明 |
|------|-------|------|
| `TTS_VOICE` | `zh-TW-HsiaoChenNeural` | Edge TTS 語音（[完整清單](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#text-to-speech)） |
| `TTS_CHUNK_MAX` | `200` | 每段朗讀字數上限 |
| `PAUSE_RE` | 等等、暫停、打字、貼上... | 觸發文字輸入模式的關鍵字（語音≤10字才觸發） |

## 運作原理

```
啟動 → 靜音校準 2 秒 → 預生成思考提示音 → [Ready!]
  ↓
聆聽（麥克風）→ Google STT（+Whisper 補判）→ 文字
  ↓
判斷關鍵字（僅語音≤10字，打字內容跳過）：
  ├─ 結束詞 → 說掰掰 → 結束程式
  ├─ 暫停詞 → 文字輸入模式 → 送出 → 回覆 → 逐句朗讀 → 回到語音
  └─ 一般語音 → 播放「嗯…讓我想想」→ Claude CLI（文字模式）
                 → 取得完整回覆 → 拆句 → 逐句 TTS → 回到語音
```

**語音辨識（STT）：** Google Speech Recognition zh-TW 為主。英文比例 >35% 時 Whisper `base` 模型補判。

**語音合成（TTS）：** Microsoft Edge TTS（免費、線上、高品質台灣女聲）。回覆拆句後逐句生成播放。

**AI 後端：** Claude Code CLI 文字模式（`claude -p --output-format text`）。每次呼叫帶語音系統提示詞（禁 emoji、禁 Markdown、口語化回覆）。每次送出為獨立呼叫。

## 授權

[MIT](LICENSE)
