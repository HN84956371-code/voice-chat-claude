# Weekly Maintenance Report — 2026-09-01

## Section 1: Dependency Check

| Package | Pinned Minimum | Latest on PyPI | Status |
|---|---|---|---|
| SpeechRecognition | >=3.10 | 3.17.0 | ✅ Compatible |
| PyAudio | >=0.2.14 | 0.2.14 | ✅ Up to date |
| edge-tts | >=6.1 | **7.2.8** | ⚠️ **Major version bump** |
| pygame | >=2.5 | 2.6.1 | ✅ Compatible |
| openai-whisper | >=20231117 | 20250625 | ✅ Compatible (newer snapshot available) |
| soundfile | >=0.12 | 0.14.0 | ✅ Compatible |

### Action required

- **edge-tts 6.x → 7.x**: A major version was released. The `>=6.1` pin allows installing 7.x, which may include breaking API changes. Recommend testing with `edge-tts==7.2.8` and pinning an upper bound (e.g. `edge-tts>=6.1,<8`) until the changelog has been reviewed and compatibility confirmed.

### Security audit

`pip-audit` is not installed in this environment. To run locally:
```
pip install pip-audit && pip-audit -r requirements.txt
```
No advisories were surfaced via PyPI metadata queries.

---

## Section 2: Issue Triage

No open issues.

---

## Section 3: PR Security Scan

No open pull requests.

---

*Report generated automatically on 2026-09-01.*
