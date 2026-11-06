#!/usr/bin/env python3
"""Generate 2G4_RF_Receiver_FrontEnd.kicad_pcb (KiCad 8 file format) for the MAX2644 2.4 GHz LNA front end.

Stack-up : F.Cu 35 um / RO4003C 0.813 mm / B.Cu 35 um (solid GND)
RF lines : grounded coplanar waveguide, W = 1.60 mm, gap = 0.30 mm  (FD solver: ~50 ohm at Dk 3.55)
All geometry is computed here, then exported to .kicad_pcb and to geometry.json for the checker.
"""
import json, uuid, math
from ids import U as SYM_UUID
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union

NS = uuid.UUID("6d1f3a52-7a38-4c61-9f11-2f0a1c9b7e01")
_c = [0]
def uid():
    _c[0] += 1
    return str(uuid.uuid5(NS, str(_c[0])))

def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

# ---------------------------------------------------------------- parameters
BW, BH = 40.0, 24.0           # board outline, mm
W, G = 1.60, 0.30             # RF line width and CPW gap (mm)
YIN, YOUT = 12.0, 10.7        # RF centre-lines (input / output)
VIA_D, VIA_DRILL = 0.60, 0.30
T_VCC, T_BIAS, T_GND = 0.30, 0.20, 0.30
ZONE_CLR = G                  # pour clearance == CPW gap
BOARD_T = 0.035 + 0.813 + 0.035

NETS = ["", "GND", "+3V3", "RF_IN", "RF_BPF_OUT", "RF_MATCH_A", "RF_LNA_IN", "RF_OUT", "BIAS"]
NID = {n: i for i, n in enumerate(NETS)}

footprints, tracks, vias = [], [], []

def pad(num, shape, dx, dy, w, h, net, func="", layers=None, kind="smd", drill=None):
    return dict(num=str(num), shape=shape, dx=dx, dy=dy, w=w, h=h, net=net, func=func,
                layers=layers or ["F.Cu"], kind=kind, drill=drill)

def fp(ref, value, name, x, y, pads, courtyard, descr="", ref_at=None):
    footprints.append(dict(ref=ref, value=value, name=name, x=x, y=y, pads=pads,
                           courtyard=courtyard, descr=descr, ref_at=ref_at))

def fp_0402(ref, value, cx, cy, orient, sgn, n1, n2, ref_at=None):
    """0402: pads 0.56x0.62, 0.96 mm centre pitch. Pad 1 at centre + sgn*0.48 along the axis."""
    if orient == "h":
        p1 = pad(1, "roundrect", sgn * 0.48, 0, 0.56, 0.62, n1)
        p2 = pad(2, "roundrect", -sgn * 0.48, 0, 0.56, 0.62, n2)
        cy_box = (-0.95, -0.46, 0.95, 0.46)
    else:
        p1 = pad(1, "roundrect", 0, sgn * 0.48, 0.62, 0.56, n1)
        p2 = pad(2, "roundrect", 0, -sgn * 0.48, 0.62, 0.56, n2)
        cy_box = (-0.46, -0.95, 0.46, 0.95)
    var = {("h", -1): "L", ("h", 1): "R", ("v", 1): "B", ("v", -1): "T"}[(orient, sgn)]   # side where pad 1 sits
    fp(ref, value, f"RF_Generic:C_R_L_0402_P1{var}", cx, cy, [p1, p2], cy_box,
       "Generic 0402 land pattern (IPC-like); pad 1 on the " + {"L": "left", "R": "right", "B": "bottom", "T": "top"}[var] +
       "; verify against chosen part", ref_at)

def track(x1, y1, x2, y2, w, net, layer="F.Cu"):
    tracks.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, w=w, net=net, layer=layer))

def via(x, y, net="GND"):
    vias.append(dict(x=x, y=y, net=net, d=VIA_D, drill=VIA_DRILL))

