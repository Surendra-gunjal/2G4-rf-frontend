#!/usr/bin/env python3
"""Generate 2G4_RF_Receiver_FrontEnd.kicad_sch (KiCad 8 format).

Net names, references, pin numbers and footprint names match gen_pcb.py / the .kicad_pcb.
All symbols are embedded in lib_symbols, so no external library is needed.
"""
from ids import U

PROJ = "2G4_RF_Receiver_FrontEnd"
ROOT = U("root-sheet")
OUT = "/home/claude/rf_pcb/2G4_RF_Receiver_FrontEnd.kicad_sch"


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def eff(size=1.27, hide=False, just=None):
    s = f"(effects (font (size {size} {size}))"
    if just:
        s += f" (justify {just})"
    if hide:
        s += " hide"
    return s + ")"


# ------------------------------------------------------------------ library symbols
LIBS = {}  # lib_id -> dict(text, pins{num:(x,y)})


def mksym(lib_id, ref, value, body, pins, *, hide_names=False, hide_numbers=False, power=False,
          in_bom=True, ref_at=(0, 2.54), val_at=(0, -2.54), name_off=0.254, unit_style="1_1"):
    short = lib_id.split(":")[1]
    t = [f'    (symbol "{lib_id}"']
    if power:
        t.append("      (power)")
    if hide_numbers:
        t.append("      (pin_numbers hide)")
    if hide_names or name_off != 0.254:
        t.append(f"      (pin_names (offset {f(name_off)}){' hide' if hide_names else ''})")
    t.append(f"      (exclude_from_sim no) (in_bom {'yes' if in_bom else 'no'}) (on_board yes)")
    t.append(f'      (property "Reference" "{ref}" (at {f(ref_at[0])} {f(ref_at[1])} 0) {eff(hide=power)})')
    t.append(f'      (property "Value" "{value}" (at {f(val_at[0])} {f(val_at[1])} 0) {eff()})')
    t.append(f'      (property "Footprint" "" (at 0 0 0) {eff(hide=True)})')
    t.append(f'      (property "Datasheet" "~" (at 0 0 0) {eff(hide=True)})')
    t.append(f'      (symbol "{short}_0_1"')
    for g in body:
        t.append("        " + g)
    t.append("      )")
    t.append(f'      (symbol "{short}_{unit_style}"')
    pd = {}
    for p in pins:
        hid = " hide" if p.get("hide") else ""
        t.append(f'        (pin {p["type"]} line (at {f(p["x"])} {f(p["y"])} {p["ang"]}) (length {f(p["len"])}){hid} '
                 f'(name "{p["name"]}" {eff()}) (number "{p["num"]}" {eff()}))')
        pd[p["num"]] = (p["x"], p["y"])
    t.append("      )")
    t.append("    )")
    LIBS[lib_id] = dict(text="\n".join(t), pins=pd)


STROKE = "(stroke (width 0.254) (type default))"
NOFILL = "(fill (type none))"
BG = "(fill (type background))"


def rect(x1, y1, x2, y2):
    return f"(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) {STROKE} {BG})"


def poly(pts, w=0.254):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return f"(polyline (pts {p}) (stroke (width {w}) (type default)) {NOFILL})"


def P(num, name, typ, x, y, ang, ln=2.54, hide=False):
    return dict(num=str(num), name=name, type=typ, x=x, y=y, ang=ang, len=ln, hide=hide)


# Passives (standard Device geometry: pin 1 at +3.81, pin 2 at -3.81)
mksym("Device:C", "C", "C", [poly([(-2.032, -0.762), (2.032, -0.762)], 0.508), poly([(-2.032, 0.762), (2.032, 0.762)], 0.508)],
      [P(1, "~", "passive", 0, 3.81, 270, 2.794), P(2, "~", "passive", 0, -3.81, 90, 2.794)],
      hide_numbers=True, hide_names=True)
mksym("Device:R", "R", "R", [rect(-1.016, 2.54, 1.016, -2.54)],
      [P(1, "~", "passive", 0, 3.81, 270, 1.27), P(2, "~", "passive", 0, -3.81, 90, 1.27)],
      hide_numbers=True, hide_names=True)
