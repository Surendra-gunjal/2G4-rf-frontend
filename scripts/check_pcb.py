import math, json, itertools
from kiutils.board import Board
from shapely.geometry import box, LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

b = Board.from_file('/home/claude/rf_pcb/2G4_RF_Receiver_FrontEnd.kicad_pcb')
netname = {n.number: n.name for n in b.nets}
BW, BH = 40.0, 24.0
objs = []  # dict(kind,name,layer,net,geom)
for fp in b.footprints:
    ref = fp.properties['Reference']
    for p in fp.pads:
        cx, cy = fp.position.X + p.position.X, fp.position.Y + p.position.Y
        g = Point(cx, cy).buffer(p.size.X/2, 32) if p.shape == 'circle' else box(cx-p.size.X/2, cy-p.size.Y/2, cx+p.size.X/2, cy+p.size.Y/2)
        lays = ['F.Cu', 'B.Cu'] if p.type == 'thru_hole' else [l for l in p.layers if l.endswith('.Cu')]
        for l in lays:
            objs.append(dict(kind='pad', name=f'{ref}.{p.number}', layer=l, net=netname[p.net.number], geom=g))
for i, it in enumerate(b.traceItems):
    c = it.__class__.__name__
    if c == 'Segment':
        g = LineString([(it.start.X, it.start.Y), (it.end.X, it.end.Y)]).buffer(it.width/2, 8, cap_style=1)
        objs.append(dict(kind='track', name=f'seg{i}', layer=it.layer, net=netname[it.net], geom=g, w=it.width))
    elif c == 'Via':
        g = Point(it.position.X, it.position.Y).buffer(it.size/2, 24)
        for l in ('F.Cu', 'B.Cu'):
            objs.append(dict(kind='via', name=f'via{i}', layer=l, net=netname[it.net], geom=g, at=(it.position.X, it.position.Y)))

report = {}
# 1. clearance between different nets, per layer
MINCLR, DRC = 0.20, 0.15
viol, near, mind = [], [], 9e9
for ly in ('F.Cu', 'B.Cu'):
    L = [o for o in objs if o['layer'] == ly]
    tree = STRtree([o['geom'] for o in L])
    for i, o in enumerate(L):
        for j in tree.query(o['geom'].buffer(0.6)):
            if j <= i: continue
            p = L[j]
            if o['net'] == p['net']: continue
            if o['kind'] == 'via' and p['kind'] == 'via': pass
            d = o['geom'].distance(p['geom'])
            mind = min(mind, d)
            if d < DRC: viol.append((ly, o['name'], p['name'], round(d, 3)))
            elif d < MINCLR - 1e-9: near.append((ly, o['name'], p['name'], round(d, 3)))
report['clearance'] = dict(min_diffnet_clearance_mm=round(mind, 3), below_0p15=viol, between_0p15_and_0p20=near)

# 2. board edge distance (copper except connector pads at the edge)
edge = box(0, 0, BW, BH).exterior
ed = []
for o in objs:
    if o['name'].split('.')[0] in ('J1', 'J2') and o['kind'] == 'pad': continue
    d = o['geom'].distance(edge)
    if d < 0.3: ed.append((o['name'], o['layer'], round(d, 3)))
report['edge_clearance_below_0p3'] = ed

# 3. connectivity of each non-GND net (F.Cu + vias + THT pads)
def components(net):
    items = [o for o in objs if o['net'] == net]
    n = len(items); par = list(range(n))
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for i in range(n):
        for j in range(i+1, n):
            a, c = items[i], items[j]
            same = a['layer'] == c['layer'] or a['name'] == c['name'] or \
                   (a['kind'] in ('via',) or c['kind'] in ('via',)) and False
            if a['layer'] == c['layer'] and a['geom'].distance(c['geom']) < 1e-6:
                par[find(i)] = find(j)
            elif a['name'] == c['name'] and a['layer'] != c['layer']:
                par[find(i)] = find(j)           # same via / THT pad spans layers
    comps = {}
    for i in range(n): comps.setdefault(find(i), []).append(items[i]['name'])
    return list(comps.values())
conn = {}
for net in ['+3V3', 'RF_IN', 'RF_BPF_OUT', 'RF_MATCH_A', 'RF_LNA_IN', 'RF_OUT', 'BIAS']:
    comps = components(net)
    pads = sorted({n for c in comps for n in c if '.' in n})
    conn[net] = dict(connected_groups=len(comps), pads=pads)
report['connectivity'] = conn

# 4. pour model: inset board minus 0.3 mm around non-GND copper, per layer
CLR = 0.30
pour = {}
for ly in ('F.Cu', 'B.Cu'):
    nong = unary_union([o['geom'] for o in objs if o['layer'] == ly and o['net'] != 'GND'])
    pr = box(0.3, 0.3, BW-0.3, BH-0.3).difference(nong.buffer(CLR, 24))
    parts = list(pr.geoms) if pr.geom_type == 'MultiPolygon' else [pr]
    pour[ly] = parts
