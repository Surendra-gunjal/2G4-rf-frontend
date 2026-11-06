"""Mimics the specific KiCad DRC rules that fired in the user's report, on the generated files."""
import re, json, itertools
from shapely.geometry import box
from kiutils.board import Board
from kiutils.footprint import Footprint
import glob, os

b = Board.from_file('2G4_RF_Receiver_FrontEnd.kicad_pcb')
rep = {}
# 1. courtyard overlaps (absolute boxes)
cy = {}
for fp in b.footprints:
    ref = fp.properties['Reference']
    for g in fp.graphicItems:
        if getattr(g, 'layer', None) == 'F.CrtYd' and g.__class__.__name__ == 'FpRect':
            cy[ref] = box(fp.position.X + g.start.X, fp.position.Y + g.start.Y, fp.position.X + g.end.X, fp.position.Y + g.end.Y)
ov = [(a, c, round(cy[a].intersection(cy[c]).area, 4)) for a, c in itertools.combinations(cy, 2) if cy[a].intersects(cy[c]) and cy[a].intersection(cy[c]).area > 1e-9]
rep['courtyard_overlaps'] = ov
# 2. silk text height and approximate bbox vs pads / board edge
TXT_MIN = 0.8
pads = []
for fp in b.footprints:
    ref = fp.properties['Reference']
    for p in fp.pads:
        cx, cy_ = fp.position.X + p.position.X, fp.position.Y + p.position.Y
        pads.append((f'{ref}.{p.number}', box(cx - p.size.X/2, cy_ - p.size.Y/2, cx + p.size.X/2, cy_ + p.size.Y/2), ref))
vias = [(f'via', box(v.position.X - v.size/2, v.position.Y - v.size/2, v.position.X + v.size/2, v.position.Y + v.size/2)) for v in b.traceItems if v.__class__.__name__ == 'Via']
small, silk_pad, silk_edge = [], [], []
for fp in b.footprints:
    ref = fp.properties['Reference']
    for it in fp.graphicItems:
        if it.__class__.__name__ == 'FpText' and it.type == 'reference':
            h = it.effects.font.height
            if h < TXT_MIN - 1e-9: small.append((ref, h))
            x, y = fp.position.X + it.position.X, fp.position.Y + it.position.Y
            w = len(ref) * h * 0.75 + 0.15
            bb = box(x - w/2, y - h/2 - 0.075, x + w/2, y + h/2 + 0.075)
            for name, pb, owner in pads:
                if bb.intersects(pb): silk_pad.append((ref, name))
            for _, vb in vias:
                if bb.intersects(vb): silk_pad.append((ref, 'via'))
            if bb.bounds[0] < 0 or bb.bounds[1] < 0 or bb.bounds[2] > 40 or bb.bounds[3] > 24: silk_edge.append(ref)
rep['ref_text_below_0.8mm'] = small
rep['ref_text_over_pad_or_via_(approx bbox)'] = silk_pad
rep['ref_text_outside_board'] = silk_edge
# 3. footprint library present and matches
libdir = 'RF_Generic.pretty'
libnames = {os.path.basename(f)[:-len('.kicad_mod')] for f in glob.glob(libdir + '/*.kicad_mod')}
used = {fp.libId.split(':')[1] for fp in b.footprints}
rep['footprints_missing_from_library'] = sorted(used - libnames)
parse_ok = []
for f in glob.glob(libdir + '/*.kicad_mod'):
    m = Footprint.from_file(f); parse_ok.append((os.path.basename(f), len(m.pads)))
rep['library_files_parse_ok'] = parse_ok
# pad geometry equal between board and library (ignoring nets)
mism = []
for fp in b.footprints:
    m = Footprint.from_file(f'{libdir}/{fp.libId.split(":")[1]}.kicad_mod')
    a = sorted((p.number, p.shape, round(p.position.X, 4), round(p.position.Y, 4), round(p.size.X, 4), round(p.size.Y, 4)) for p in fp.pads)
    c = sorted((p.number, p.shape, round(p.position.X, 4), round(p.position.Y, 4), round(p.size.X, 4), round(p.size.Y, 4)) for p in m.pads)
    if a != c: mism.append(fp.properties['Reference'])
rep['board_vs_library_pad_mismatch'] = mism
# 4. edge clearance: everything except pads must keep 0.3 mm (pads are waived by the custom rule)
from shapely.geometry import LineString, Point
edge = box(0, 0, 40, 24).exterior
viol = []
for t in b.traceItems:
    c = t.__class__.__name__
    if c == 'Segment':
        g = LineString([(t.start.X, t.start.Y), (t.end.X, t.end.Y)]).buffer(t.width/2)
    else:
        g = Point(t.position.X, t.position.Y).buffer(t.size/2)
    if g.distance(edge) < 0.3 - 1e-9: viol.append((c, round(g.distance(edge), 3)))
rep['non_pad_copper_closer_than_0.3mm_to_edge'] = viol
pad_edge = sorted({o for (n, pb, o) in pads if pb.distance(edge) < 0.3 - 1e-9})
rep['pads_within_0.3mm_of_edge_(waived by rule file)'] = pad_edge
rep['rule_file'] = open('2G4_RF_Receiver_FrontEnd.kicad_dru').read()
# schematic footprint fields match
sch = open('2G4_RF_Receiver_FrontEnd.kicad_sch').read()
fps_sch = dict(re.findall(r'\(property "Reference" "([A-Z]+\d+)".*?\(property "Footprint" "([^"]*)"', sch, re.S))
rep['schematic_footprint_fields_match_board'] = all(fps_sch.get(fp.properties['Reference']) == fp.libId for fp in b.footprints)
print(json.dumps(rep, indent=1, default=str))