# ---------------------------------------------------------------- SMA edge launches (generic placeholder)
def fp_sma(ref, xe, y, s):
    gy = W / 2 + G + 1.0                        # centre of the top-layer ground pads
    pads_ = [pad(1, "rect", s * 1.0, 0, 2.0, W, "RF_IN" if ref == "J1" else "RF_OUT", "SIGNAL"),
             pad(2, "rect", s * 1.75, -gy, 3.5, 2.0, "GND", "GND"),
             pad(3, "rect", s * 1.75, +gy, 3.5, 2.0, "GND", "GND"),
             pad(4, "rect", s * 1.75, 0, 3.5, 5.0, "GND", "GND", layers=["B.Cu"])]
    x0 = min(0, s * 3.5)
    fp(ref, "SMA edge-launch 50R (PLACEHOLDER)", "RF_Generic:SMA_EdgeLaunch_PLACEHOLDER_" + ("W" if s > 0 else "E"), xe, y, pads_,
       (min(0, s * 3.5) - 0.2, -gy - 1.2, max(0, s * 3.5) + 0.2, gy + 1.2),
       "Generic edge-launch footprint. Replace with vendor footprint matching 0.813 mm RO4003C + 35 um Cu",
       ref_at=(s * 5.0, -3.9))

fp_sma("J1", 0.0, YIN, +1)
fp_sma("J2", BW, YOUT, -1)

# ---------------------------------------------------------------- Filter (reconstructed land pattern -> HIGH RISK)
FLX, FLY = 8.0, YIN
fp("FL1", "Johanson 2450BP14D0100001T", "RF_Generic:BPF_0603_Johanson_RECONSTRUCTED", FLX, FLY,
   [pad(2, "rect", -0.6, 0, 0.4, 0.8, "RF_IN", "I/O"),
    pad(4, "rect", +0.6, 0, 0.4, 0.8, "RF_BPF_OUT", "I/O"),
    pad(1, "rect", 0, -0.6, 0.4, 0.5, "GND", "GND"),
    pad(3, "rect", 0, +0.6, 0.4, 0.5, "GND", "GND")],
   (-1.0, -1.0, 1.0, 1.0), "Reconstructed from datasheet text; replace with Johanson CAD footprint")

# ---------------------------------------------------------------- Passives and LNA
C1X, L1X = 12.0, 18.2
fp_0402("C1", "33pF C0G", C1X, YIN, "h", -1, "RF_BPF_OUT", "RF_MATCH_A")      # series DC block
fp_0402("L1", "3.3nH RF", L1X, YIN, "h", -1, "RF_MATCH_A", "RF_LNA_IN")       # series (TOPOLOGY TO CONFIRM)

UX, UY = 21.0, YIN - 0.65                      # pin 3 (RFIN) lands on the RF centre-line
PX_L, PX_R = UX - 0.95, UX + 0.95
VCC_Y_LOW = 17.0                               # VCC line drops away from the RF output line
fp("U1", "MAX2644EXT+", "RF_Generic:SC70-6_MAX2644", UX, UY,
   [pad(1, "roundrect", -0.95, -0.65, 0.75, 0.40, "BIAS", "BIAS"),
    pad(2, "roundrect", -0.95, 0.0, 0.75, 0.40, "GND", "GND"),
    pad(3, "roundrect", -0.95, 0.65, 0.75, 0.40, "RF_LNA_IN", "RFIN"),
    pad(4, "roundrect", 0.95, 0.65, 0.75, 0.40, "+3V3", "VCC"),
    pad(5, "roundrect", 0.95, 0.0, 0.75, 0.40, "GND", "GND"),
    pad(6, "roundrect", 0.95, -0.65, 0.75, 0.40, "RF_OUT", "RFOUT")],
   (-1.5, -1.1, 1.5, 1.1), "SC70-6 generic land; verify against Analog package drawing")

