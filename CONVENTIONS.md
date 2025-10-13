# KS Toolbox Project – Coding Conventions



## 🧠 Coding Principles

- **KISS:** Keep It Simple, Stupid—write clear, minimal, and direct code. Avoid unnecessary complexity.
- **SOLID Principles:** Ensure code is modular, single-responsibility, easily extendable, and loosely coupled.
- **Centralized Configuration:**  
  - No hardcoded paths or drive letters (except `C:` for Gemini CLI editing).
  - Use config files or environment variables for all paths and settings.
- **Archiving, Not Deleting:**  
  - Move obsolete or unused scripts to the `archive/` folder rather than deleting.
- **Documentation:**  
  - Docstrings and comments should be clear, concise, and describe all public APIs and major functions.
- **Modularity:**  
  - Scripts and modules should be reusable, portable, and organized for clarity.

---

## 🗂️ Directory & Workflow Policy

- **Editing/Refactoring (Gemini CLI):** Only use absolute paths on the `C:` drive.
- **Testing/Project/Models:** Use config to reference models/assets, which may reside on any drive.
- **.gitignore:** Keep large model files, outputs, and irrelevant assets out of version control.

---

*Stick to these conventions to ensure a consistent, maintainable, and professional codebase across the whole Patchline project!*
