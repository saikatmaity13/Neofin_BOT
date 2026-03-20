"""
clean_fix.py
Surgically removes the leftover old CSS block and old header fragment from main.py
"""
with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"Total lines: {total}")

# ── Find the two problematic regions ───────────────────────────────────────────

# Region 1: stray old CSS  (starts after the new </style> close, ends before _HELPERS)
# Look for the first bare `:root{` that is NOT inside a string
# Our new block ends with `""", unsafe_allow_html=True)` on a line that closes the markdown call.
# The stray block starts right after that close on the next line with `:root{`

region1_start = None
region1_end   = None

# Region 2: old header HTML fragment left dangling after the new markdown call closes
# It starts right after `""", unsafe_allow_html=True)` for the header (second occurrence)
# and ends before `# SIDEBAR` section

region2_start = None
region2_end   = None

# Pass 1 – find region boundaries
in_region1 = False

for i, line in enumerate(lines):
    stripped = line.strip()

    # Region 1 starts at bare `:root{` (approximately line 380 in original, ~380 in new)
    if not in_region1 and stripped == ":root{":
        region1_start = i
        in_region1 = True

    # Region 1 ends when we hit the python def for _decision_badge
    if in_region1 and stripped.startswith("def _decision_badge"):
        region1_end = i
        in_region1 = False
        break

# Pass 2 – find region 2 (old header HTML dangling after marker)
# It's the lines after `""", unsafe_allow_html=True)` that begin with `  <div style=`
# and ends before `# ══ SIDEBAR` comment
for i in range(region1_end or 0, len(lines)):
    stripped = lines[i].strip()
    # The dangling old header HTML begins right after the new header markdown closes
    # its triple-quote.  The new header ends with `""", unsafe_allow_html=True)`
    # then immediately the stray `  <div style=` block starts
    if region2_start is None and stripped.startswith('<div style="position:absolute'):
        region2_start = i
    if region2_start and stripped.startswith("# ══════") and "SIDEBAR" in stripped:
        region2_end = i
        break

print(f"Region 1 (stale CSS block):    lines {region1_start}–{region1_end - 1}")
print(f"Region 2 (dangling old header): lines {region2_start}–{region2_end - 1}")

# ── Remove regions (in reverse order so indices stay valid) ───────────────────
new_lines = lines[:]

if region2_start and region2_end:
    del new_lines[region2_start:region2_end]

# Recompute region1 indices after region2 removal (region1 is before region2)
# so they are still valid — just delete region1 as well
if region1_start and region1_end:
    del new_lines[region1_start:region1_end]

# ── Also update inline CSS class refs from old names to new names ──────────────
result = "".join(new_lines)

# Old class     -> New class
replacements = [
    ('class="example-card"',   'class="ns-card"'),
    ('class="user-bubble"',    'class="bubble-user"'),
    ('class="agent-bubble"',   'class="bubble-agent-hdr"'),
    # Tool/web pill classes
    ('class="tool-pill"',      'class="pill-tool"'),
    ('class="web-pill"',       'class="pill-web"'),
    # Section label
    ('class="sec-label"',      'class="ns-section"'),
    # Card subclasses
    ('class="card-tag"',       'class="card-badge"'),
    # Metric boxes
    ('class="metric-box"',     'class="ns-metric"'),
    ('class="metric-val"',     'class="ns-metric-val"'),
    ('class="metric-lbl"',     'class="ns-metric-lbl"'),
    # Sidebar residual colour refs
    ('#00c8f0',                 '#3B82F6'),
    ('#00e5a0',                 '#10B981'),
    ('#9060ff',                 '#8B5CF6'),
    ('#142d4a',                 '#1E2D45'),
    ('#071220',                 '#0C1220'),
    ('#0b1c30',                 '#131A2A'),
    ('#0a1520',                 '#131A2A'),
]

for old, new in replacements:
    result = result.replace(old, new)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(result)

print("✅ Clean fix applied successfully.")