arcs = []
for (a, b, c) in [(-2.54, -1.905, -1.27), (-1.27, -0.635, 0), (0, 0.635, 1.27), (1.27, 1.905, 2.54)]:
    arcs.append(f"(arc (start 0 {f(a)}) (mid 0.6323 {f(b)}) (end 0 {f(c)}) {STROKE} {NOFILL})")
mksym("Device:L", "L", "L", arcs,
      [P(1, "1", "passive", 0, 3.81, 270, 1.27), P(2, "2", "passive", 0, -3.81, 90, 1.27)],
      hide_numbers=True, hide_names=True)

# SMA edge launch: pin 1 = signal, pins 2-4 = shield (stacked, same as the 3 ground pads on the PCB footprint)
sma_body = [rect(-2.54, 2.54, 2.54, -2.54), f"(circle (center 0 0) (radius 1.27) {STROKE} {NOFILL})"]
shield = [P(2, "Shield", "passive", 0, -5.08, 90), P(3, "Shield", "passive", 0, -5.08, 90, hide=True),
          P(4, "Shield", "passive", 0, -5.08, 90, hide=True)]
mksym("RF_Generic:SMA_R", "J", "SMA", sma_body, [P(1, "Signal", "passive", 5.08, 0, 180)] + shield,
      ref_at=(0, 5.08), val_at=(0, -7.62), hide_numbers=True)
mksym("RF_Generic:SMA_L", "J", "SMA", sma_body, [P(1, "Signal", "passive", -5.08, 0, 0)] + shield,
      ref_at=(0, 5.08), val_at=(0, -7.62), hide_numbers=True)

# Band-pass filter 0603, 4 terminals (2,4 = I/O; 1,3 = GND)
mksym("RF_Generic:BPF_4T", "FL", "BPF",
      [rect(-5.08, 5.08, 5.08, -5.08), '(text "BPF" (at 0 0 0) (effects (font (size 1.27 1.27))))'],
      [P(2, "I/O", "passive", -7.62, 0, 0), P(4, "I/O", "passive", 7.62, 0, 180),
       P(1, "GND", "passive", -2.54, -7.62, 90), P(3, "GND", "passive", 2.54, -7.62, 90)],
      ref_at=(0, 7.62), val_at=(0, 10.16))

# MAX2644 SC70-6
mksym("RF_Generic:MAX2644", "U", "MAX2644",
      [rect(-7.62, 7.62, 7.62, -7.62), '(text "MAX2644" (at 0 0 0) (effects (font (size 1.27 1.27))))'],
      [P(3, "RFIN", "passive", -10.16, 0, 0), P(1, "BIAS", "passive", -10.16, -5.08, 0),
       P(6, "RFOUT", "passive", 10.16, 0, 180), P(4, "VCC", "power_in", 2.54, 10.16, 270),
       P(2, "GND", "power_in", -2.54, -10.16, 90), P(5, "GND", "power_in", 2.54, -10.16, 90)],
      ref_at=(9.0, 5.08), val_at=(9.0, -5.08))

# Supply connector (pin 1 = +3V3, pin 2 = GND)
mksym("RF_Generic:Conn_Supply_2", "J", "Conn",
      [rect(-2.54, 2.54, 2.54, -7.62)],
      [P(1, "+3V3", "passive", -5.08, 0, 0), P(2, "GND", "passive", -5.08, -5.08, 0)],
      ref_at=(0, 5.08), val_at=(0, 7.62))

# Power symbols
mksym("power:GND", "#PWR", "GND",
      [poly([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)], 0)],
      [P(1, "GND", "power_in", 0, 0, 270, 0, hide=True)],
      hide_names=True, hide_numbers=True, power=True, in_bom=False, ref_at=(0, -6.35), val_at=(0, -3.81), name_off=0)
mksym("power:+3V3", "#PWR", "+3V3",
      [poly([(-0.762, 1.27), (0, 2.54)], 0), poly([(0, 0), (0, 2.54)], 0), poly([(0, 2.54), (0.762, 1.27)], 0)],
      [P(1, "+3V3", "power_in", 0, 0, 90, 0, hide=True)],
      hide_names=True, hide_numbers=True, power=True, in_bom=False, ref_at=(0, -3.81), val_at=(0, 3.81), name_off=0)
