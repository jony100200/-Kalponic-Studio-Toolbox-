Got it, Jony. Here’s the bare-bones cheat sheet you can hand to an AI or a teammate.

# Fix white halos & jaggies on Photoshop cut-outs — fast

## 1) Local fix (Mask + Smudge), then re-harden

* Add a **layer mask** to your cut-out. Put a black or white **solid color** layer behind it to spot halos.
* Select the **mask**, grab **Smudge Tool** (~50% strength), use a **big, soft brush**, and gently push the fringe **inward** only where it exists (surgical, not global). This avoids deleting clean areas elsewhere. 
* If edges turned a bit soft, re-harden the mask: **Image → Adjustments → Brightness/Contrast → Use Legacy** ✓, then raise **Contrast** until edges snap clean (white gets whiter, black gets blacker → thinner, sharper edge).   

**When to use:** Mixed edges—some areas clean, some with fringe.

---

## 2) Selection-driven cleanup (Contract + Paint)

* **Load the mask as a selection** (Ctrl/Cmd-click mask). **Select → Modify → Contract** (start at 1–2 px, adjust to resolution). 
* **Invert** selection (Ctrl/Cmd+Shift+I). With the **mask** active, **paint/fill black** to wipe the halo ring. Hide/show marching ants with **Ctrl/Cmd+H** if they distract.  

**Pros:** Crisp, fast.
**Cons:** If you contract everywhere, you can clip fine detail—use selectively. 

---

## 3) De-jaggify edges fast (Select and Mask “Smooth”)

* With the **mask** selected, open **Select and Mask** (older PS: Refine Edge). In CC 2015.5+ it’s built-in. 
* Push **Smooth** a little (**~1–3**; **4 can be too much**) to kill staircase edges, then OK.  

---

## Quick decision guide

* **Few problem spots?** Use **Smudge on mask** locally → then **Use Legacy Contrast** to re-harden. 
* **Halo all around?** Try **Contract + Invert + Paint** (watch delicate areas). 
* **Edges look blocky?** **Select and Mask → Smooth (1–3)**. 

---

## Copy-paste prompt for an AI assistant

“Given a Photoshop layer with a mask that shows white halos and some jaggies:

1. On the **mask**, use **Smudge Tool (~50% strength, soft, large)** to push fringe inward only where it exists; then **Image → Adjustments → Brightness/Contrast → Use Legacy**, increase **Contrast** to re-harden the mask edge.
2. If halo persists globally, **Ctrl/Cmd-click mask → Select → Modify → Contract (1–2 px) → Invert → fill/paint black on the mask** to erase the ring; hide ants with **Ctrl/Cmd+H**.
3. For jagged edges, open **Select and Mask** and set **Smooth ≈1–3** (avoid over-smoothing). Output should preserve fine detail and remove halos without shrinking good edges unnecessarily.”

That’s it—practical, fast, and clean.
