2.4 GHz RF Receiver Front-End — Reference Design Draft B
========================================================

Files
-----
2G4_RF_Receiver_FrontEnd.kicad_sch
    KiCad schematic-page reference drawing with selected components and values.
2G4_RF_Receiver_BOM.csv
    Bill of materials and supplier/manufacturer links.

Design basis
------------
The LNA was changed from MAX2641 to MAX2644 because the MAX2644 datasheet gives
a manufacturer-recommended input matching circuit at 2450 MHz and an on-chip
output match. Reference values used here: C1=33 pF, L1=3.3 nH, R1=1.2 kOhm,
C2=33 pF, C3=15 pF. The exact circuit topology and placement must follow the
MAX2644 datasheet schematic and layout guidance. Do not infer topology solely
from this overview page.

Chosen filter
-------------
Johanson 2450BP14D0100001T, 0603, 2400-2500 MHz passband. Datasheet lists 1.5 dB
typical and 1.7 dB maximum insertion loss, so the original <=1.5 dB maximum
filter-loss target is not guaranteed.

Important limitation
--------------------
This is NOT a fabrication-ready KiCad electrical schematic/PCB layout. It is a
component-level reference page. The values come from the manufacturer's
reference circuit, not an independent optimization or a full RF simulation.
Before fabrication, confirm actual KiCad symbol pin numbering and topology
against the MAX2644 datasheet, choose exact footprints, add all actual nets,
specify board stack-up, calculate 50-ohm trace width using the chosen laminate
thickness/copper, simulate/measure, and run ERC/DRC.

Official sources
----------------
MAX2644: https://www.analog.com/en/products/max2644.html
MAX2644 datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/MAX2644.pdf
Filter: https://www.johansontechnology.com/products/integrated-passives/band-pass-filters/2450bp14d0100001t/
Filter datasheet: https://www.johansontechnology.com/docs/4650/BandPassFilter-2450BP14D0100001T-Rev3.0.pdf
Rogers RO4003C: https://www.rogerscorp.com/advanced-electronics-solutions/ro4000-series-laminates/ro4003c-laminates
