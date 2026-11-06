import re, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
exec(open('check_sch.py').read().split('# ---- library pins')[0])   # reuse parse/kids/walk + sch tree
fig, ax = plt.subplots(figsize=(17, 11)); ax.set_xlim(20, 262); ax.set_ylim(150, 66); ax.set_aspect('equal'); ax.set_facecolor('#fffff0')
col = '#8b0000'
for w in kids(sch, 'wire'):
    xy = kids(kids(w, 'pts')[0], 'xy'); ax.plot([float(xy[0][1]), float(xy[1][1])], [float(xy[0][2]), float(xy[1][2])], color='#006400', lw=1.6, zorder=2)
for j in kids(sch, 'junction'):
    at = kids(j, 'at')[0]; ax.add_patch(Circle((float(at[1]), float(at[2])), 0.6, color='#006400', zorder=3))
libs = {s[1]: s for ls in kids(sch, 'lib_symbols') for s in kids(ls, 'symbol')}
for sym in kids(sch, 'symbol'):
    lib = kids(sym, 'lib_id')[0][1]; at = kids(sym, 'at')[0]; x, y, rot = float(at[1]), float(at[2]), int(float(at[3]))
    c, s_ = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot % 360]
    T = lambda px, py: (x + px * c - py * s_, y - (px * s_ + py * c))
    for n in walk(libs[lib]):
        if n[0] == 'rectangle':
            a = kids(n, 'start')[0]; b = kids(n, 'end')[0]
            p1, p2 = T(float(a[1]), float(a[2])), T(float(b[1]), float(b[2]))
            ax.add_patch(Rectangle((min(p1[0], p2[0]), min(p1[1], p2[1])), abs(p1[0]-p2[0]), abs(p1[1]-p2[1]), fc='#ffffc8', ec=col, lw=1.2, zorder=4))
        elif n[0] == 'polyline':
            pts = [T(float(q[1]), float(q[2])) for q in kids(kids(n, 'pts')[0], 'xy')]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=1.6, zorder=4)
        elif n[0] == 'arc':
            q = [T(float(kids(n, k)[0][1]), float(kids(n, k)[0][2])) for k in ('start', 'mid', 'end')]
            ax.plot([p[0] for p in q], [p[1] for p in q], color=col, lw=1.6, zorder=4)
        elif n[0] == 'circle':
            cc = T(0, 0); ax.add_patch(Circle(cc, 1.27, fill=False, ec=col, lw=1.2, zorder=4))
        elif n[0] == 'pin' and len(n) > 3 and isinstance(n[3], list) and n[3][0] == 'at':
            a = kids(n, 'at')[0]; ln = float(kids(n, 'length')[0][1]); ang = float(a[3])
            px, py = float(a[1]), float(a[2]); ex, ey = px + ln * math.cos(math.radians(ang)), py + ln * math.sin(math.radians(ang))
            p1, p2 = T(px, py), T(ex, ey); ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=col, lw=1.2, zorder=4)
            if 'hide' not in n[:8] and not lib.startswith(('power', 'Device')):
                nm = kids(n, 'name')[0][1]; num = kids(n, 'number')[0][1]
                if nm not in ('~',): ax.text((p1[0]+p2[0])/2 + (0 if abs(p2[0]-p1[0]) < 1e-6 else 0), (p1[1]+p2[1])/2 - 0.8, f'{nm}', fontsize=5, ha='center', color='#555', zorder=6)
    props = {p[1]: p for p in kids(sym, 'property')}
    for k in ('Reference', 'Value'):
        p = props[k]; 
        if 'hide' in p[-1]: continue
        a = kids(p, 'at')[0]; ax.text(float(a[1]), float(a[2]), p[2], fontsize=7, color='#008080' if k == 'Reference' else '#006666', ha='center', va='center', zorder=7)
for l in kids(sch, 'label'):
    at = kids(l, 'at')[0]; ax.text(float(at[1]), float(at[2]) - 0.4, l[1], fontsize=8, color='#b8860b', ha='left', va='bottom', zorder=7, fontweight='bold')
for t in kids(sch, 'text'):
    at = kids(t, 'at')[0]; ax.text(float(at[1]), float(at[2]), t[1].replace('\\n', '\n'), fontsize=6.5, va='top', ha='left', color='#222')
ax.set_title('2G4 RF front-end schematic - matplotlib PREVIEW of the .kicad_sch contents (not the KiCad renderer)', fontsize=10)
ax.set_xticks([]); ax.set_yticks([])
plt.tight_layout(); plt.savefig('schematic_preview.png', dpi=105)