mksym("power:PWR_FLAG", "#FLG", "PWR_FLAG",
      [poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)], 0)],
      [P(1, "pwr", "power_out", 0, 0, 90, 0)],
      hide_names=False, hide_numbers=True, power=True, in_bom=False, ref_at=(0, 3.81), val_at=(0, 3.81), name_off=0)

# ------------------------------------------------------------------ placement
SYMS = {}       # ref -> dict
ELEMS = []      # text blocks
_pw = [0, 0]


def place(lib_id, ref, value, x, y, rot=0, fp="", ds="~", ref_at=None, val_at=None, just="left", key=None):
    power = lib_id.startswith("power:")
    if power:
        k = "pwr" if "PWR_FLAG" not in lib_id else "flg"
        _pw[0 if k == "pwr" else 1] += 1
        ref = f"#PWR{_pw[0]:02d}" if k == "pwr" else f"#FLG{_pw[1]:02d}"
        uid = U("sym-" + ref)
    else:
        uid = U("sym-" + ref)
    SYMS[ref] = dict(lib=lib_id, x=x, y=y, rot=rot, value=value, fp=fp, ds=ds, uid=uid, power=power,
                     ref_at=ref_at, val_at=val_at, just=just)
    return ref


def pin_pos(ref, num):
    s = SYMS[ref]
    px, py = LIBS[s["lib"]]["pins"][str(num)]
    rx, ry = {0: (px, py), 90: (-py, px), 180: (-px, -py), 270: (py, -px)}[s["rot"] % 360]
    return (round(s["x"] + rx, 4), round(s["y"] - ry, 4))


WIRES, LABELS, JUNCS = [], [], []


def wire(a, b):
    WIRES.append((a, b))


def label(name, x, y):
    LABELS.append((name, x, y))


def junction(x, y):
    JUNCS.append((x, y))


Y = 101.6
CAP_FP = "RF_Generic:C_R_L_0402"
# --- RF chain
J1 = place("RF_Generic:SMA_R", "J1", "SMA edge-launch (RF IN)", 50.8, Y, fp="RF_Generic:SMA_EdgeLaunch_PLACEHOLDER",
           ref_at=(50.8, Y - 5.08), val_at=(50.8, Y - 7.62), just="center")
FL1 = place("RF_Generic:BPF_4T", "FL1", "2450BP14D0100001T", 88.9, Y, fp="RF_Generic:BPF_0603_Johanson_RECONSTRUCTED",
            ds="https://www.johansontechnology.com/docs/4650/BandPassFilter-2450BP14D0100001T-Rev3.0.pdf",
            ref_at=(88.9, Y - 7.62), val_at=(88.9, Y - 10.16), just="center")
C1 = place("Device:C", "C1", "33pF C0G", 121.92, Y, rot=90, fp=CAP_FP, ref_at=(121.92, Y - 3.81), val_at=(121.92, Y + 3.81), just="center")
L1 = place("Device:L", "L1", "3.3nH", 152.4, Y, rot=90, fp=CAP_FP, ref_at=(152.4, Y - 3.81), val_at=(152.4, Y + 3.81), just="center")
U1 = place("RF_Generic:MAX2644", "U1", "MAX2644EXT+", 190.5, Y, fp="RF_Generic:SC70-6_MAX2644",
           ds="https://www.analog.com/media/en/technical-documentation/data-sheets/MAX2644.pdf",
           ref_at=(199.5, Y - 5.08), val_at=(199.5, Y + 5.08))
J2 = place("RF_Generic:SMA_L", "J2", "SMA edge-launch (RF OUT)", 233.68, Y, fp="RF_Generic:SMA_EdgeLaunch_PLACEHOLDER",
           ref_at=(238.76, Y - 1.27), val_at=(238.76, Y + 1.27))