# R1 (bias) vertical above pin 1; pad 1 = BIAS (lower pad), pad 2 = GND
fp_0402("R1", "1.2k 1%", PX_L, 8.72, "v", +1, "BIAS", "GND")
# C3 close to VCC pin: pad1 1.04 mm below pin-4 pad centre (datasheet 0.041 in), mounted sideways
C3_P1 = YIN + 1.04
fp_0402("C3", "15pF C0G", PX_R + 0.48, C3_P1, "h", -1, "+3V3", "GND", ref_at=(0, 1.5))
# C2 on the VCC line, 8.94 mm (0.352 in) of line length from the IC:
#   1.04 down to C3 + (VCC_Y_LOW-C3_P1) down + remaining run to the right
C2_RUN = 8.94 - 1.04 - (VCC_Y_LOW - C3_P1)
C2X = PX_R + C2_RUN
fp_0402("C2", "33pF C0G", C2X, VCC_Y_LOW + 0.48, "v", -1, "+3V3", "GND")
# J3 supply pads (THT 2.54 mm); total VCC line length IC -> J3 = 13.51 mm (0.532 in)
J3X = PX_R + (13.51 - 1.04 - (VCC_Y_LOW - C3_P1))
fp("J3", "3V3 / GND", "RF_Generic:PinHeader_1x02_P2.54mm", J3X, VCC_Y_LOW,
   [pad(1, "circle", 0, 0, 1.7, 1.7, "+3V3", "3V3", layers=["F.Cu", "B.Cu"], kind="thru_hole", drill=1.0),
    pad(2, "circle", 0, 2.54, 1.7, 1.7, "GND", "GND", layers=["F.Cu", "B.Cu"], kind="thru_hole", drill=1.0)],
   (-1.1, -1.1, 1.1, 3.64), "Supply input: pin 1 = +3.3 V, pin 2 = GND")

# ---------------------------------------------------------------- RF tracks (F.Cu)
NECK_C = 0.62
# KiCad tracks have round caps, so a 1.6 mm line projects 0.8 mm past its end points.
# Wide sections are therefore drawn shortened by W/2 at each step so the copper ends where intended.
# input: J1 pad -> wide line (ends at x=6.2) -> 0.8 -> 0.4 neck -> FL1 pin 2
track(1.6, YIN, 5.4, YIN, W, "RF_IN")
track(6.2, YIN, 6.8, YIN, 0.8, "RF_IN")
track(6.8, YIN, FLX - 0.6, YIN, 0.4, "RF_IN")
# FL1 pin 4 -> C1
track(FLX + 0.6, YIN, 9.0, YIN, 0.4, "RF_BPF_OUT")
track(9.0, YIN, 10.4, YIN, 0.8, "RF_BPF_OUT")
track(10.4, YIN, C1X - 0.48, YIN, NECK_C, "RF_BPF_OUT")
# C1 -> wide line (x 13.0..17.0) -> L1
track(C1X + 0.48, YIN, 13.0, YIN, NECK_C, "RF_MATCH_A")
track(13.8, YIN, 16.2, YIN, W, "RF_MATCH_A")
track(17.0, YIN, L1X - 0.48, YIN, NECK_C, "RF_MATCH_A")
track(L1X + 0.48, YIN, PX_L, YIN, 0.40, "RF_LNA_IN")
# output: pin 6 -> 0.4 neck -> wide line (x 24.0..) -> J2 pad
track(PX_R, YOUT, 24.0, YOUT, 0.40, "RF_OUT")
track(24.8, YOUT, BW - 1.6, YOUT, W, "RF_OUT")
# VCC line: pin 4 -> C3 node -> down -> C2 -> J3
track(PX_R, YIN, PX_R, C3_P1, T_VCC, "+3V3")
track(PX_R, C3_P1, PX_R, VCC_Y_LOW, T_VCC, "+3V3")
track(PX_R, VCC_Y_LOW, J3X, VCC_Y_LOW, T_VCC, "+3V3")
# BIAS
track(PX_L, YOUT, PX_L, 9.2, T_BIAS, "BIAS")
# ground connections of small parts
track(PX_L, YIN - 0.65, 19.4, YIN - 0.65, T_GND, "GND")                       # U1 pin 2
track(19.4, YIN - 0.65, 19.1, 11.0, T_GND, "GND"); via(19.1, 11.0)
track(PX_R, YIN - 0.65, 23.1, 11.5, T_GND, "GND"); via(23.1, 11.5)            # U1 pin 5
track(PX_L, 8.24, PX_L, 7.4, T_GND, "GND"); via(PX_L, 7.4)                    # R1
track(PX_R + 0.96, C3_P1, PX_R + 1.9, C3_P1, T_GND, "GND"); via(PX_R + 1.9, C3_P1)   # C3
track(C2X, VCC_Y_LOW + 0.96, C2X, VCC_Y_LOW + 1.9, T_GND, "GND"); via(C2X, VCC_Y_LOW + 1.9)  # C2
track(FLX, YIN + 0.6, FLX, 13.5, T_GND, "GND"); via(FLX, 13.5)                # FL1 pin 3
track(FLX, YIN - 0.6, FLX, 10.5, T_GND, "GND"); via(FLX, 10.5)                # FL1 pin 1
# connector ground-pad vias
for (vx, vy) in [(2.4, YIN - (W / 2 + G + 1.0)), (2.4, YIN + (W / 2 + G + 1.0)),
                 (BW - 2.4, YOUT - (W / 2 + G + 1.0)), (BW - 2.4, YOUT + (W / 2 + G + 1.0))]:
    via(vx, vy)

