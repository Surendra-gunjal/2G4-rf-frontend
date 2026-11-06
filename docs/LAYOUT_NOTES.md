# 2.4 GHz RF front-end: PCB layout draft (rev A)

**Status: LAYOUT DRAFT. Not fabrication-validated.** Do not send to a fab until the "Before fabrication" list below is closed.

## What is in the file
- `2G4_RF_Receiver_FrontEnd.kicad_pcb` (KiCad 8 format): 40 x 24 mm outline, 2 copper layers, 10 footprints, 24 tracks, 104 GND vias, GND zones on F.Cu and B.Cu (not pre-filled).
- Stack-up written into the file: F.Cu 35 um / Rogers RO4003C 0.813 mm (design Dk 3.55, Df 0.0027) / B.Cu 35 um. B.Cu is a solid ground plane.
- Signal flow, left to right: J1 (SMA in) > FL1 (BPF) > C1 (33 pF series) > L1 (3.3 nH) > U1 pin 3 ... U1 pin 6 > J2 (SMA out).
- Bias: R1 1.2 k from U1 pin 1 to GND. Supply: J3 (+3.3 V / GND) > narrow VCC line > C2 33 pF > C3 15 pF > U1 pin 4.

## RF line geometry
| Item | Value |
|---|---|
| Line type | Grounded coplanar waveguide (top-side pour at 0.30 mm gap, solid ground below, via fence) |
| Width / gap | 1.60 mm / 0.30 mm (pour clearance is set equal to the gap) |
| Solver result | 50.3 ohm at Dk 3.55; 49.3 ohm at Dk 3.38 |
| Solver accuracy | About +/-2.5 percent (a validation case on FR4 read 51.2 ohm against a 50 ohm closed-form value) |
| Not modelled | Copper plating build-up, solder mask, thickness tolerance, loss |
| Closed-form microstrip for comparison | 1.82 mm (Hammerstad-Jensen); not used |

The 1.6 mm line steps down to 0.62 / 0.4 mm necks at the component pads. These are short stepped discontinuities and have not been simulated.

## Datasheet spacing implemented (MAX2644)
- C3 pad to U1 pin 4: 1.04 mm (datasheet 0.041 in).
- C2 pad along the VCC line: 8.94 mm (datasheet 0.352 in).
- VCC line to J3: 13.51 mm, 0.30 mm wide (datasheet 0.532 in x 0.012 in).
- Both GND pins have their own via next to the package.

## Checks run (script, on the written file)
- Parses and round-trips in kiutils (KiCad 8 syntax). **Not opened in KiCad; no DRC or ERC was run.**
- Minimum different-net clearance 0.20 mm; nothing below 0.15 mm.
- Copper-to-edge at least 0.3 mm (connector pads excepted).
- All 7 non-GND nets are single connected groups.
- Modelled F.Cu pour is one contiguous piece with no via-less islands; CPW gap to the pour is 0.30 mm on every 1.6 mm section.
- Via-fence pitch at most 2.75 mm (lambda/20 is about 4 mm at 2.45 GHz).

## Before fabrication (open items)
1. **LNA input network topology.** I could not read the datasheet schematic figure (the text extraction drops the drawing and the sandbox blocked the PDF download). L1 is placed in series between C1 and U1 pin 3. Confirm against Figure 1/2 of the MAX2644 datasheet.
2. **C3 and L2 mismatch in the BOM.** Datasheet Figure 1 (high gain) uses C3 = 2.2 pF. Figure 2 (high linearity) uses C3 = 15 pF and also lists L2 = 3.9 nH. Your README and BOM have C3 = 15 pF but no L2. Pick one variant. This layout has no L2 footprint.
3. **FL1 footprint is reconstructed** from datasheet dimension text. I/O terminals are assumed to be on the short ends. Replace it with Johanson's CAD footprint.
4. **SMA footprints are generic placeholders.** Use the vendor footprint for your connector at 0.813 mm / 35 um copper, then re-check the gap to the pour.
5. **U1 (SC70-6) and 0402 land patterns are generic.** Use the manufacturer drawings.
6. **VCC line interpretation.** I read the datasheet's 0.532 in x 0.012 in line and the C2/C3 distances as the VCC feed. The datasheet wording is ambiguous and its values are for the evaluation board's substrate.
7. **Simulation or measurement.** Run a field-solver/EM check of the stepped transitions and the connector launches, and measure a test coupon or board.
8. **Fill and run DRC.** Press B in pcbnew to fill zones, then run DRC against your fab's rules. The `.kicad_pro` is minimal.
9. **Ask the fab** to confirm RO4003C 0.813 mm availability, the Dk used for impedance control, final copper thickness, and 0.30 mm via drill capability.

## Design note
The BPF sits ahead of the LNA, so its 1.5 to 1.7 dB insertion loss adds almost directly to the system noise figure (LNA NF is 2.0 dB typical, 2.5 dB max).

## Schematic (`2G4_RF_Receiver_FrontEnd.kicad_sch`, rev A draft)
- Single A4 sheet, KiCad 8 format, all symbols embedded (no external library needed).
- 30 symbol pins vs 30 PCB pads: net names agree on every one (independent netlist extraction from the file, no mismatches, no shorts, no floating pins).
- Each PCB footprint carries a link to its schematic symbol, so Tools > Update PCB from Schematic (F8) should associate them by link instead of creating duplicates.
- Footprint fields point at the `RF_Generic:*` names used on the board. No such library exists yet, so KiCad may warn that these footprints cannot be found in a library. Keep the existing board footprints, or replace them with vendor footprints.
- SMA symbols have pins 2-4 stacked at one point (the three ground pads of the edge-launch footprint). KiCad may show a stacked-pin warning in ERC.
- **Not done: ERC was not run in KiCad.** PWR_FLAGs are placed on +3V3 and GND so power-pin ERC should not complain about undriven nets.
- The topology open items (L1 position, C3 / L2 variant) apply to the schematic too; they are listed in the sheet notes.