R1 = place("Device:R", "R1", "1.2k 1%", 170.18, 114.3, fp=CAP_FP, ref_at=(172.72, 113.03), val_at=(172.72, 115.57))
C3 = place("Device:C", "C3", "15pF C0G", 203.2, 90.17, fp=CAP_FP, ref_at=(205.74, 88.9), val_at=(205.74, 91.44))
C2 = place("Device:C", "C2", "33pF C0G", 215.9, 90.17, fp=CAP_FP, ref_at=(218.44, 88.9), val_at=(218.44, 91.44))
J3 = place("RF_Generic:Conn_Supply_2", "J3", "3V3 / GND", 243.84, 83.82, fp="RF_Generic:PinHeader_1x02_P2.54mm",
           ref_at=(243.84, 78.74), val_at=(243.84, 76.2), just="center")

# signal wires + net labels (names equal the PCB nets)
def run(a, b, name):
    pa, pb = pin_pos(*a), pin_pos(*b)
    wire(pa, pb)
    label(name, pa[0] + 2.54, pa[1])

run((J1, 1), (FL1, 2), "RF_IN")
run((FL1, 4), (C1, 1), "RF_BPF_OUT")
run((C1, 2), (L1, 1), "RF_MATCH_A")
run((L1, 2), (U1, 3), "RF_LNA_IN")
run((U1, 6), (J2, 1), "RF_OUT")

# bias
pb = pin_pos(U1, 1); pr = pin_pos(R1, 1)
corner = (pr[0], pb[1])
wire(pb, corner); wire(corner, pr)
label("BIAS", pr[0] + 2.54, pb[1])

# VCC bus
BY = 83.82
pv = pin_pos(U1, 4)
top = (pv[0], BY)
wire(pv, top)
x_c3, x_c2 = pin_pos(C3, 1)[0], pin_pos(C2, 1)[0]
P33 = place("power:+3V3", "", "+3V3", 226.06, BY)
FLG1 = place("power:PWR_FLAG", "", "PWR_FLAG", 233.68, BY)
xj = pin_pos(J3, 1)[0]
xs = [top[0], x_c3, x_c2, 226.06, 233.68, xj]
for a, b in zip(xs, xs[1:]):
    wire((a, BY), (b, BY))
for xc, c in ((x_c3, C3), (x_c2, C2)):
    wire((xc, BY), pin_pos(c, 1))
    junction(xc, BY)

# ground symbols
def gnd(ref, num, rot=0):
    x, y = pin_pos(ref, num)
    place("power:GND", "", "GND", x, y)

for ref, num in [(J1, 2), (J2, 2), (FL1, 1), (FL1, 3), (U1, 2), (U1, 5), (R1, 2), (C3, 2), (C2, 2)]:
    gnd(ref, num)
pg = pin_pos(J3, 2)
gx = pg[0] - 5.08
wire(pg, (gx, pg[1])); wire((gx, pg[1]), (gx - 10.16, pg[1]))
place("power:GND", "", "GND", gx, pg[1])
place("power:PWR_FLAG", "", "PWR_FLAG", gx - 10.16, pg[1], rot=180)

NOTES = ("2.4 GHz RF RECEIVER FRONT-END - SCHEMATIC DRAFT (rev A)\\n"
         "Net names, references and pin numbers match 2G4_RF_Receiver_FrontEnd.kicad_pcb (cross-checked by script).\\n"
         "ERC has not been run in KiCad.\\n\\n"
         "OPEN ITEMS (details in LAYOUT_NOTES.md)\\n"
         "1. L1 is drawn in series after C1. Confirm the input match topology against the MAX2644 datasheet Fig. 1 / Fig. 2.\\n"
         "2. C3: Fig. 1 (high gain) uses 2.2 pF. Fig. 2 (high linearity) uses 15 pF and adds L2 = 3.9 nH, which is not placed here.\\n"
         "   The BOM lists C3 = 15 pF and no L2.\\n"
         "3. Datasheet VCC bypass spacing from U1: C3 0.041 in, C2 0.352 in, supply line 0.532 in x 0.012 in (layout constraint).\\n"
         "4. FL1 insertion loss (1.5 dB typ / 1.7 dB max) sits ahead of the LNA and adds to system noise figure.\\n"
         "5. R1 sets bias current. Leaving BIAS open puts the LNA in standby.\\n"
         "6. RF lines are 50 ohm grounded coplanar waveguide on RO4003C 0.813 mm (W 1.6 mm, gap 0.3 mm).")


