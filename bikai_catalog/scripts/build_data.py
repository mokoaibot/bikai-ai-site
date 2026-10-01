#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIKAI product catalog — source data builder.
Produces catalog/data/products.json from manually transcribed scrape results
(bikaicorp.com = primary source for instruments, uvtech-cc.com = source for
Sample Treatment + all Consumables). See catalog/data/SOURCES.md for provenance.

Design goal: adding a new product later = append one dict to PRODUCTS below
(or add a row directly to the DB / JSON) and re-run build_db.py + build_site.py.
"""
import json
import os

PRODUCTS = []

def add(**kw):
    kw.setdefault("features", [])
    kw.setdefault("spec_groups", [])
    kw.setdefault("consumable", None)
    kw.setdefault("description", "")
    kw.setdefault("gallery_urls", [])  # extra photos beyond the primary image_url, same product
    PRODUCTS.append(kw)

# ---------------------------------------------------------------------------
# CHROMATOGRAPHY  (source: bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="uhplc-1521-pro",
    category="chromatography",
    name="UHPLC 1521 Pro",
    tagline="UHPLC with ultra-high pressure till 22000 psi",
    image_url="https://bikaicorp.com/uploads/images/20260702/20260702102645483295.png",
    source_url="https://bikaicorp.com/chromatography/1.html",
    features=["UHPLC", "Pressure up to 22000 psi", "Flexible choices on injection mode", "Multiple selection of functions"],
    description=(
        "**High-Pressure UHPLC for Fast, Efficient Separations**\n\n"
        "A purpose-built UHPLC platform designed for high-pressure separations, flexible injection "
        "strategies and demanding analytical workflows. The BIKAI 1521 Pro's high-pressure pump "
        "architecture supports modern UHPLC columns and high-efficiency chromatographic methods, "
        "while configurable autosampling and temperature-control options allow the system to adapt "
        "to different method and throughput requirements. The modular detector architecture enables "
        "the system to be configured according to the analytical characteristics of the target compounds."
    ),
    spec_groups=[
        {"title": "Key Capabilities", "rows": [
            ["Parameter", "Specification"],
            ["System Type", "UHPLC"],
            ["Pump", "Up to 18,000 psi / 124 MPa"],
            ["Flow Range", "Up to 5.000 mL/min for UHPLC configuration"],
            ["Injection Modes", "Full Loop / Partial Loop / \u00b5L Pick-Up / FTN"],
            ["Sample Capacity", "Up to 216 \u00d7 1.5 mL vials"],
            ["Carryover", "<0.0025% under specified conditions"],
            ["Column Oven", "Up to 90\u00b0C"],
            ["Cooling", "Down to 4\u00b0C"],
            ["Detector Options", "UV-Vis / DAD / FLD / RID and other compatible detectors"],
        ]},
        {"title": "UHPLC Pump", "rows": [
            ["Parameter", "Value"],
            ["Maximum Pressure", "18,000 psi"],
            ["Pressure Equivalent", "124 MPa"],
            ["Flow range", "up to 5.000 mL/min"],
            ["Flow increment", "0.001 mL/min"],
            ["Configuration", "High-pressure binary gradient, online degassing"],
        ]},
        {"title": "Autosampler", "rows": [
            ["Parameter", "Specification"],
            ["Injection Modes", "Full Loop / Partial Loop / \u00b5L Pick-Up / FTN"],
            ["Loop Options", "10 / 20 / 50 / 100 / 1000 / 5000 \u00b5L"],
            ["Standard Capacity", "108 \u00d7 1.5 mL vials"],
            ["High-Throughput Capacity", "216 \u00d7 1.5 mL vials"],
            ["Microplate Capacity", "Up to 4 \u00d7 96-well plates"],
            ["Preparative Configuration", "80 \u00d7 5 mL vials"],
            ["Carryover", "<0.0025% under specified conditions"],
        ]},
        {"title": "Column Oven", "rows": [
            ["Parameter", "Specification"],
            ["Temperature Control", "Forced-air circulation / Peltier"],
            ["Heating Range", "Ambient +5\u00b0C to 90\u00b0C"],
            ["Cooling Range", "Down to ambient \u221221\u00b0C"],
            ["Minimum Temperature", "4\u00b0C"],
            ["Temperature Accuracy", "\u00b10.5\u00b0C"],
            ["Temperature Stability", "\u00b10.1\u00b0C"],
            ["Column Capacity", "Up to 4 \u00d7 300 mm columns"],
        ]},
        {"title": "Detector: UV-Vis", "rows": [
            ["Parameter", "Specification"], ["Wavelength Range", "190\u2013900 nm"],
            ["Light Source", "Deuterium + Tungsten lamps"], ["Wavelength Accuracy", "\u00b10.5 nm"],
        ]},
        {"title": "Detector: DAD", "rows": [
            ["Parameter", "Specification"], ["Wavelength Options", "190\u2013640 nm / 190\u2013800 nm"],
            ["Array", "1024 pixels"], ["Spectral Resolution", "0.6 nm/pixel"],
            ["Standard Flow Cell", "12 \u00b5L, 10 mm optical path"],
        ]},
        {"title": "Detector: FLD", "rows": [
            ["Parameter", "Specification"], ["Excitation Range", "200\u2013750 / 200\u2013900 nm"],
            ["Light Source", "Xenon Lamp"], ["Water Raman S/N", "1200:1"], ["Flow Cell", "12 \u00b5L"],
        ]},
        {"title": "Detector: RID", "rows": [
            ["Parameter", "Specification"], ["Refractive Index Range", "1\u20131.75"],
            ["Baseline Noise", "<2.5 nRIU"], ["Flow Cell Volume", "8 \u00b5L"], ["Max Flow Rate", "10 mL/min"],
        ]},
        {"title": "Software", "rows": [
            ["Function", "Capability"],
            ["Platform", "BIKAI ChromCore chromatography workstation"],
            ["Regulatory Support", "FDA 21 CFR Part 11 / GMP / GLP"],
            ["Electronic Signature", "Supported"],
            ["Maintenance", "Consumable-life and maintenance reminders"],
        ]},
    ],
)

add(
    slug="hplc-1511-pro",
    category="chromatography",
    name="HPLC 1511 Pro",
    tagline="Economical and durable, reasonable price, and stable quality. The best choice to reduce the input and get a quick return on investment.",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610104654174912.png",
    source_url="https://bikaicorp.com/chromatography/3.html",
    features=["HPLC", "2D HPLC", "Semi prep. HPLC", "Flexible detectors", "Multiple application possibilities"],
    description=(
        "**Flexible HPLC Platform for Routine, Advanced and Multi-Dimensional LC Applications**\n\n"
        "A modular and configurable HPLC system designed for routine analysis, 2D chromatography, "
        "semi-preparative workflows and a wide range of detector configurations. Its modular architecture "
        "allows users to configure the system with different pumps, autosamplers, column-management "
        "options and detectors according to analytical requirements — from conventional HPLC to "
        "multidimensional chromatography and semi-preparative applications."
    ),
    spec_groups=[
        {"title": "Key Capabilities", "rows": [
            ["Parameter", "Capability"],
            ["System Type", "HPLC"],
            ["Maximum Pressure", "Up to 11,600 psi / 80 MPa*"],
            ["Flow Rate Options", "Analytical to preparative configurations"],
            ["Autosampler Capacity", "Up to 108 standard vials"],
            ["Carryover", "<0.0025% under specified conditions"],
            ["Column Oven Stability", "\u00b10.1\u00b0C"],
            ["Cooling", "Down to 4\u00b0C"],
            ["Detector Options", "UV-Vis, DAD, FLD, RID and other optional detectors"],
            ["Application Modes", "HPLC / 2D HPLC / Semi-Prep HPLC"],
        ]},
        {"title": "Pump", "rows": [
            ["Parameter", "Specification"],
            ["Pump Configurations", "Isocratic, Binary, Quaternary, Dual-Ternary"],
            ["Maximum Pressure", "Up to 11,600 psi / 80 MPa for HPLC configuration*"],
            ["Analytical Flow Range", "0\u20135.000 mL/min or 0\u201310.000 mL/min"],
            ["Flow Increment", "0.001 mL/min"],
            ["Semi-Preparative Flow Range", "Up to 50 mL/min"],
            ["Preparative Flow Range", "Up to 150 mL/min"],
            ["Pressure Pulsation", "\u22641.0% at 1 mL/min, water, back pressure >10 MPa"],
        ]},
        {"title": "Autosampler", "rows": [
            ["Parameter", "Specification"],
            ["Injection Modes", "Full Loop, Partial Loop, Microliter Pick-Up, FTN"],
            ["Sample Loop Options", "10, 20, 50, 100, 1000, 5000 \u00b5L"],
            ["Standard Sample Capacity", "2 \u00d7 54 \u00d7 1.5 mL vials \u2014 108 positions"],
            ["Microplate Option", "2 \u00d7 96-well plates"],
            ["High-Throughput Option", "Up to 216 \u00d7 1.5 mL vials or 4 \u00d7 96-well plates"],
            ["Preparative Sample Capacity", "2 \u00d7 40 \u00d7 5 mL vials"],
            ["Carryover", "<0.0025% under specified conditions"],
        ]},
        {"title": "Column Oven", "rows": [
            ["Parameter", "Specification"],
            ["Temperature Control", "Forced-air circulation or Peltier control"],
            ["Heating Range", "Ambient +5\u00b0C to 90\u00b0C"],
            ["Cooling Range", "Down to ambient \u221221\u00b0C, minimum 4\u00b0C"],
            ["Temperature Accuracy", "\u00b10.5\u00b0C"],
            ["Temperature Stability", "\u00b10.1\u00b0C"],
            ["Column Capacity", "Up to 4 \u00d7 300 mm columns or multiple shorter columns"],
        ]},
        {"title": "Detector: UV-Vis", "rows": [
            ["Parameter", "Specification"], ["Wavelength Range", "190\u2013900 nm"],
            ["Light Source", "Deuterium + Tungsten lamps"], ["Wavelength Accuracy", "\u00b10.5 nm"],
        ]},
        {"title": "Detector: DAD", "rows": [
            ["Parameter", "Specification"], ["Wavelength Options", "190\u2013640 nm / 190\u2013800 nm"],
            ["Array", "1024 pixels"], ["Spectral Resolution", "0.6 nm/pixel"],
            ["Standard Flow Cell", "12 \u00b5L, 10 mm optical path"],
        ]},
        {"title": "Detector: Fluorescence", "rows": [
            ["Parameter", "Specification"], ["Excitation/Emission Range", "200\u2013750 nm or 200\u2013900 nm"],
            ["Light Source", "Xenon lamp"], ["Water Raman S/N", "1200:1"], ["Max Sampling Rate", "100 Hz"],
        ]},
        {"title": "Detector: Refractive Index", "rows": [
            ["Parameter", "Specification"], ["Refractive Index Range", "1\u20131.75"],
            ["Baseline Noise", "<2.5 nRIU"], ["Flow Cell Volume", "8 \u00b5L"],
            ["Communication", "RS-232, RS-485, USB, LAN"],
        ]},
        {"title": "Software", "rows": [
            ["Function", "Capability"],
            ["Platform", "BIKAI ChromCore chromatography workstation"],
            ["Database", "SQL Server"],
            ["Regulatory Support", "FDA 21 CFR Part 11 / GMP / GLP"],
        ]},
    ],
)

add(
    slug="prep-hplc-1511-pro",
    category="chromatography",
    name="Prep HPLC 1511 Pro",
    tagline="Semi preparative HPLC. Simple and flexible preparative purification, truly fully automated preparative system. From autosampling to automatic fraction collection, from controlled runs to analysis.",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610105701281531.png",
    source_url="https://bikaicorp.com/chromatography/4.html",
    description=(
        "**Simple and Flexible Preparation and Purification**\n\n"
        "A truly fully automated preparative system. From injection to fraction collection, from "
        "operation to analysis. Helps solve various semi-preparation and preparation applications. "
        "Supports extension to a high-pressure 2D system."
    ),
)

add(
    slug="2d-hplc-1511-pro",
    category="chromatography",
    name="2D HPLC 1511 Pro",
    tagline="Complex Analysis, One Step Faster",
    image_url="https://bikaicorp.com/uploads/images/20260703/20260703140555968560.png",
    source_url="https://bikaicorp.com/chromatography/5.html",
    features=["Two-dimensional separation, doubling the peak capacity", "Easy determination, greatly reducing pre-treatment", "Ultra-efficient grade, higher analysis efficiency"],
    description=(
        "Unlock more complex application scenarios: natural pharmaceutical ingredients, Chinese herbal "
        "medicine extract components, quality control of traditional Chinese medicine, toxic and "
        "harmful substances in the environment, differential proteomics, biopharmaceutical analysis."
    ),
)

add(
    slug="bio-hplc-1511-pro",
    category="chromatography",
    name="Bio HPLC 1511 Pro",
    tagline="Biologically Inert LC Systems. Flow paths are made of biologically inert materials for corrosion resistance, reducing the adsorption of biomolecules and ensuring integrity.",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610105917226832.png",
    source_url="https://bikaicorp.com/chromatography/6.html",
    features=["Bio-inert sample flow path", "PEEK, titanium and other biocompatible materials", "Easily adapted to biological and extreme pH applications", "Minimizes losses due to metal adsorption"],
    description="Enabling Efficient Biological Sample Analysis with a bio-inert flow path that effectively guarantees analytical reproducibility and durability.",
)

add(
    slug="gc-7000",
    category="chromatography",
    name="GC 7000",
    tagline="Professional GC Performance for Cost-Conscious Laboratories",
    image_url="https://bikaicorp.com/uploads/images/20260710/20260710141826238435.png",
    source_url="https://bikaicorp.com/chromatography/7.html",
    description=(
        "A frontier GC with IoT technology, providing more possibilities \u2014 a great balance between "
        "reliability, performance and efficiency. Built for future labs that focus on easy access and "
        "operation. Ideal GC system for environmental, chemical, petrochemical, food, forensic, "
        "pharmaceutical and material testing.\n\n"
        "**Real \u201cIoT\u201d Solution.** Embedded with the uniLite software platform, allowing time-consuming "
        "diagnostics, firmware updates, real-time plotting, method/sequence editing and log checks via "
        "an intuitive multi-function touchscreen, or remotely via pad/phone/computer.\n\n"
        "**Advanced Pneumatic Control.** Core microchannel-based advanced pneumatic control (APC) "
        "architecture protects against H\u2082 leaking.\n\n"
        "**Highly Modulized Detectors.** All detector modules are self-installable with a single 4-pin "
        "cable, minimizing GC downtime.\n\n"
        "**High speed and throughput.** More than 4 inlets, 5 detectors and 2 ovens can be installed in "
        "a single GC system, with valve boxes, multi-channel liquid/gas samplers and dynamic dilution "
        "add-ins available.\n\n"
        "**Anywhere, any terminal.** 7\" embedded touchscreen plus built-in web server for remote access; "
        "4 physical buttons (Stop, Pre-run, Service, Start) for fast local control."
    ),
)

# ---------------------------------------------------------------------------
# MASS SPECTROMETRY (source: bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="tq-1621",
    category="mass-spectrometry",
    name="TQ 1621",
    tagline="Triple Quadrupole LC-MS/MS \u00b7 Models A and B",
    image_url="https://bikaicorp.com/uploads/images/20260922/20260922132030216449.png",
    source_url="https://bikaicorp.com/mass-spectrometry/56.html",
    features=["m/z 5 \u2013 1250", "\u22640.1 amu per 24 h", "\u2265500 MRM/s", "IDL <2.0fg for reserpine, ESI+", "Nitrogen-Only Operation"],
    description=(
        "BIKAI TQ 1621 triple quadrupole LC-MS/MS achieves femtogram-level instrument detection limit, "
        "operating purely with nitrogen gas without requiring an argon gas cylinder. Equipped with a "
        "180\u00b0 curved collision cell with axial linear acceleration, it eliminates neutral particles "
        "from the ion beam and restricts MRM crosstalk down to 0.01%, preserving excellent sensitivity "
        "even for complex real-world sample matrices. The complete system is delivered with an "
        "integrated PSA nitrogen generator and oil-free dry fore pump with a 5-year maintenance-free "
        "service life, removing the hassle of argon supply contracts, gas cylinder management and "
        "regular oil changes."
    ),
    spec_groups=[
        {"title": "Sensitivity (A vs B)", "rows": [
            ["Sensitivity specification", "TQ 1621A", "TQ 1621B"],
            ["S/N, ESI+ MRM (1 pg reserpine, RMS)", "\u22651,500,000:1", "\u22652,000,000:1"],
            ["IDL, ESI+ (10 fg reserpine, n\u22658, 99%)", "\u22644.0 fg", "\u22642.0 fg"],
            ["IDL, ESI\u2212 (10 fg chloramphenicol, n\u22658, 99%)", "\u22646.0 fg", "\u22644.0 fg"],
            ["Everything else", "Identical \u2014 same ion source, analyser, collision cell, detector, vacuum system and software", ""],
        ]},
        {"title": "Core Specifications", "rows": [
            ["Parameter", "Specification"],
            ["Configuration", "Spatial tandem triple quadrupole, circular gold-plated rods"],
            ["Mass range", "m/z 5 \u2013 1250"],
            ["Resolution", "0.4 \u2013 2.5 FWHM, adjustable across the full mass range"],
            ["Mass stability / accuracy", "\u22640.1 amu per 24 h; \u2264\u00b10.1 amu"],
            ["Crosstalk", "\u22640.01%"],
            ["Dynamic range", "6 orders of magnitude"],
            ["MRM scan speed", "\u2265500 MRM/s"],
            ["Reproducibility", "Peak area RSD below 1.5%, RT RSD below 0.25% (5 pg tacrolimus, n\u22658)"],
            ["Collision cell", "Q2, 180\u00b0 curved linear acceleration; high-purity N\u2082, no argon required"],
            ["Detector", "Discrete-dynode electron multiplier"],
            ["Fore pump", "Oil-free dry pump \u226590 m\u00b3/h, five years maintenance-free"],
            ["Dimensions and weight", "800 \u00d7 852 \u00d7 590 mm; 208 kg"],
        ]},
    ],
)

add(
    slug="tq-1620",
    category="mass-spectrometry",
    name="TQ 1620",
    tagline="Triple Quadrupole Mass Spectrometer",
    image_url="https://bikaicorp.com/uploads/images/20260922/20260922131543680163.png",
    source_url="https://bikaicorp.com/mass-spectrometry/8.html",
    features=["m/z 5\u20132000", "10,000 amu/s", "IDL <6 fg", "S/N >200,000:1", "4-Order Dynamic Range", "ESI + APCI Dual Ion Source"],
    description=(
        "BIKAI TQ 1620 is a high-performance triple quadrupole mass spectrometer equipped with a "
        "plug-and-play ESI/APCI dual ion source, efficient ion transmission, a 180\u00b0 curved linear "
        "acceleration collision cell, and a highly stable triple quadrupole mass analyzer. It supports "
        "MS/MS, MRM, SIM, Full Scan, Product Ion Scan, Precursor Ion Scan and Neutral Loss Scan. The "
        "system uses high-purity nitrogen for both nebulization and collision gas and can be equipped "
        "with a nitrogen generator, reducing the need for additional gas cylinders. Well suited for "
        "pharmaceutical analysis, food safety, environmental testing and research applications."
    ),
    spec_groups=[
        {"title": "Core Specifications", "rows": [
            ["Parameter", "Specification"],
            ["Mass Spectrometer Type", "Triple Quadrupole Mass Spectrometer"],
            ["Ion Source", "ESI + APCI dual ion source"],
            ["Ion Source Switching", "Plug-and-play design; replacement in approx. 30 seconds"],
            ["ESI Flow Rate", "5 \u00b5L/min \u2013 3 mL/min"],
            ["APCI Flow Rate", "200 \u2013 2000 \u00b5L/min"],
            ["Maximum Heating Temperature", "750 \u00b0C"],
            ["Mass Range", "m/z 5\u20132000"],
            ["Scanning Speed", "Up to 10,000 amu/s"],
            ["Mass Resolution", "<0.8 amu"],
            ["Mass Stability", "0.1 amu / 24 h"],
            ["Dynamic Range", "4 orders of magnitude"],
            ["MRM Sensitivity", "S/N >200,000:1 for reserpine, MRM 609/195"],
            ["Instrument Detection Limit (IDL)", "<6 fg for reserpine, ESI+"],
            ["Scan Modes", "Full Scan, SIM, Product Ion, Precursor Ion, Neutral Loss, MRM"],
            ["Reproducibility", "Peak area RSD <5.0%; retention time RSD <5.0%"],
            ["Collision Cell", "180\u00b0 curved linear acceleration collision cell"],
            ["Gas System", "High-purity nitrogen for nebulization and collision gas"],
            ["Vacuum System", "Mechanical pump + integrated multi-port turbo molecular pump"],
            ["Mechanical Pumping Speed", "40 m\u00b3/h"],
            ["Data System", "Windows 10 or above, 64-bit"],
            ["Software Language", "Chinese / English"],
        ]},
    ],
)

add(
    slug="sq-1610",
    category="mass-spectrometry",
    name="SQ 1610",
    tagline="Single Quadrupole Mass Spectrometer",
    image_url="https://bikaicorp.com/uploads/images/20260820/20260820170003712440.png",
    source_url="https://bikaicorp.com/mass-spectrometry/55.html",
    features=["m/z 5 \u2013 2000", ">10,000 amu/s", "S/N Ratio >100:1", "Source Swap in Under 30 Seconds", "Six orders of magnitude"],
    description=(
        "BIKAI SQ 1610 single-quadrupole LC-MS is engineered for outstanding anti-contamination "
        "performance. Instrument downtime is mostly caused by contamination rather than hardware "
        "specifications, so SQ 1610 addresses contamination risks throughout the full ion path: "
        "orthogonal spray design, active exhaust system, heated counter-flow curtain gas paired with a "
        "0.3 mm cone orifice (without consumable capillary), and a gold-plated molybdenum quadrupole. "
        "These four independent protective measures together deliver stable mass-axis performance with "
        "mass stability of 0.2 amu over 24-hour operation. Delivered as a complete analytical system "
        "bundled with a binary UHPLC front-end."
    ),
    spec_groups=[
        {"title": "Mass Spectrometer", "rows": [
            ["Parameter", "Specification"],
            ["Analyser", "200 mm circular pure-molybdenum quadrupole, gold-plated"],
            ["Resolution", "Unit mass resolution"],
            ["Mass axis stability", "0.2 amu / 24 h"],
            ["Repeatability", "Reserpine peak area RSD below 8%"],
            ["Acquisition modes", "Full scan, SIM, simultaneous full scan and SIM, alternating scan"],
            ["Detector", "Discrete-dynode electron multiplier"],
            ["Vacuum system", "Three-stage differential; 40 m\u00b3/h rotary; 30 and 60 L/s oil-free multi-port turbo, air-cooled"],
            ["Dimensions", "330 \u00d7 350 \u00d7 585 mm"],
            ["Data system", "Independent acquisition/processing software; English, Chinese, Russian UI"],
        ]},
        {"title": "Bundled Binary UHPLC Front End", "rows": [
            ["Parameter", "Value"],
            ["Maximum system pressure", "18,000 psi \u2014 1.7 to 5 \u00b5m columns, HPLC and UHPLC on one system"],
            ["Pump", "0.001\u20135.000 mL/min, parallel short-stroke binary gradient, 4 solvent selection, active plunger wash"],
            ["Autosampler", "4 \u00d7 54 vials or 4 \u00d7 96-well, cooled 4\u00b0C\u2013ambient, carryover below 0.0025%"],
            ["Column oven", "Forced-air, \u00b11\u00b0C, RT+5\u201390\u00b0C, four 300 mm columns with optional switching valves"],
        ]},
    ],
)

add(
    slug="gc-ms-7500",
    category="mass-spectrometry",
    name="GC-MS 7500",
    tagline="Single-Quadrupole Gas Chromatography-Mass Spectrometry",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610140258335786.png",
    source_url="https://bikaicorp.com/mass-spectrometry/9.html",
    description=(
        "A single-quadrupole gas chromatography-mass spectrometry (GC-MS) system suitable for "
        "environmental monitoring, food safety, pharmaceutical analysis and chemical testing "
        "applications. The MS module features an inert ceramic EI ion source (dual filament with "
        "software switching), an all-metal pre-quadrupole mass analyzer, and a long-life 13-stage "
        "discrete dynode electron multiplier, with an independent vacuum system. The GC module includes "
        "a 30-ramp/31-platform programmable oven, a split/splitless injector and a 24-position liquid "
        "autosampler. The software workstation supports full scan, SIM and alternating scan modes, with "
        "NIST library search, user-built library, batch quantification and automatic report generation."
    ),
    spec_groups=[
        {"title": "Mass Spectrometer Module", "rows": [
            ["Parameter", "Specification"],
            ["Mass Range", "4\u20131200 amu"],
            ["Sensitivity", "1 pg OFN, S/N \u22651500:1; IDL < 10 fg OFN"],
            ["Mass Stability", "\u00b10.10 amu / 24h"],
            ["Maximum Scan Speed", "20,000 amu/s (fully adjustable)"],
            ["Resolution", "1.0 amu"],
            ["Dynamic Range", "10\u2076"],
            ["Peak Area Reproducibility", "<3% RSD"],
            ["Ion Source Type", "EI, inert ceramic, dual filament with software switching"],
            ["Ion Source Temperature", "50\u2013350\u2103"],
            ["Mass Analyzer", "All-metal pre-quadrupole (removable and washable)"],
            ["Detector", "13-stage discrete dynode electron multiplier, 10kV conversion dynode"],
            ["Vacuum System", "Backing pump 4 m\u00b3/h, turbo molecular pump 250 L/s"],
        ]},
        {"title": "GC Module", "rows": [
            ["Parameter", "Specification"],
            ["Oven Temperature Range", "Ambient +5\u2103 to 450\u2103"],
            ["Temperature Control Accuracy", "\u22640.01\u2103"],
            ["Programmed Ramp Stages", "30 ramps / 31 platforms"],
            ["Maximum Ramp Rate", "120\u2103/min"],
            ["Cooling Rate", "450\u2103 \u2192 50\u2103 in \u22646 min (at 20\u2103 ambient)"],
            ["Injection Port Type", "Split/Splitless capillary injector, up to 450\u2103"],
            ["Pressure Range / Accuracy", "0\u2013100 psi, accuracy 0.001 psi"],
            ["Maximum Split Ratio", "\u22657500"],
            ["Autosampler", "24-position tray, adjustable injection/depth"],
        ]},
        {"title": "Software & Safety", "rows": [
            ["Parameter", "Specification"],
            ["Software", "Full English interface, manual/auto tuning, NIST library search, self-built library, batch quantification, automatic report generation"],
            ["Safety", "Carrier gas cutoff protection, real-time turbo pump monitoring, one-click emergency shutdown"],
        ]},
    ],
)

# ---------------------------------------------------------------------------
# SPECTROSCOPY (source: bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="uv-3600-spectrophotometer",
    category="spectroscopy",
    name="Spectrophotometer UV 3600 (Ultra-3000)",
    tagline="Double Beam Optical System",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610140823728040.png",
    source_url="https://bikaicorp.com/spectroscopy/10.html",
    spec_groups=[
        {"title": "Technical Specifications", "rows": [
            ["Parameter", "Ultra-3000"],
            ["Light Path", "Double beam"],
            ["Spectral Bandwidth", "0.5 / 1 / 2 / 4 nm"],
            ["Wavelength Reproducibility", "0.1 nm"],
            ["Wavelength Accuracy", "\u00b10.3 nm"],
            ["Wavelength Range", "190\u20131100 nm"],
            ["Noise", "\u00b10.00004 A"],
            ["Drift", "0.0005 Abs/hr"],
            ["Stray Light", "\u22640.03%T"],
            ["Spectrum Scanning", "Standard"],
            ["Screen", "7\" TFT color screen WVGA (800\u00d7480)"],
            ["Direct Printing", "Available"],
            ["USB Storage", "Available"],
            ["Built-in Methods", "Available"],
            ["Workstation", "Available"],
        ]},
    ],
)

# ---------------------------------------------------------------------------
# FUNCTIONAL MODULES (source: bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="lc-pump",
    category="functional-modules",
    name="LC Pump",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610163342364396.png",
    source_url="https://bikaicorp.com/functional-module/11.html",
    spec_groups=[{"title": "Configurations", "rows": [
        ["Category", "Specifications"],
        ["Isocratic", "10500 PSI / >72MPa \u2014 small volume"],
        ["Isocratic", "10500 PSI / >72MPa \u2014 standard volume"],
        ["Binary", "11600 PSI / >80MPa"],
        ["Binary", "11600 PSI / >80MPa, 2CH degasser, 2\u00d7 2-way solvent selection valves"],
        ["Quaternary", "11600 PSI / >80MPa, 4CH degasser"],
        ["Quaternary", "11600 PSI / >80MPa, 5CH degasser"],
        ["Dual ternary gradient", "11600 PSI / >80MPa, 6CH degasser, triple gradient proportional valve"],
    ]}],
)

add(
    slug="lc-sampler",
    category="functional-modules",
    name="LC Sampler",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610163732825556.png",
    source_url="https://bikaicorp.com/functional-module/26.html",
    spec_groups=[{"title": "Configurations", "rows": [
        ["Category", "Specifications"],
        ["Auto sample Inhalation", "9000 PSI, standard"],
        ["Auto sample Inhalation", "9000 PSI, standard, with cooling function"],
        ["Auto sample Inhalation", "9000 PSI, standard, double valve"],
        ["Auto sample Inhalation", "9000 PSI, standard, double valve, cooling function"],
        ["Auto sample Inhalation", "9000 PSI, mass injection 1 mL"],
        ["Auto sample Inhalation", "9000 PSI, mass injection 1 mL, cooling function"],
        ["Auto sample Inhalation", "9000 PSI, mass injection 1 mL, double valve"],
        ["Auto sampler \u2014 Integral-Loop", "9000 PSI, 4\u00d7 sample tray, 100 \u00b5L quantitative pump"],
        ["Auto sampler \u2014 Integral-Loop", "9000 PSI, 4\u00d7 sample tray, 100 \u00b5L quantitative pump, cooling function"],
    ]}],
)

add(
    slug="lc-column-oven",
    category="functional-modules",
    name="LC Column Oven",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610164130750093.png",
    source_url="https://bikaicorp.com/functional-module/27.html",
    spec_groups=[{"title": "Configurations", "rows": [
        ["Category", "Specifications"],
        ["Standard", "Room temperature +5\u2103 ~ 90\u2103"],
        ["Standard", "Room temperature +5\u2103 ~ 90\u2103, two-position 6-way valve \u00d72"],
        ["Standard", "Room temperature +5\u2103 ~ 90\u2103, two-position 6-way valve \u00d71 + two-position 10-way valve \u00d71"],
        ["Heating & cooling", "Temperature 4\u2103 \u2013 90\u2103"],
        ["Heating & cooling", "Temperature 4\u2103 \u2013 90\u2103, two-position 6-way valve \u00d72"],
        ["Heating & cooling", "Temperature 4\u2103 \u2013 90\u2103, two-position 6-way valve \u00d71 + two-position 10-way valve \u00d71"],
    ]}],
)

add(
    slug="lc-diode-array-detector",
    category="functional-modules",
    name="LC Diode Array Detector",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610162924519879.png",
    source_url="https://bikaicorp.com/functional-module/25.html",
    spec_groups=[{"title": "Configurations", "rows": [
        ["Type", "Specification"],
        ["Diode-array Detector", "1024 pixels, 190nm\u2013640nm"],
        ["Diode-array Detector", "1024 pixels, 190nm\u2013800nm"],
    ]}],
)

add(
    slug="lc-uv-detector",
    category="functional-modules",
    name="LC UV Detector",
    tagline="Wavelength range 190 nm\u2013900 nm",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610164324131807.png",
    source_url="https://bikaicorp.com/functional-module/28.html",
    features=["Wavelength range 190 nm\u2013900 nm"],
)

add(
    slug="fluorescence-detector",
    category="functional-modules",
    name="Fluorescence Detector",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610164704298539.png",
    source_url="https://bikaicorp.com/functional-module/30.html",
    spec_groups=[{"title": "D50 vs D51", "rows": [
        ["Parameter", "D50", "D51"],
        ["Wavelength range", "EX: 200\u2013750 nm / EM: 200\u2013750 nm", "EX: 200\u2013900 nm / EM: 200\u2013900 nm"],
        ["Light source", "Xenon Lamp (DC)", "Xenon Lamp (DC)"],
        ["Spectral bandwidth", "20 nm", "20 nm"],
        ["Wavelength accuracy", "\u00b12 nm", "\u00b12 nm"],
        ["Wavelength precision", "\u00b10.2 nm", "\u00b10.2 nm"],
        ["Water Raman peak S/N", "1200 : 1", "1200 : 1"],
        ["Dynamic noise", "\u22645\u00d710\u207b\u2074 FU", "\u22645\u00d710\u207b\u2074 FU"],
        ["Dynamic drift", "\u22645\u00d710\u207b\u00b3 FU/h", "\u22645\u00d710\u207b\u00b3 FU/h"],
        ["Linear range", ">10\u2075 (JJG)", ">10\u2075 (JJG)"],
        ["Maximum sampling rate", "100 Hz", "100 Hz"],
        ["Flow cell", "12 \u00b5L; 2 MPa (290 PSI)", "12 \u00b5L; 2 MPa (290 PSI)"],
        ["Minimum detection concentration", "2\u00d710\u207b\u00b9\u2070 g/mL (Na)", "2\u00d710\u207b\u00b9\u2070 g/mL (Na)"],
        ["Weight", "24 Kg", "24 Kg"],
        ["Dimensions", "550(D)\u00d7400(W)\u00d7280(H) mm", "550(D)\u00d7400(W)\u00d7280(H) mm"],
        ["Power supply", "100\u2013240 VAC, 50/60 Hz, 300 W max", "100\u2013240 VAC, 50/60 Hz, 300 W max"],
    ]}],
)

add(
    slug="refractive-index-detector",
    category="functional-modules",
    name="Refractive Index Detector",
    tagline="Noise < 2.5 nRIU, Drift < 200 nRIU/h",
    image_url="https://bikaicorp.com/uploads/images/20260702/20260702132012225195.png",
    source_url="https://bikaicorp.com/functional-module/31.html",
    features=["Noise < 2.5 nRIU, Drift < 200 nRIU/h"],
    spec_groups=[{"title": "Technical Specifications", "rows": [
        ["Parameter", "Specification"],
        ["Principle", "Refractometry"],
        ["Refractive Index Range", "1.00 \u2013 1.75"],
        ["Detection Range", "0.25 \u2013 512 \u00b5RIU"],
        ["Linear Range", "600 \u00b5RIU"],
        ["Noise", "\u2264 2.5 nRIU (Response: 1.5 sec)"],
        ["Drift", "\u2264 200 nRIU/h (pure water, 1 mL/min, purge off)"],
        ["Response Time", "0.1 / 0.25 / 0.5 / 1.0 / 1.5 / 2 / 3 / 6 sec (selectable)"],
        ["Auto-Zero", "Optical / Electrical Auto-Zero"],
        ["Temperature Control", "30 \u2013 50 \u00b0C (1\u00b0C increments)"],
        ["Communication Interface", "USB"],
        ["Cell Volume", "8 \u00b5L"],
        ["Max Flow Rate", "10 mL/min (pure water as mobile phase)"],
        ["Wetted Materials", "SUS316, Teflon, Quartz Glass"],
        ["Power Supply", "AC 100\u2013240 V \u00b110%, 50/60 Hz"],
        ["Dimensions", "260 (W) \u00d7 150 (H) \u00d7 400 (D) mm"],
        ["Weight", "~12 kg (27 lbs)"],
        ["EMC / Safety Standards", "EN61326-1 / EN61010-1"],
    ]}],
)

add(
    slug="evaporative-light-scattering-detector",
    category="functional-modules",
    name="Evaporative Light Scattering Detector (ELSD)",
    tagline="Typical sensitivity as low as 5 ng",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610181540797922.png",
    source_url="https://bikaicorp.com/functional-module/37.html",
    features=["Typical sensitivity as low as 5 ng"],
    description=(
        "BIKAI L-3535 ELSD \u2014 Low-Temperature Evaporative Light Scattering Detector. Universal "
        "detection for HPLC beyond UV limitations: detects all non-volatile and semi-volatile "
        "compounds regardless of chromophores or electroactive groups (e.g. saponins, terpenes, "
        "lipids, sugars). Works with any HPLC system, full GLP compliance with SOP protocols, and a "
        "remote shutdown mode that extends instrument life. Ideal for natural products analysis, "
        "pharmaceutical QC, and food & nutraceutical testing."
    ),
    spec_groups=[{"title": "Technical Specifications", "rows": [
        ["Parameter", "Details"],
        ["Detection Principle", "Evaporative Light Scattering (ELS)"],
        ["Flow Rate Range", "200 \u00b5L/min \u2013 2 mL/min"],
        ["Nebulizer Type", "High-efficiency, low-bandwidth design"],
        ["Control Method", "PC software or local interface"],
        ["Remote Shutdown", "Yes (gas, heater, light source)"],
        ["Compatibility", "Works with any HPLC system"],
        ["Regulatory Compliance", "GLP-ready with full SOP support"],
    ]}],
)

add(
    slug="gc-sampler",
    category="functional-modules",
    name="GC Sampler",
    image_url="https://bikaicorp.com/uploads/images/20260702/20260702132625790317.jpg",
    # Source page has a 2-photo gallery for this product (wide shot + close-up of the
    # injector head/touchscreen) — confirmed by inspecting the swiper on the live page.
    gallery_urls=["https://bikaicorp.com/uploads/images/20260703/20260703141013543802.jpg"],
    source_url="https://bikaicorp.com/functional-module/51.html",
    spec_groups=[{"title": "Models", "rows": [
        ["System / module", "Specifications / Notice"],
        ["Sampler 1100 (19 vials)", "19-vial autosampler, equivalent to Agilent G4513A, compatible with multiple GC brands"],
        ["Tray 4100 (150 vials)", "150-vial tray, equivalent to Agilent G4514A, supports AS-3016A / AS-3016C / AS-3016F"],
        ["Sampler 3100 (24 vials)", "24-vial autosampler, equivalent to Agilent G4513A, compatible with multiple GC brands"],
        ["Sampler 2100 (22 vials)", "22-vial autosampler, equivalent to Agilent G4513A, compatible with multiple GC brands"],
    ]}],
)

add(
    slug="charged-aerosol-detector",
    category="functional-modules",
    name="Charged Aerosol Detector",
    tagline="Sensitive (500 pg detection) and simple to use",
    image_url="https://bikaicorp.com/uploads/images/20260702/20260702132056642136.png",
    source_url="https://bikaicorp.com/functional-module/54.html",
    features=["Sensitive (500 pg detection) and simple to use"],
    spec_groups=[{"title": "Technical Specifications", "rows": [
        ["Category", "Details"],
        ["General", "Model: BIKAI CAD D70. Min. Detection: 500 pg. Dynamic Range: 10\u2077. Repeatability (RSD): \u2264 2.5%"],
        ["Power & Environment", "Input: 84\u2013265 VAC, 40\u201360 Hz. Consumption: 250 VA. Conditions: 5\u201330\u00b0C, \u2264 90% RH"],
        ["Temperature Control", "Nebulizer / drying tube / detection cell: ambient to 100\u00b0C, \u00b10.1\u00b0C accuracy"],
        ["Gas System", "Nitrogen/Clean Air, 2\u20135 bar, flow <4 L/min, manual & PC control"],
        ["Liquid Flow", "Eluent flow rate 0.01\u20133.0 mL/min"],
        ["Signal Performance", "Analog + digital (serial, Ethernet) output; baseline noise \u22640.05 pA, drift \u22640.5 pA/30min"],
        ["Communication & Software", "RS-232, RS-485, USB, LAN; dedicated CAD control software"],
        ["Data Management", "100 method sets storage with auto recall"],
    ]}],
)

add(
    slug="photochemical-derivatizer",
    category="functional-modules",
    name="Photochemical Derivatizer",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610181311311121.png",
    source_url="https://bikaicorp.com/functional-module/53.html",
)

add(
    slug="fraction-collector",
    category="functional-modules",
    name="Fraction Collector",
    image_url="https://bikaicorp.com/uploads/images/20260610/20260610181126758173.png",
    source_url="https://bikaicorp.com/functional-module/52.html",
)

# ---------------------------------------------------------------------------
# GAS GENERATORS (source: bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="nitrogen-generator",
    category="gas-generators",
    name="Nitrogen Generator",
    tagline="Switchable between nitrogen and air, with a combined maximum output of 35 L/min.",
    image_url="https://bikaicorp.com/uploads/images/20260914/20260914160544924385.png",
    source_url="https://bikaicorp.com/gas-generators/50.html",
    spec_groups=[{"title": "BIKAI Light Series", "rows": [
        ["Model", "Specification"],
        ["Light 35", "N2 max: 19 L/min, 55 psi; GAS1/2 AIR: 25 L/min, 100 psi; EXHAUST AIR: 26 L/min, 65 psi"],
        ["Light 35 Pro", "N2 max: 35 L/min, pressure: 100 psi"],
        ["Light 70", "N2 max: 70 L/min, pressure: 100 psi"],
    ]}],
)

# ---------------------------------------------------------------------------
# SAMPLE TREATMENT (source: uvtech-cc.com — not present on bikaicorp.com)
# ---------------------------------------------------------------------------

add(
    slug="hextractor-20",
    category="sample-treatment",
    name="Automated Sample Preparation System hExtractor 20",
    tagline="Extraction \u00b7 Hydrolysis \u00b7 Digestion \u00b7 Oxidation \u00b7 Organic Synthesis",
    image_url="https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/701f5386-1168-4e24-a53b-ab4b5fda5ba7.png",
    image_referer="https://www.uvtech-cc.com/product/sample-treatment/automated-sample-preparation-system-hextractor20.html",
    source_url="https://www.uvtech-cc.com/product/sample-treatment/automated-sample-preparation-system-hextractor20.html",
    features=["Extraction", "Hydrolysis", "Digestion", "Oxidation", "Organic Synthesis"],
    description=(
        "Officially named Auto-Chemical Extractor / Auto-Chemical Reactor (ACR20), offered in two "
        "models: sequential **hExtractor 20** and batch-type **hExtractor 20B**. An integrated, fully "
        "automatic pretreatment instrument with high-pressure heating and reflux functions that "
        "replaces traditional manual lab pretreatment equipment (Soxhlet extractors, ultrasonic "
        "cleaners, microwave processors, high-pressure digesters, reflux hydrolysis devices) \u2014 "
        "realizing full automation of chemical laboratory sample prep.\n\n"
        "**Applications:** rapid extraction of plastic additives (antioxidants, flame retardants, "
        "stabilizers) from PP/rubber/PET/nylon in minutes instead of hours; PET/nylon depolymerization "
        "for monomer analysis; high-pressure nitric-acid digestion of plastics for heavy-metal testing; "
        "PFAS Total Oxidisable Precursor (TOP) assay (5\u201320 min vs. 12 h traditionally, >99.9% oxidation "
        "efficiency); extraction of dioxins/PBDEs from soil and waste; extraction of human metabolites "
        "from hair & nails (nicotine, cannabinoids, fatty acids) with up to 100% recovery; herbal-medicine "
        "active-ingredient extraction (e.g. ginsenosides); rapid protein hydrolysis for amino-acid "
        "testing (5\u201330 min vs. 12\u201324 h traditionally); polysaccharide hydrolysis; and general "
        "high-pressure chemical synthesis/crystallization reactions (0.5\u20132 h vs. 4\u2013120 h traditionally).\n\n"
        "**Key advantages:** dramatic time savings (e.g. Soxhlet extraction 1\u201372 h \u2192 2\u201310 min on the "
        "hExtractor); micro-solvent consumption (0.1\u20135 mL vs. 50\u2013200 mL, cutting organic solvent use "
        "by over 99%); full-process automation (automatic sample feeding \u2192 closed high-pressure "
        "reaction/heated reflux \u2192 cooling & depressurization \u2192 automatic dilution, no manual "
        "operation); touchscreen control storing up to 20 methods (temperature 50\u2013300\u00b0C, heating "
        "duration 0\u201316 h); and a multi-layer safety protection system with graded pressure-resistant "
        "reaction sleeves for risk-free high-pressure operation."
    ),
)

# ---------------------------------------------------------------------------
# CONSUMABLES (source: uvtech-cc.com — listing-page structured fields)
# ---------------------------------------------------------------------------

UVTECH_REFERER_CONSUMABLES = "https://www.uvtech-cc.com/product/Consumables.html"

def add_consumable(slug, name, image_url, source_url, part_no, instrument_model,
                    instrument_manufacturer, original_part_no, life_span, note=None):
    add(
        slug=slug,
        category="consumables",
        name=name,
        tagline=note or f"Equivalent lamp for {instrument_manufacturer} {instrument_model}",
        image_url=image_url,
        image_referer=UVTECH_REFERER_CONSUMABLES,
        source_url=source_url,
        consumable={
            "part_no": part_no,
            "instrument_model": instrument_model,
            "instrument_manufacturer": instrument_manufacturer,
            "original_part_no": original_part_no,
            "life_span": life_span,
        },
    )

# Generic items (no structured consumable fields)
add(
    slug="column",
    category="consumables",
    name="Column",
    image_url="https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/9178baa2-03af-4d13-b930-7ef02ff851db.jpg",
    image_referer=UVTECH_REFERER_CONSUMABLES,
    source_url="https://www.uvtech-cc.com/products_details/23.html",
    tagline="HPLC / GC chromatography columns \u2014 specifications on request",
)
add(
    slug="cuvette",
    category="consumables",
    name="Cuvette",
    image_url="https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/78b68a87-82e1-4f24-80dc-8d4bfc314d4d.jpg",
    image_referer=UVTECH_REFERER_CONSUMABLES,
    source_url="https://www.uvtech-cc.com/products_details/24.html",
    tagline="Spectrophotometer cuvettes \u2014 specifications on request",
)
add(
    slug="equivalent-lamp",
    category="consumables",
    name="Equivalent Lamp (generic)",
    image_url="https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/64179b26-2a50-408c-b1e9-e39671da2d73.png",
    image_referer=UVTECH_REFERER_CONSUMABLES,
    source_url="https://www.uvtech-cc.com/product/consumables/equivalent-lamp.html",
    tagline="High-quality equivalent lamp \u2014 deuterium lamp, D2 lamp (catch-all / instrument model not specified)",
)

add_consumable("lamp-waters-996-2996", "Waters 2996 / 996 \u2014 Wat052586", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/a0d6dfa1-eb96-4aa3-ad29-5457d35febd9.jpg", "https://www.uvtech-cc.com/products_details/d2lampwat052586.html", "BK82022996", "Waters996/2996", "Waters", "Wat052586", "2000 hours")
add_consumable("lamp-waters-2489-2998", "Waters 2489/2998 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/d08e155f-77b1-486b-84c0-9b3e699343c0.jpg", "https://www.uvtech-cc.com/products_details/76.html", "BK82020281", "Waters2489(2695)/2998", "Waters", "201000281/201000186", "2000 hours")
add_consumable("lamp-waters-2487", "Waters 2487 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/17e0e2f9-cd4e-44ea-91fb-b4d1fdb6b489.jpg", "https://www.uvtech-cc.com/products_details/75.html", "BK82112487", "Waters2487", "Waters", "Was081142", "2000 hours")
add_consumable("lamp-thermo-u3000-d2", "Thermo U3000 6074.1110 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/12a544d2-7574-49f7-8925-b11082af43af.jpg", "https://www.uvtech-cc.com/products_details/74.html", "BK82226999", "U3000 series", "Thermo ThermoFisher", "6074.1110/L6999-52", "2000 hours")
add_consumable("lamp-thermofisher-u3000-tungsten", "ThermoFisher U3000 equivalent tungsten lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/b59a6515-a42a-4bbd-9d96-18766c4ec6d7.jpg", "https://www.uvtech-cc.com/products_details/73.html", "BKWL6074", "U3000 series", "ThermoFisher", "6074.2000/6083.2000", "2000 hours")
add_consumable("lamp-thermofisher-ice3500", "ThermoFisher atomic absorption ICE3500", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/3b279597-71fe-4791-b4ec-dcfea1d28a30.jpg", "https://www.uvtech-cc.com/products_details/72.html", "BK82024204", "Atomic absorption ICE3500", "ThermoFisher", "9423-420-30004", "2000 hours")
add_consumable("lamp-thermofisher-vhd1", "Thermo Fisher VH-D1 6083.1110 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/86bc4a6e-67db-41c0-895d-6705ac73d0b8.jpg", "https://www.uvtech-cc.com/products_details/71.html", "BK60831110", "VH-D1", "ThermoFisher", "6083.1110", "2000 hours")
add_consumable("lamp-shimadzu-l6380", "Shimadzu UV lamp L6380", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/4afeb723-14d1-424c-8eff-ac9a93e4a58b.jpg", "https://www.uvtech-cc.com/products_details/70.html", "L6380", "UV-3700/3600/2700/2550/2450/1700/1800/1240/1280", "Shimadzu", "062-65055-05", "2000 hours")
add_consumable("lamp-shimadzu-spd10a", "Shimadzu SPD-10A/20A/15C equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/f2217af4-0d4d-4f36-a309-62e443a0d8b9.jpg", "https://www.uvtech-cc.com/products_details/69.html", "BK82000010", "SPD-10A/20A/15C", "Shimadzu", "228-34016-02/L6585-02", "2000 hours")
add_consumable("lamp-shimadzu-lc2010", "Shimadzu LC-2010 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/31a917ff-669c-478c-8903-8e09128f5fe0.jpg", "https://www.uvtech-cc.com/products_details/68.html", "BK82002010", "LC-2010/A/C", "Shimadzu", "228-37401-91", "2000 hours")
add_consumable("lamp-shimadzu-lc2030-2040", "Shimadzu LC-2030/2040 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/705c62f0-e722-4ba6-9cf5-7bfa737e91e6.jpg", "https://www.uvtech-cc.com/products_details/67.html", "BK82002030/2040", "LC-2030/2040", "Shimadzu", "228-63621/228-55626-01", "2000 hours")
add_consumable("lamp-pe-365-tungsten", "Perkin Elmer 365 series tungsten lamp N4101037", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/046c606c-92f3-48fc-89c7-45cf372a8e3d.jpg", "https://www.uvtech-cc.com/products_details/66.html", "BK82221037", "365 series", "Perkin Elmer", "N4101037", "1000 hours")
add_consumable("lamp-pe-series200", "Perkin Elmer Series 200 UV/vis B0114620", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/e4fd5ac0-af34-4ab8-98bb-ce4ee3f2f530.jpg", "https://www.uvtech-cc.com/products_details/65.html", "B0114620", "Series 200 UV/vis", "Perkin Elmer", "B0114620", "1000 hours")
add_consumable("lamp-pe-lambda-d2", "Perkin Elmer Lambda series L6022728 deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/bd6da430-ba52-4d46-a264-5c827bdc6344.jpg", "https://www.uvtech-cc.com/products_details/64.html", "L6022728", "Lambda", "Perkin Elmer", "L6022728", "2000 hours")
add_consumable("lamp-pe-lambda365", "PE Lambda365 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/9a756faf-68ac-4234-8125-e72faa1d9c8e.jpg", "https://www.uvtech-cc.com/products_details/63.html", "BK82221036", "Lambda365", "Perkin Elmer", "N4101036", "2000 hours")
add_consumable("lamp-knauer-2520-2550", "Knauer 2520/2550 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/270dd2be-09a1-43bf-a093-1853666a66fd.jpg", "https://www.uvtech-cc.com/products_details/62.html", "BK82012520", "2520/2550", "Knauer", "NOT", "2000 hours")
add_consumable("lamp-knauer-2501", "Knauer 2501 ALL", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/b7a1740c-1903-4a6f-b35f-e89294e84914.jpg", "https://www.uvtech-cc.com/products_details/61.html", "BK82024071", "2501 ALL", "Knauer", "NOT", "2000 hours")
add_consumable("lamp-jasco-970b", "Jasco 970B 975B 5330-0091B", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/5c79fede-133c-4d57-90d0-be2c0f6762a8.jpg", "https://www.uvtech-cc.com/products_details/60.html", "BK82000091", "970B/975B, 1570/1575, 2070/2075", "JASCO", "5330-0091B", "2000 hours")
add_consumable("lamp-hitachi-primaide", "Hitachi primaide DAD deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/d3fd4f29-0925-4256-9e4f-71e10d0347e9.jpg", "https://www.uvtech-cc.com/products_details/59.html", "BK82224755", "Primaide DAD", "Hitachi", "2J1-1500/893-4755", "2000 hours")
add_consumable("lamp-hitachi-lc-vwd", "Hitachi LC-VWD", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/774e522b-bca1-465c-b969-822349e4a1ab.jpg", "https://www.uvtech-cc.com/products_details/58.html", "BK81022430", "LC-VWD", "Hitachi", "890-2430/892-2550", "2000 hours")
add_consumable("lamp-analytikjena-ea5000", "Analytik Jena EA5000 equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/cb174a49-0fbf-4b76-9e8b-336d4093f2e7.jpg", "https://www.uvtech-cc.com/products_details/57.html", "11-0402-001-21", "EA5000", "Analytikjena", "11-0402-001-21", "2000 hours")
add_consumable("lamp-analytikjena-specord-plus", "Analytikjena SPECORD PLUS equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/89afbe7f-7cbd-408f-87d4-8438b2a67385.jpg", "https://www.uvtech-cc.com/products_details/56.html", "820-60274-C", "SPECORD PLUS", "Analytikjena", "820-60274-C", "2000 hours")
add_consumable("lamp-analytikjena-specord-2xx", "Analytikjena SPECORD 2xx 820-60021-0", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/1194523d-cdd2-4876-9d28-ab34a384979c.jpg", "https://www.uvtech-cc.com/products_details/55.html", "820-60021-0", "SPECORD 2xx (PLUS)/50(PLUS)/40/30, SPECORD S600, S100, SPEKOL 1200", "Analytikjena", "820-60021-0", "2000 hours")
add_consumable("lamp-agilent-1290-dad", "Agilent 1290 DAD 5190-0917", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/d3436759-88d1-4cf7-95cc-301c61a7be39.jpg", "https://www.uvtech-cc.com/products_details/54.html", "BK82220917", "1290 DAD", "Agilent", "5190-0917 (8 needles)", "2000 hours")
add_consumable("lamp-agilent-vwd", "Agilent (1100/1200/1220/1260) VWD equivalent deuterium lamp", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/b7316b24-5141-447d-ab78-d1101822e5ae.jpg", "https://www.uvtech-cc.com/products_details/53.html", "BK82010100", "1100/1200/1220/1260 VWD", "Agilent", "G1314-60100/60101", "2000 hours")
add_consumable("lamp-agilent-1100-1200-dad", "Agilent 1100/1200 DAD 2140-0820", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/b01655b9-78bf-4f77-889a-2dc39228351a.jpg", "https://www.uvtech-cc.com/products_details/52.html", "BK82220820", "1100/1200/1220/1260 DAD / 1260 MD", "Agilent", "2140-0820", "2000 hours")
add_consumable("lamp-absciex-mdq-plus", "AB SCIEX MDQ plus 144-667", "https://omo-oss-image.thefastimg.com/portal-saas/pg2025032718364349704/cms/image/74727a0d-382a-4450-b202-ef62e0bdf45a.jpg", "https://www.uvtech-cc.com/products_details/51.html", "BK82220251", "P/ACE MDQ plus", "ABSCIEX", "144-667", "2000 hours")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "products.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(PRODUCTS, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(PRODUCTS)} products to {out_path}")