# ---------------------------------------------------------------- geometry objects
def pad_geom(fpd, p):
    cx, cy = fpd["x"] + p["dx"], fpd["y"] + p["dy"]
    if p["shape"] == "circle":
        return Point(cx, cy).buffer(p["w"] / 2, 32)
    return box(cx - p["w"] / 2, cy - p["h"] / 2, cx + p["w"] / 2, cy + p["h"] / 2)

def objects():
    objs = []
    for fpd in footprints:
        for p in fpd["pads"]:
            for ly in p["layers"]:
                objs.append(dict(kind="pad", name=f'{fpd["ref"]}.{p["num"]}', layer=ly, net=p["net"],
                                 geom=pad_geom(fpd, p)))
    for i, t in enumerate(tracks):
        objs.append(dict(kind="track", name=f"T{i}", layer=t["layer"], net=t["net"],
                         geom=LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8, cap_style=1)))
    for i, v in enumerate(vias):
        for ly in ("F.Cu", "B.Cu"):
            objs.append(dict(kind="via", name=f"V{i}", layer=ly, net=v["net"], geom=Point(v["x"], v["y"]).buffer(v["d"] / 2, 24)))
    return objs

def non_gnd_front(extra_via=None):
    return [o["geom"] for o in objects() if o["layer"] == "F.Cu" and o["net"] != "GND"]

