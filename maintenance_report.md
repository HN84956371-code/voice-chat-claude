# Weekly Maintenance Report — 2026-10-01

## Section 1: Dependency Check

| Package | Pinned Min | Latest PyPI | Status |
|---|---|---|---|
| SpeechRecognition | >=3.10 | 3.17.0 | Minor gap (7 minor versions) |
| PyAudio | >=0.2.14 | 0.2.14 | Up to date |
| edge-tts | >=6.1 | 7.2.8 | **ACTION NEEDED — major version jump (6→7)** |
| pygame | >=2.5 | 2.6.1 | Minor gap, no action needed |
| openai-whisper | >=20231117 | 20250625 | Significant gap (~19 months of updates) |
| soundfile | >=0.12 | 0.14.0 | Minor gap, no action needed |

### Items needing attention

**edge-tts (6.x → 7.x):** The pinned minimum `>=6.1` will still resolve to 7.x in a fresh install (pip satisfies `>=6.1` with any higher version), meaning the project already receives edge-tts 7.x. However, edge-tts 7.x introduced breaking changes to its async API (notably `Communicate.run()` was redesigned). If the project uses edge-tts directly, test for breakage and update the pin to `>=7.0` to document the actual requirement.

**openai-whisper (20231117 → 20250625):** ~19 months of upstream changes. Recommend testing with the latest version and bumping the minimum pin if compatible. May include model improvements and bug fixes.

**SpeechRecognition (3.10 → 3.17):** Minor version gap. Low risk but worth testing the latest.

**Security audit:** `pip-audit` is not installed in this environment. No automated vulnerability check was performed. Consider adding `pip-audit` to the CI pipeline (`pip install pip-audit && pip-audit -r requirements.txt`).

---

## Section 2: Issue Triage

No open issues.

---

## Section 3: PR Security Scan

No open pull requests.

---

## Summary

One item needs prompt attention: **edge-tts has a major version bump (6→7) with known breaking API changes** — the minimum pin should be audited and updated. The openai-whisper pin is also significantly stale. Everything else is clean.