# GND objects must touch a pour piece that is big & stitched; check islands on F.Cu
gnd_vias = [o for o in objs if o['kind'] == 'via' and o['layer'] == 'F.Cu' and o['net'] == 'GND']
isl = []
for k, part in enumerate(pour['F.Cu']):
    if part.area < 0.5: continue
    has_via = any(part.intersects(v['geom']) and part.intersection(v['geom']).area > 0.1 for v in gnd_vias)
    if not has_via: isl.append((k, round(part.area, 2), [round(x, 1) for x in part.centroid.coords[0]]))
report['F.Cu_pour_pieces_over_0.5mm2'] = sum(1 for p in pour['F.Cu'] if p.area >= 0.5)
report['F.Cu_pour_islands_without_via'] = isl
report['B.Cu_pour_pieces_over_0.5mm2'] = sum(1 for p in pour['B.Cu'] if p.area >= 0.5)
# GND pads/tracks reaching pour
unreached = []
for o in objs:
    if o['net'] == 'GND' and o['layer'] == 'F.Cu' and o['kind'] in ('pad', 'track'):
        touch = any(o['geom'].buffer(1e-6).intersects(p) and o['geom'].buffer(1e-6).intersection(p).area > 1e-4 for p in pour['F.Cu'])
        if not touch: unreached.append(o['name'])
report['F.Cu_GND_pads_tracks_not_touching_pour'] = unreached

# 5. RF geometry: CPW gap actually achieved to the pour on the 1.6 mm sections
gaps = {}
for o in objs:
    if o['kind'] == 'track' and o['layer'] == 'F.Cu' and abs(o['w'] - 1.6) < 1e-6:
        d = min(p.distance(o['geom']) for p in pour['F.Cu'] if p.area > 2.0)
        gaps[o['name']] = round(d, 3)
report['CPW_gap_pour_to_1.6mm_line_mm'] = gaps

# 6. via fence pitch along RF lines (max spacing between vias flanking each wide section)
def fence_pitch(x0, x1, yc):
    xs = sorted(v['at'][0] for v in gnd_vias if x0 <= v['at'][0] <= x1 and 1.2 < abs(v['at'][1]-yc) < 2.4)
    top = sorted(v['at'][0] for v in gnd_vias if x0 <= v['at'][0] <= x1 and -2.4 < v['at'][1]-yc < -1.2)
    bot = sorted(v['at'][0] for v in gnd_vias if x0 <= v['at'][0] <= x1 and 1.2 < v['at'][1]-yc < 2.4)
    def mx(a):
        return round(max(b2-a2 for a2, b2 in zip(a, a[1:])), 2) if len(a) > 1 else None
    return dict(upper=len(top), lower=len(bot), max_pitch_upper=mx(top), max_pitch_lower=mx(bot))
report['via_fence'] = {'RF_in_J1_to_FL1 (x2-6.2)': fence_pitch(1.5, 7.0, 12.0),
                       'RF_out (x24-38)': fence_pitch(23.5, 38.5, 10.7)}

# 7. datasheet spacing checks
U = {p.number: (p.position.X, p.position.Y) for fp in b.footprints if fp.properties['Reference'] == 'U1' for p in fp.pads}
ux = [fp.position for fp in b.footprints if fp.properties['Reference'] == 'U1'][0]
def padpos(ref, num):
    fp = [f for f in b.footprints if f.properties['Reference'] == ref][0]
    p = [p for p in fp.pads if p.number == num][0]
    return fp.position.X + p.position.X, fp.position.Y + p.position.Y
p4 = padpos('U1', '4'); c3 = padpos('C3', '1'); c2 = padpos('C2', '1'); j3 = padpos('J3', '1')
man = lambda a, b: abs(a[0]-b[0]) + abs(a[1]-b[1])
d_c3 = math.dist(p4, c3); d_c2 = man(p4, c3) + man(c3, c2); d_j3 = man(p4, c3) + man(c3, j3)
report['vcc_line_mm'] = dict(pin4_to_C3=round(d_c3, 3), pin4_to_C2_along_line=round(d_c2, 3), pin4_to_J3_along_line=round(d_j3, 3),
                             datasheet_targets_mm=dict(C3=round(0.041*25.4, 3), C2=round(0.352*25.4, 3), line=round(0.532*25.4, 3)))
report['pin3_on_RF_centerline'] = dict(U1_pin3_y=padpos('U1', '3')[1], L1_pad2_y=padpos('L1', '2')[1], J1_y=padpos('J1', '1')[1])
report['U1_pin6_vs_J2_y'] = (padpos('U1', '6')[1], padpos('J2', '1')[1])

# 8. electrical length context
lam = 299.792458/2.45/math.sqrt(2.2)
report['lambda_g_mm_at_2p45GHz_epseff2.2'] = round(lam, 1)
report['lambda_over_20_mm'] = round(lam/20, 2)

json.dump(report, open('/home/claude/rf_pcb/check_report.json', 'w'), indent=1, default=str)
print(json.dumps(report, indent=1, default=str))