# ---------------------------------------------------------------- automatic via fence + stitching
def add_fences():
    off = W / 2 + G + 0.3 + 0.4          # via centre offset from RF centre-line
    sections = [(2.0, 6.2, YIN), (9.2, 10.9, YIN), (13.2, 17.0, YIN), (24.0, BW - 2.0, YOUT)]
    cand = []
    for (xa, xb, yc) in sections:
        n = max(1, int((xb - xa) // 2.0))
        xs = [xa + (xb - xa) * (k + 0.5) / n for k in range(n)]
        for x in xs:
            cand += [(x, yc - off), (x, yc + off)]
    # light stitching grid for the rest of the pour
    gx = 3.0
    x = 1.5
    while x < BW - 1.0:
        y = 1.5
        while y < BH - 1.0:
            cand.append((x, y)); y += gx
        x += gx
    nong = unary_union(non_gnd_front())
    others = [o["geom"] for o in objects() if o["layer"] == "F.Cu" and o["net"] == "GND"]
    kept = []
    for (x, y) in cand:
        pt = Point(x, y).buffer(VIA_D / 2, 24)
        if x < 0.9 or x > BW - 0.9 or y < 0.9 or y > BH - 0.9:
            continue
        if pt.distance(nong) < ZONE_CLR + 0.1:
            continue
        if any(pt.distance(g) < 0.3 for g in others):
            continue
        if any(math.hypot(x - v["x"], y - v["y"]) < 1.2 for v in vias):
            continue
        via(x, y); kept.append((x, y))
        others.append(pt)
    return len(cand), len(kept)

n_cand, n_kept = add_fences()

# ---------------------------------------------------------------- KiCad file writer
def eff(size=0.8, th=0.12, hide=False):
    return f"(effects (font (size {f(size)} {f(size)}) (thickness {f(th)})){' hide' if hide else ''})"

def emit_fp(d):
    L = []
    L.append(f'  (footprint "{d["name"]}" (layer "F.Cu") (uuid "{uid()}") (at {f(d["x"])} {f(d["y"])})')
    L.append(f'    (descr "{d["descr"]}")')
    rx, ry = d.get("ref_at") or (0, d["courtyard"][1] - 0.6)
    L.append(f'    (property "Reference" "{d["ref"]}" (at {f(rx)} {f(ry)} 0) (layer "F.SilkS") (uuid "{uid()}") {eff(0.8, 0.15)})')
    L.append(f'    (property "Value" "{d["value"]}" (at 0 {f(d["courtyard"][3] + 0.6)} 0) (layer "F.Fab") (uuid "{uid()}") {eff(0.7, 0.1)})')
    L.append(f'    (path "/{SYM_UUID("sym-" + d["ref"])}")')
    smd_only = all(p["kind"] == "smd" for p in d["pads"])
    L.append(f'    (attr {"smd" if smd_only else "through_hole"})')
    x1, y1, x2, y2 = d["courtyard"]
    L.append(f'    (fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (uuid "{uid()}"))')
    for p in d["pads"]:
        net = f'(net {NID[p["net"]]} "{p["net"]}")'
        pf = f' (pinfunction "{p["func"]}")' if p["func"] else ""
        if p["kind"] == "thru_hole":
            L.append(f'    (pad "{p["num"]}" thru_hole circle (at {f(p["dx"])} {f(p["dy"])}) (size {f(p["w"])} {f(p["h"])}) (drill {f(p["drill"])}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) {net}{pf} (uuid "{uid()}"))')
        else:
            ly = p["layers"][0]
            side = "F" if ly == "F.Cu" else "B"
            lay = f'"{ly}" "{side}.Paste" "{side}.Mask"'
            rr = " (roundrect_rratio 0.25)" if p["shape"] == "roundrect" else ""
            L.append(f'    (pad "{p["num"]}" smd {p["shape"]} (at {f(p["dx"])} {f(p["dy"])}) (size {f(p["w"])} {f(p["h"])}) (layers {lay}){rr} {net}{pf} (uuid "{uid()}"))')
    L.append("  )")
    return "\n".join(L)

def write_pcb(path):
    o = []
    o.append("(kicad_pcb")
    o.append("  (version 20240108)")
    o.append('  (generator "pcbnew")')
    o.append('  (generator_version "8.0")')
    o.append(f"  (general (thickness {f(BOARD_T)}) (legacy_teardrops no))")
    o.append('  (paper "A4")')
    o.append("  (layers")
    for n, nm, ty, alias in [(0, "F.Cu", "signal", None), (31, "B.Cu", "signal", None),
                             (32, "B.Adhes", "user", "B.Adhesive"), (33, "F.Adhes", "user", "F.Adhesive"),
                             (34, "B.Paste", "user", None), (35, "F.Paste", "user", None),
                             (36, "B.SilkS", "user", "B.Silkscreen"), (37, "F.SilkS", "user", "F.Silkscreen"),
                             (38, "B.Mask", "user", None), (39, "F.Mask", "user", None),
                             (40, "Dwgs.User", "user", "User.Drawings"), (41, "Cmts.User", "user", "User.Comments"),
                             (42, "Eco1.User", "user", "User.Eco1"), (43, "Eco2.User", "user", "User.Eco2"),
                             (44, "Edge.Cuts", "user", None), (45, "Margin", "user", None),
                             (46, "B.CrtYd", "user", "B.Courtyard"), (47, "F.CrtYd", "user", "F.Courtyard"),
                             (48, "B.Fab", "user", None), (49, "F.Fab", "user", None)]:
        o.append(f'    ({n} "{nm}" {ty}' + (f' "{alias}"' if alias else "") + ")")
    o.append("  )")
    o.append("  (setup")
    o.append("    (stackup")
    o.append('      (layer "F.SilkS" (type "Top Silk Screen"))')
    o.append('      (layer "F.Paste" (type "Top Solder Paste"))')
    o.append('      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))')
    o.append('      (layer "F.Cu" (type "copper") (thickness 0.035))')
    o.append('      (layer "dielectric 1" (type "core") (thickness 0.813) (material "Rogers RO4003C") (epsilon_r 3.55) (loss_tangent 0.0027))')
    o.append('      (layer "B.Cu" (type "copper") (thickness 0.035))')
    o.append('      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))')
    o.append('      (layer "B.Paste" (type "Bottom Solder Paste"))')
    o.append('      (layer "B.SilkS" (type "Bottom Silk Screen"))')
    o.append('      (copper_finish "ENIG")')
    o.append("      (dielectric_constraints no)")
    o.append("    )")
    o.append("    (pad_to_mask_clearance 0)")
    o.append("    (allow_soldermask_bridges_in_footprints no)")
    o.append("  )")
    for n, nm in enumerate(NETS):
        o.append(f'  (net {n} "{nm}")')
    for d in footprints:
        o.append(emit_fp(d))
    for t in tracks:
        o.append(f'  (segment (start {f(t["x1"])} {f(t["y1"])}) (end {f(t["x2"])} {f(t["y2"])}) (width {f(t["w"])}) (layer "{t["layer"]}") (net {NID[t["net"]]}) (uuid "{uid()}"))')
    for v in vias:
        o.append(f'  (via (at {f(v["x"])} {f(v["y"])}) (size {f(v["d"])}) (drill {f(v["drill"])}) (layers "F.Cu" "B.Cu") (net {NID[v["net"]]}) (uuid "{uid()}"))')
    # board outline
    o.append(f'  (gr_rect (start 0 0) (end {f(BW)} {f(BH)}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{uid()}"))')
    # silkscreen labels
    for (txt, x, y) in [("RF IN", 5.0, 5.0), ("RF OUT", 33.0, 5.0), ("+3V3", J3X + 1.4, VCC_Y_LOW + 0.5),
                        ("GND", J3X + 1.4, VCC_Y_LOW + 3.0), ("2G4 LNA FE  RO4003C 0.813", 5.0, 21.5)]:
        o.append(f'  (gr_text "{txt}" (at {f(x)} {f(y)} 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15)) (justify left bottom)))')
    # ground pours (unfilled; press B in pcbnew to fill)
    ins = 0.3
    for ly in ("F.Cu", "B.Cu"):
        o.append(f'  (zone (net {NID["GND"]}) (net_name "GND") (layer "{ly}") (uuid "{uid()}") (hatch edge 0.5)')
        o.append(f'    (connect_pads yes (clearance {f(ZONE_CLR)}))')
        o.append('    (min_thickness 0.2) (filled_areas_thickness no)')
        o.append(f'    (fill (thermal_gap {f(ZONE_CLR)}) (thermal_bridge_width 0.3))')
        o.append(f'    (polygon (pts (xy {f(ins)} {f(ins)}) (xy {f(BW - ins)} {f(ins)}) (xy {f(BW - ins)} {f(BH - ins)}) (xy {f(ins)} {f(BH - ins)})))')
        o.append("  )")
    o.append(")")
    open(path, "w").write("\n".join(o) + "\n")

def emit_mod(d):
    """Library (.kicad_mod) version of a board footprint: no nets, no position."""
    short = d["name"].split(":")[1]
    x1, y1, x2, y2 = d["courtyard"]
    smd_only = all(p["kind"] == "smd" for p in d["pads"])
    L = [f'(footprint "{short}" (version 20240108) (generator "pcbnew") (generator_version "8.0") (layer "F.Cu")',
         f'  (descr "{d["descr"]}")',
         f'  (property "Reference" "REF**" (at 0 {f(y1 - 0.6)} 0) (layer "F.SilkS") {eff(0.8, 0.15)})',
         f'  (property "Value" "{short}" (at 0 {f(y2 + 0.6)} 0) (layer "F.Fab") {eff(0.7, 0.1)})',
         f'  (attr {"smd" if smd_only else "through_hole"})',
         f'  (fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))']
    for p in d["pads"]:
        if p["kind"] == "thru_hole":
            L.append(f'  (pad "{p["num"]}" thru_hole circle (at {f(p["dx"])} {f(p["dy"])}) (size {f(p["w"])} {f(p["h"])}) (drill {f(p["drill"])}) (layers "*.Cu" "*.Mask") (remove_unused_layers no))')
        else:
            ly = p["layers"][0]; side = "F" if ly == "F.Cu" else "B"
            rr = " (roundrect_rratio 0.25)" if p["shape"] == "roundrect" else ""
            L.append(f'  (pad "{p["num"]}" smd {p["shape"]} (at {f(p["dx"])} {f(p["dy"])}) (size {f(p["w"])} {f(p["h"])}) (layers "{ly}" "{side}.Paste" "{side}.Mask"){rr})')
    L.append(")")
    return "\n".join(L) + "\n"


def write_support(outdir):
    import os
    lib = os.path.join(outdir, "RF_Generic.pretty")
    os.makedirs(lib, exist_ok=True)
    seen = {}
    for d in footprints:
        seen.setdefault(d["name"], d)
    for name, d in seen.items():
        open(os.path.join(lib, name.split(":")[1] + ".kicad_mod"), "w").write(emit_mod(d))
    open(os.path.join(outdir, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "RF_Generic")(type "KiCad")(uri "${KIPRJMOD}/RF_Generic.pretty")(options "")'
        '(descr "Generic placeholder footprints for the 2.4 GHz front-end"))\n)\n')
    # SMA edge-launch pads must reach the board edge: waive the edge rule for pads only (tracks, vias, zones keep 0.3 mm)
    open(os.path.join(outdir, "2G4_RF_Receiver_FrontEnd.kicad_dru"), "w").write(
        '(version 1)\n'
        '(rule "Edge-launch connector pads may reach the board edge"\n'
        '  (constraint edge_clearance (min 0mm))\n'
        '  (condition "A.Type == \'Pad\'"))\n')
    return sorted(seen)


if __name__ == "__main__":
    out = "/home/claude/rf_pcb/2G4_RF_Receiver_FrontEnd.kicad_pcb"
    write_pcb(out)
    libs = write_support("/home/claude/rf_pcb")
    print("library footprints:", libs)
    json.dump(dict(W=W, G=G, BW=BW, BH=BH, YIN=YIN, YOUT=YOUT, n_fp=len(footprints), n_tracks=len(tracks),
                   n_vias=len(vias), fence_candidates=n_cand, fence_kept=n_kept), open("/home/claude/rf_pcb/gen_summary.json", "w"), indent=1)
    print("wrote", out, "| footprints", len(footprints), "tracks", len(tracks), "vias", len(vias), f"(candidates {n_cand}, kept {n_kept})")
