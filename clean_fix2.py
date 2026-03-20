"""
clean_fix2.py  –  Remove two stale blocks from main.py
  Block A: lines 380-628  (old CSS :root block that's raw Python)
  Block B: lines 743-778  (old header HTML fragment dangling after new header)
  Also canonicalise colour literals and CSS class names throughout.
"""
with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Python uses 0-indexed slices; file line numbers above are 1-indexed.
# Block A:  line 380 → index 379   to   line 628 → index 627  (inclusive)
# Block B:  line 743 → index 742   to   line 778 → index 777  (inclusive)

# Delete Block B first (higher indices) so Block A indices are unaffected
del lines[742:778]   # was lines 743–778 (indices 742–777 inclusive)
del lines[379:628]   # was lines 380–628 (indices 379–627 inclusive)

result = "".join(lines)

# ── Canonicalise inline CSS class names and colour literals ─────────────────
replacements = [
    # CSS class names → new design system
    ('class="example-card"',   'class="ns-card"'),
    ('class="user-bubble"',    'class="bubble-user"'),
    # agent bubble is split header + body – just update header references
    ('"agent-bubble"',          '"bubble-agent-hdr"'),
    ('class="tool-pill"',      'class="pill-tool"'),
    ('class="web-pill"',       'class="pill-web"'),
    ('class="sec-label"',      'class="ns-section"'),
    ('class="card-tag"',       'class="card-badge"'),
    ('class="metric-box"',     'class="ns-metric"'),
    ('class="metric-val"',     'class="ns-metric-val"'),
    ('class="metric-lbl"',     'class="ns-metric-lbl"'),
    # Legacy colour palette → new palette
    ('#00c8f0',                 '#3B82F6'),
    ('#00e5a0',                 '#10B981'),
    ('#9060ff',                 '#8B5CF6'),
    ('#142d4a',                 '#1E2D45'),
    ('#1E2532',                 '#1E2D45'),
    ('#071220',                 '#0C1220'),
    ('#0b1c30',                 '#131A2A'),
    ('#0a1520',                 '#131A2A'),
    ('#9ab8d0',                 '#94A3B8'),
    # Sidebar section dividers
    ('color:#8F9BAD',           'color:#94A3B8'),
    ('border-bottom:1px solid #1E2D45', 'border-bottom:1px solid var(--bd-subtle)'),
    ('border-top:1px solid #1E2D45',    'border-top:1px solid var(--bd-subtle)'),
    # Card/old hover colours
    ('#4a6a84',                 '#94A3B8'),
    ('#e8f4ff',                 '#F1F5F9'),
]
for old, new in replacements:
    result = result.replace(old, new)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(result)

print("✅ clean_fix2 done. Verifying compile…")

import subprocess, sys
r = subprocess.run([sys.executable, "-m", "py_compile", "main.py"], capture_output=True, text=True)
if r.returncode == 0:
    print("✅ main.py compiles without errors.")
else:
    print("❌ Compile errors:\n", r.stderr[:2000])
