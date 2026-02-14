# Roadmap (Checklist)

This file tracks what is done and what is left for KS CodeOps.

- [x] VS Code window focus and input focus verification
- [x] Text send via clipboard
- [x] Image send via clipboard
- [x] Per-target presets (Copilot, Gemini, Codex, Kilo, Cline)
- [x] Target selection in GUI
- [x] Test target activation in GUI/CLI
- [x] Per-step target routing in sequence JSON
- [x] Single-lane job runner, status, retries, validators
- [x] Phase 1: Output capture, extraction, and step artifacts
- [x] Phase 2: Optional UIA backend with pyautogui fallback
- [x] Phase 3: Companion VS Code bridge extension scaffold
- [x] Modernized dark UI visual system and action hierarchy
- [x] Status strip chips + ordered activity logging in GUI
- [x] Professional font fallback stack for cross-machine consistency

Next:

- [ ] GUI target checkbox matrix (`enabled_targets`) for explicit multi-target selection
- [ ] Rule-based scheduler for task-to-target assignment (fit/speed/reliability)
- [ ] Multi-lane dispatcher skeleton with safe fallback to single-lane
- [ ] Lane/worktree isolation and health-based rerouting
- [ ] Troubleshooting matrix and regression checklist for focus/activation failures
