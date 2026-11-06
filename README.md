# 2.4 GHz RF Receiver Front-End (MAX2644 LNA + 2.4 GHz band-pass filter)

KiCad 8 project for a 2.4 GHz receiver front end: SMA in, Johanson 2450BP14D0100001T band-pass filter, MAX2644 LNA with the datasheet input match, 3.3 V supply, SMA out. Board stack-up: Rogers RO4003C 0.813 mm, 35 um copper, grounded coplanar waveguide RF lines (W 1.6 mm, gap 0.3 mm).

**Status: layout draft. Not fabrication-validated.** Run DRC and ERC in KiCad and read `docs/LAYOUT_NOTES.md` (open items and a pre-fabrication checklist) before ordering boards.

## Layout
- `hardware/` KiCad project (`.kicad_pcb`, `.kicad_sch`, `.kicad_pro`) and the generic footprint library
- `scripts/` Python that generates the PCB and schematic from parameters, a 50 ohm line solver, and geometry/netlist checks
- `docs/` layout notes, previews, and the project plan (`RF_Frontend_Project_Plan.xlsx`)
- `reference/` the original README and BOM the design started from

## Regenerating
```
cd scripts
python3 gen_pcb.py   # needs: shapely
python3 gen_sch.py
```
Paths inside the scripts point at the original working folder; edit the output paths at the top of each script first.

## Known limitations
- Footprints for the SMA connectors, filter and SC70-6 are generic placeholders; use the vendor footprints.
- The input-match topology (L1 position) and the C3 / L2 variant must be confirmed against the MAX2644 datasheet.
- The 50 ohm width comes from a quasi-static solver (about +/-2.5%), not an EM simulation or measurement.
