# 🤖 AI RULES - ESSENTIAL GUIDE

## 🚨 **MANDATORY WORKFLOW (WIN 10/11 ONLY):**

### **STEP 1: AUDIT FIRST**
```
1. list_dir - See what exists
2. read_file - Understand before touching
3. Check if feature exists before creating
4. Follow KISS + SOLID
5. Everything modular, NO hardcoding
6. Do not include "inspired by", "based on", or similar references in code comments or files. All implemented systems must be treated as original. Once adapted or rewritten, it becomes our own version.
7.Use python 3.10 
```

### **STEP 2: WORK WITH EXISTING**
```
- Modify existing files vs creating new
- Use existing patterns/structures  
- Build on working code
```

### **STEP 3: CLEANUP SAME SESSION**
```
DELETE TEMP FILES:
- test_*.py → DELETE after testing
- setup_*.py → DELETE after use
- Any temp files → DELETE before session ends
```

## ✅ **AI MUST / 🚫 MUST NEVER:**
```
✅ ALWAYS:                    🚫 NEVER:
- Audit before action         - Create files without checking
- Work with existing files    - Leave temp files in root
- Delete temps same session   - Work multiple tasks at once
- One focused task           - Skip reading existing code
- Test changes work          - Create duplicate functionality
```

## 📋 **3-STEP CHECKLIST:**
```
1. BEFORE ACTION:
   □ list_dir to see what exists?
   □ read_file to understand current code?
   □ Working with existing vs creating new?

2. BEFORE CODE:
   □ Function does ONE thing <30 lines?
   □ Filename shows clear purpose?
   □ Keeping simple (no deep nesting)?

3. BEFORE ENDING:
   □ Deleted all test_*.py created?
   □ Deleted all setup_*.py created?
   □ Verified system works?
```

**CORE: AUDIT → EXISTING → SIMPLE → CLEANUP**

## 🔧 **CODE QUALITY - ESSENTIAL:**

### **RULES:**
```
Functions: <30 lines, ONE thing, clear name
Files: <300 lines ideal, <500 limit, <800 absolute max
Names: Clear purpose (NO: core.py, utils.py, handler.py, manager.py)
Logic: Max 3 nesting levels
Pattern: One file = One purpose, One function = One task
```

### **BANNED PATTERNS:**
```
🚫 Vague names: core.py, utils.py, manager.py, handler.py
🚫 Long functions: >30 lines
🚫 Big files: >500-600 lines  
🚫 Multiple purposes in one file/function
🚫 Deep nesting: >3 levels
```

## 🧠 **ANTI-STUPID RULES:**

### **NEVER FIX WORKING CODE:**
```
❌ DON'T TOUCH IF:
- Backend runs and serves requests
- Endpoints respond correctly  
- System works despite warnings
- Import errors in dev ≠ broken production

✅ ONLY FIX IF:
- System fails to start
- Endpoints return 500 errors
- User reports specific broken functionality
```

### **TESTING ORDER:**
```
✅ RIGHT: start_allama.py → test endpoints → analyze if broken
❌ WRONG: random imports → see error → claim "broken"
```

### **CONFIDENCE LEVELS:**
```
🟢 HIGH: "Tested actual app, verified X works"
🟡 MED: "Code analysis suggests this works"
🔴 LOW: "Haven't tested, but think..."
❌ NEVER: "Nothing works" without testing
```


## 🚀 **TECH STACK RULES:**

### **ALWAYS USE:**
```
FRONTEND:
- TurboStyle utilities (NO custom CSS)
- TurboReactive signals (signal, computed, effect)
- MissionJS plugins (RegisterPlugin, Deploy, LoadComponent)

BACKEND:
- allamepy plugins (RegisterAllamepyPlugin, Deploy, LoadBackendComponent)
- Modular, single-responsibility components

PATTERNS:
- Football team approach: small utilities working together
- One component = one clear role
- Make impossible → possible with coordinated small parts
```

### **QUICK CHECKS:**
```
□ TurboStyle for styling?          □ allamepy for backend plugins?
□ TurboReactive for state?         □ Small, focused components?
□ MissionJS for frontend plugins?  □ Single responsibility?
□ Football team approach?          □ Reusable design?
```
