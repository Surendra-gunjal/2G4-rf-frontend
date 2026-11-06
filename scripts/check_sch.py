import re, math, json, sys
from collections import defaultdict

def parse(s):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', s)
    st = [[]]
    for t in toks:
        if t == '(': st.append([])
        elif t == ')': x = st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def kids(n, key): return [c for c in n if isinstance(c, list) and c and c[0] == key]
def walk(n):
    yield n
    for c in n:
        if isinstance(c, list): yield from walk(c)

sch = parse(open('2G4_RF_Receiver_FrontEnd.kicad_sch').read())
pcb = parse(open('2G4_RF_Receiver_FrontEnd.kicad_pcb').read())
rep = {}

# ---- library pins straight from the file
libpins = {}
for ls in kids(sch, 'lib_symbols'):
    for sym in kids(ls, 'symbol'):
        pins = {}
        for n in walk(sym):
            if n[0] == 'pin' and len(n) > 3 and isinstance(n[3], list) and n[3][0] == 'at':
                at = kids(n, 'at')[0]; num = kids(n, 'number')[0][1]
                pins[num] = (float(at[1]), float(at[2]))
        libpins[sym[1]] = pins

# ---- instances
inst = []
for sym in kids(sch, 'symbol'):
    lib = kids(sym, 'lib_id')[0][1]; at = kids(sym, 'at')[0]
    x, y, rot = float(at[1]), float(at[2]), int(float(at[3]))
    props = {p[1]: p[2] for p in kids(sym, 'property')}
    uid = kids(sym, 'uuid')[0][1]
    pts = {}
    for pn in kids(sym, 'pin'):
        num = pn[1]; px, py = libpins[lib][num]
        c, s_ = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot % 360]
        rx, ry = px * c - py * s_, px * s_ + py * c
        pts[num] = (round(x + rx, 3), round(y - ry, 3))
    inst.append(dict(lib=lib, ref=props['Reference'], value=props['Value'], fp=props.get('Footprint', ''), uid=uid, pins=pts,
                     power=lib.startswith('power:')))

# ---- union-find over points
par = {}
def find(a):
    par.setdefault(a, a)
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
def union(a, b): par[find(a)] = find(b)
def pt(x, y): return (round(float(x), 3), round(float(y), 3))

wires = []
for w in kids(sch, 'wire'):
    xy = kids(kids(w, 'pts')[0], 'xy'); a, b = pt(*xy[0][1:3]), pt(*xy[1][1:3])
    wires.append((a, b)); union(a, b)
def on_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > 1e-3: return False
    return min(ax, bx) - 1e-3 <= px <= max(ax, bx) + 1e-3 and min(ay, by) - 1e-3 <= py <= max(ay, by) + 1e-3

nodes = []   # (point, kind, info)
for (a, b) in wires: nodes += [(a, 'wire', None), (b, 'wire', None)]
for l in kids(sch, 'label'):
    at = kids(l, 'at')[0]; nodes.append((pt(at[1], at[2]), 'label', l[1]))
for j in kids(sch, 'junction'):
    at = kids(j, 'at')[0]; nodes.append((pt(at[1], at[2]), 'junction', None))
for i in inst:
    for num, p in i['pins'].items(): nodes.append((p, 'pin', (i['ref'], num, i)))
for (p, k, info) in nodes:
    find(p)
    for (a, b) in wires:
        if on_seg(p, a, b): union(p, a)

names = defaultdict(set)
for (p, k, info) in nodes:
    if k == 'label': names[find(p)].add(info)
    if k == 'pin' and info[2]['power'] and 'PWR_FLAG' not in info[2]['lib']: names[find(p)].add(info[2]['value'])
problems = []
for r, n in names.items():
    if len(n) > 1: problems.append(f'SHORT between names {sorted(n)}')

sch_net = {}
members = defaultdict(list)
for (p, k, info) in nodes:
    if k == 'pin' and not info[2]['power']:
        ref, num, _ = info
        nm = names.get(find(p)); sch_net[(ref, num)] = (sorted(nm)[0] if nm else None)
        members[find(p)].append((ref, num))
for r, m in members.items():
    nm = names.get(r)
    if not nm: problems.append(f'UNNAMED net with pins {m}')
# every pin on a net with >=2 connection points?
for (p, k, info) in nodes:
    if k == 'pin' and not info[2]['power']:
        cnt = sum(1 for (q, kk, ii) in nodes if find(q) == find(p) and kk in ('pin', 'label') and not (kk == 'pin' and ii[2]['power'] is False and ii[:2] == info[:2]))
        if cnt == 0: problems.append(f'FLOATING pin {info[0]}.{info[1]}')

# ---- PCB pads
pcb_net, pcb_fp, pcb_path = {}, {}, {}
for fp in kids(pcb, 'footprint'):
    ref = [p for p in kids(fp, 'property') if p[1] == 'Reference'][0][2]
    pcb_fp[ref] = fp[1]; pcb_path[ref] = kids(fp, 'path')[0][1]
    for pad in kids(fp, 'pad'):
        net = kids(pad, 'net')
        pcb_net[(ref, pad[1])] = net[0][2] if net else None

mism = []
for k in sorted(set(sch_net) | set(pcb_net)):
    a, b = sch_net.get(k), pcb_net.get(k)
    if a != b: mism.append((k, 'sch=' + str(a), 'pcb=' + str(b)))
rep['pins_in_schematic'] = len(sch_net); rep['pads_in_pcb'] = len(pcb_net)
rep['net_mismatches'] = mism
rep['problems'] = problems
rep['nets_in_schematic'] = sorted({v for v in sch_net.values() if v})
# footprint / path link
fpm, pathm = [], []
for i in inst:
    if i['power']: continue
    if pcb_fp.get(i['ref']) != i['fp']: fpm.append((i['ref'], i['fp'], pcb_fp.get(i['ref'])))
    if pcb_path.get(i['ref']) != '/' + i['uid']: pathm.append(i['ref'])
rep['footprint_name_mismatch'] = fpm; rep['path_link_mismatch'] = pathm
rep['refs_only_in_one'] = sorted(set(i['ref'] for i in inst if not i['power']) ^ set(pcb_fp))
# stacked-pin positions sanity: wire endpoints not attached to anything (dangling)
deg = defaultdict(int)
for (a, b) in wires: deg[a] += 1; deg[b] += 1
att = {p for (p, k, info) in nodes if k in ('pin', 'label')}
dangling = [p for p, d in deg.items() if d == 1 and p not in att]
rep['dangling_wire_ends'] = dangling
print(json.dumps(rep, indent=1, default=str))