# ------------------------------------------------------------------ writer
def sym_text(ref, s):
    lib = LIBS[s["lib"]]
    x, y = s["x"], s["y"]
    ra = s["ref_at"] or (x + 2.54, y - 1.27)
    va = s["val_at"] or (x + 2.54, y + 1.27)
    j = f" (justify {s['just']})" if s["just"] else ""
    jf = "" if s["just"] == "center" else j
    out = [f'  (symbol (lib_id "{s["lib"]}") (at {f(x)} {f(y)} {s["rot"]}) (unit 1) (exclude_from_sim no) '
           f'(in_bom {"no" if s["power"] else "yes"}) (on_board yes) (dnp no) (uuid "{s["uid"]}")']
    if s["power"]:
        out.append(f'    (property "Reference" "{ref}" (at {f(x)} {f(y)} 0) {eff(hide=True)})')
        # graphic of GND points down; +3V3 and PWR_FLAG point up (PWR_FLAG rotated 180 points down)
        down = ("GND" in s["lib"] and s["rot"] == 0) or ("PWR_FLAG" in s["lib"] and s["rot"] == 180)
        vy = y + (3.81 if down else -3.81)
        out.append(f'    (property "Value" "{s["value"]}" (at {f(x)} {f(vy)} 0) {eff()})')
    else:
        out.append(f'    (property "Reference" "{ref}" (at {f(ra[0])} {f(ra[1])} 0) {eff(just=None if s["just"] == "center" else "left")})')
        out.append(f'    (property "Value" "{s["value"]}" (at {f(va[0])} {f(va[1])} 0) {eff(just=None if s["just"] == "center" else "left")})')
    out.append(f'    (property "Footprint" "{s["fp"]}" (at {f(x)} {f(y)} 0) {eff(hide=True)})')
    out.append(f'    (property "Datasheet" "{s["ds"]}" (at {f(x)} {f(y)} 0) {eff(hide=True)})')
    for num in lib["pins"]:
        out.append(f'    (pin "{num}" (uuid "{U("pin-" + ref + "-" + num)}"))')
    out.append(f'    (instances (project "{PROJ}" (path "/{ROOT}" (reference "{ref}") (unit 1))))')
    out.append("  )")
    return "\n".join(out)


def write():
    from gen_pcb import footprints as _pcb_fps
    names = {d["ref"]: d["name"] for d in _pcb_fps}
    for ref, s in SYMS.items():
        if not s["power"]:
            s["fp"] = names[ref]
    o = ["(kicad_sch", "  (version 20231120)", '  (generator "eeschema")', '  (generator_version "8.0")',
         f'  (uuid "{ROOT}")', '  (paper "A4")', "  (title_block",
         '    (title "2.4 GHz RF Receiver Front-End (MAX2644 LNA)")', '    (date "2026-10-12")', '    (rev "A")',
         '    (comment 1 "SCHEMATIC DRAFT - not fabrication validated")',
         '    (comment 2 "Matches 2G4_RF_Receiver_FrontEnd.kicad_pcb (RO4003C 0.813 mm)")', "  )", "  (lib_symbols"]
    for lib in LIBS.values():
        o.append(lib["text"])
    o.append("  )")
    for (x, y) in JUNCS:
        o.append(f'  (junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U(f"junc-{x}-{y}")}"))')
    for i, ((x1, y1), (x2, y2)) in enumerate(WIRES):
        o.append(f'  (wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U(f"wire-{i}")}"))')
    for i, (n, x, y) in enumerate(LABELS):
        o.append(f'  (label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U(f"label-{i}")}"))')
    o.append(f'  (text "{NOTES}" (exclude_from_sim no) (at 25.4 134.62 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid "{U("notes")}"))')
    for ref, s in SYMS.items():
        o.append(sym_text(ref, s))
    o.append('  (sheet_instances (path "/" (page "1")))')
    o.append(")")
    open(OUT, "w").write("\n".join(o) + "\n")


if __name__ == "__main__":
    write()
    print("wrote", OUT, "| symbols", len(SYMS), "wires", len(WIRES), "labels", len(LABELS), "junctions", len(JUNCS))
