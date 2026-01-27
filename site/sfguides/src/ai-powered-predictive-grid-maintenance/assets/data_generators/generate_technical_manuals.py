# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate realistic technical manual PDFs for equipment manufacturers
Creates 12 comprehensive operation and maintenance manuals
"""

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Configuration
OUTPUT_DIR = Path(__file__).parent / "generated_technical_manuals"
OUTPUT_DIR.mkdir(exist_ok=True)

# Equipment specifications
EQUIPMENT_SPECS = [
    # ABB Transformers
    {
        "MANUAL_ID": "MAN-ABB-TXP25MVA-001",
        "MANUFACTURER": "ABB",
        "MODEL": "TXP-25MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "OPERATION_MANUAL",
        "CAPACITY_MVA": 25,
        "VOLTAGE_RATING": "138/13.8 kV",
        "COOLING_TYPE": "ONAN/ONAF",
        "WEIGHT_KG": 45000,
        "OIL_VOLUME_L": 12500,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 10.5,
    },
    {
        "MANUAL_ID": "MAN-ABB-TXP35MVA-001",
        "MANUFACTURER": "ABB",
        "MODEL": "TXP-35MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "MAINTENANCE_GUIDE",
        "CAPACITY_MVA": 35,
        "VOLTAGE_RATING": "230/13.8 kV",
        "COOLING_TYPE": "OFAF",
        "WEIGHT_KG": 62000,
        "OIL_VOLUME_L": 17500,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 12.0,
    },
    {
        "MANUAL_ID": "MAN-ABB-DIAG-001",
        "MANUFACTURER": "ABB",
        "MODEL": "All Models",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "TROUBLESHOOTING",
    },
    # GE Transformers
    {
        "MANUAL_ID": "MAN-GE-PTG30MVA-001",
        "MANUFACTURER": "GE",
        "MODEL": "PTG-30MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "OPERATION_MANUAL",
        "CAPACITY_MVA": 30,
        "VOLTAGE_RATING": "138/13.8 kV",
        "COOLING_TYPE": "ONAN/ONAF",
        "WEIGHT_KG": 50000,
        "OIL_VOLUME_L": 13500,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 11.0,
    },
    {
        "MANUAL_ID": "MAN-GE-PTG30MVA-002",
        "MANUFACTURER": "GE",
        "MODEL": "PTG-30MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "MAINTENANCE_GUIDE",
        "CAPACITY_MVA": 30,
        "VOLTAGE_RATING": "138/13.8 kV",
        "COOLING_TYPE": "ONAN/ONAF",
        "WEIGHT_KG": 50000,
        "OIL_VOLUME_L": 13500,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 11.0,
    },
    {
        "MANUAL_ID": "MAN-GE-TROUBLESHOOT-001",
        "MANUFACTURER": "GE",
        "MODEL": "All Models",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "TROUBLESHOOTING",
    },
    # Siemens Transformers
    {
        "MANUAL_ID": "MAN-SIEMENS-H25-001",
        "MANUFACTURER": "Siemens",
        "MODEL": "H-Class-25MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "OPERATION_MANUAL",
        "CAPACITY_MVA": 25,
        "VOLTAGE_RATING": "138/13.8 kV",
        "COOLING_TYPE": "ONAN",
        "WEIGHT_KG": 43000,
        "OIL_VOLUME_L": 11800,
        "TEMP_RISE_C": 55,
        "IMPEDANCE_PCT": 10.0,
    },
    {
        "MANUAL_ID": "MAN-SIEMENS-H35-001",
        "MANUFACTURER": "Siemens",
        "MODEL": "H-Class-35MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "SPECIFICATIONS",
        "CAPACITY_MVA": 35,
        "VOLTAGE_RATING": "230/13.8 kV",
        "COOLING_TYPE": "OFAF",
        "WEIGHT_KG": 60000,
        "OIL_VOLUME_L": 16500,
        "TEMP_RISE_C": 55,
        "IMPEDANCE_PCT": 11.5,
    },
    {
        "MANUAL_ID": "MAN-SIEMENS-MAINT-001",
        "MANUFACTURER": "Siemens",
        "MODEL": "H-Class Series",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "MAINTENANCE_GUIDE",
    },
    # Westinghouse Transformers
    {
        "MANUAL_ID": "MAN-WESTING-WPT25-001",
        "MANUFACTURER": "Westinghouse",
        "MODEL": "WPT-25MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "OPERATION_MANUAL",
        "CAPACITY_MVA": 25,
        "VOLTAGE_RATING": "138/13.8 kV",
        "COOLING_TYPE": "ONAN/ONAF",
        "WEIGHT_KG": 47000,
        "OIL_VOLUME_L": 12800,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 10.8,
    },
    {
        "MANUAL_ID": "MAN-WESTING-WPT35-001",
        "MANUFACTURER": "Westinghouse",
        "MODEL": "WPT-35MVA",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "MAINTENANCE_GUIDE",
        "CAPACITY_MVA": 35,
        "VOLTAGE_RATING": "230/13.8 kV",
        "COOLING_TYPE": "OFAF",
        "WEIGHT_KG": 63000,
        "OIL_VOLUME_L": 17800,
        "TEMP_RISE_C": 65,
        "IMPEDANCE_PCT": 12.2,
    },
    {
        "MANUAL_ID": "MAN-WESTING-SPEC-001",
        "MANUFACTURER": "Westinghouse",
        "MODEL": "WPT Series",
        "EQUIPMENT_TYPE": "Power Transformer",
        "MANUAL_TYPE": "SPECIFICATIONS",
    },
]

# Manual content templates
OPERATION_MANUAL_CONTENT = """
1. INTRODUCTION

This operation manual provides comprehensive guidance for the safe and efficient operation of {manufacturer} {model} power transformers. These transformers are designed for utility applications and meet all relevant IEEE and IEC standards.

2. SAFETY PRECAUTIONS

WARNING: High voltage equipment. Only qualified personnel should operate and maintain this equipment.

- Always de-energize equipment before performing any work
- Follow proper lockout/tagout procedures
- Wear appropriate personal protective equipment (PPE)
- Maintain minimum approach distances per OSHA regulations
- Never operate equipment beyond nameplate ratings

3. TECHNICAL SPECIFICATIONS

Primary Voltage:         {voltage_high} kV
Secondary Voltage:       {voltage_low} kV
Rated Capacity:          {capacity} MVA
Cooling Method:          {cooling}
Total Weight:            {weight:,} kg
Insulating Oil Volume:   {oil:,} liters
Temperature Rise:        {temp_rise}°C above ambient
Impedance:               {impedance}%
Frequency:               60 Hz
Insulation Class:        155°C (Class F)

4. NORMAL OPERATING PARAMETERS

Oil Temperature:
  - Normal operation: 60-75°C
  - Maximum continuous: 95°C
  - Emergency overload: 105°C (2 hours max)

Winding Temperature (calculated):
  - Normal: 75-90°C
  - Maximum continuous: 110°C
  - Short-term overload: 130°C

Load Limits:
  - Continuous: 100% of nameplate rating
  - Short-term overload: 120% for 4 hours max
  - Emergency overload: 140% for 30 minutes max

Oil Level:
  - Check gauge daily
  - Maintain between 80-90% full marks
  - Temperature compensated indicator

5. OPERATING PROCEDURES

5.1 Pre-Energization Checks
  a) Verify all protective relays are in service
  b) Check oil level and color
  c) Inspect for external leaks or damage
  d) Verify cooling system operation
  e) Check all connections are tight
  f) Review dissolved gas analysis (DGA) results if available
  g) Confirm power factor within limits (< 0.5%)

5.2 Energization Sequence
  a) Close primary circuit breaker (HV side)
  b) Monitor inrush current (should decay in 5-10 cycles)
  c) Verify no unusual sounds or vibrations
  d) Check oil and winding temperatures
  e) After 30 minutes of no-load operation, proceed to load

5.3 Load Application
  a) Apply load gradually, monitoring temperatures
  b) Do not exceed 50% load for first hour after energization
  c) Verify cooling fans activate at set points
  d) Monitor dissolved gas levels for first 24 hours

5.4 Normal Monitoring
  - Check oil temperature gauge every 4 hours
  - Monitor load levels continuously via SCADA
  - Listen for abnormal sounds during daily inspections
  - Check cooling equipment weekly
  - Review trend data for early warning signs

6. ALARM CONDITIONS

HIGH OIL TEMPERATURE ALARM (85°C):
  - Verify cooling system operation
  - Check load levels
  - Reduce load if temperature continues to rise
  - Investigate if alarm persists with normal load

PRESSURE RELIEF DEVICE OPERATION:
  - IMMEDIATELY de-energize transformer
  - Do not re-energize until fault is cleared
  - Perform internal inspection and testing
  - Contact manufacturer for guidance

LOW OIL LEVEL ALARM:
  - Check for external leaks
  - Add oil only if transformer is de-energized
  - Use only manufacturer-approved oil
  - Investigate cause of oil loss

BUCHHOLZ RELAY TRIP:
  - Indicates internal fault or gas accumulation
  - Do not re-energize without investigation
  - Perform dissolved gas analysis
  - Inspect for internal damage

7. COOLING SYSTEM OPERATION

{cooling} Cooling System:
  - ONAN: Natural oil circulation, natural air cooling
  - ONAF: Natural oil circulation, forced air (fans)
  - OFAF: Forced oil circulation through external radiators with fans

Cooling Fan Control:
  - Stage 1: Activate at 65°C oil temperature
  - Stage 2: Activate at 75°C oil temperature
  - Manual override available on control panel
  - Test fans monthly under no-load conditions

8. EMERGENCY PROCEDURES

FIRE:
  - Activate fire suppression system
  - Isolate transformer immediately
  - Evacuate personnel
  - Call emergency services
  - Use Class C fire extinguishers only

OIL SPILL:
  - Contain spill using absorbent materials or booms
  - Prevent entry into waterways
  - Notify environmental authorities if required
  - Clean up per EPA regulations

OVERLOAD EMERGENCY:
  - If load exceeds 140%, attempt to shed load immediately
  - If temperature exceeds limits, trip transformer
  - Allow 4-hour cooling period before re-energization
  - Document event and perform DGA analysis

9. MAINTENANCE SCHEDULE

Daily:
  - Visual inspection
  - Temperature readings
  - Sound check

Weekly:
  - Cooling system check
  - Bushing inspection
  - Connection tightness check (thermography recommended)

Monthly:
  - Oil sample (if equipped with sampling valve)
  - Moisture indicator check
  - Pressure relief device test
  - Dehydrating breather inspection

Quarterly:
  - Detailed visual inspection
  - Load tap changer operation (if equipped)
  - Protective relay test
  - Grounding system continuity

Annually:
  - Dissolved gas analysis (DGA)
  - Power factor test
  - Turns ratio test
  - Winding resistance measurement
  - Oil dielectric strength test
  - Infrared thermography scan

10. TROUBLESHOOTING QUICK REFERENCE

High Oil Temperature:
  - Check cooling fans
  - Verify normal load
  - Inspect radiators for blockage
  - Check oil pump (if forced cooling)

Unusual Noise:
  - Increased hum: Check for loose core
  - Banging: Internal fault - de-energize immediately
  - Clicking: Loose connections or tap changer issue

Low Insulation Resistance:
  - Moisture contamination - perform oil processing
  - Winding degradation - consider replacement
  - External contamination - clean bushings

For additional support, contact {manufacturer} Technical Service:
Phone: 1-800-{manufacturer}-HELP
Email: technical.support@{manufacturer}.com
Web: www.{manufacturer}.com/support

Document Version: 1.0
Publication Date: January 2024
Copyright © {manufacturer} Corporation. All rights reserved.
"""

MAINTENANCE_GUIDE_CONTENT = """
MAINTENANCE GUIDE

{manufacturer} {model} Power Transformer
Preventive Maintenance Procedures

1. MAINTENANCE PHILOSOPHY

Preventive maintenance is essential to ensure long service life and reliable operation. This guide outlines recommended maintenance intervals and procedures based on industry best practices and manufacturer experience.

2. MAINTENANCE SCHEDULE OVERVIEW

MONTHLY PROCEDURES (1-2 hours):
  □ Visual inspection for oil leaks
  □ Check oil level and color
  □ Verify cooling system operation
  □ Inspect bushings for cracks or tracking
  □ Check pressure gauges
  □ Test temperature indicators
  □ Inspect lightning arresters
  □ Review SCADA alarm history

QUARTERLY PROCEDURES (4-6 hours):
  □ All monthly items plus:
  □ Thermography scan of all connections
  □ Tap changer operation test (10 cycles)
  □ Verify relay settings and operation
  □ Check nitrogen blanket pressure (if equipped)
  □ Inspect foundation and grounding
  □ Lubricate tap changer mechanism
  □ Test cooling fan operation (all stages)

ANNUAL PROCEDURES (2-3 days):
  □ All quarterly items plus:
  □ Dissolved Gas Analysis (DGA)
  □ Oil quality testing (dielectric, acidity, moisture, PCB)
  □ Power factor/tan delta test
  □ Turns ratio test
  □ Winding resistance measurement
  □ Insulation resistance (megger) test
  □ Tap changer contact resistance
  □ Bushing power factor test
  □ Protective relay calibration
  □ Lightning arrester test
  □ Gasket and seal inspection
  □ Paint touch-up as needed
  □ Documentation review and update

3. DETAILED MAINTENANCE PROCEDURES

3.1 OIL SAMPLING AND ANALYSIS

Purpose: Detect internal faults, aging, and contamination
Frequency: Annually, or when DGA indicates issue

Procedure:
1. Ensure transformer has been energized for at least 24 hours
2. Wear clean nitrile gloves to prevent contamination
3. Purge sampling valve (100ml) before collecting sample
4. Collect sample in clean, dry bottle provided by lab
5. Fill bottle completely to eliminate headspace
6. Cap immediately and label with asset ID and date
7. Ship to laboratory within 24 hours
8. Request full DGA panel, dielectric strength, moisture, acidity

Interpretation Guidelines:
- Hydrogen (H2) > 100 ppm: Possible partial discharge
- Acetylene (C2H2) > 1 ppm: Possible arcing
- Carbon monoxide (CO) > 500 ppm: Paper insulation degradation
- Ethylene (C2H4) > 50 ppm: Local overheating above 150°C
- Moisture > 35 ppm: Compromised insulation, consider oil processing
- Acidity > 0.2 mg KOH/g: Oil aging, plan oil reconditioning

3.2 THERMOGRAPHIC INSPECTION

Purpose: Detect loose connections, unbalanced loads, cooling issues
Frequency: Quarterly, or after any maintenance on connections

Procedure:
1. Perform scan during loaded conditions (>50% of rating)
2. Use infrared camera with minimum 320×240 resolution
3. Scan all external connections, bushings, and tap changer
4. Scan radiators to verify uniform cooling
5. Document all temperature differences greater than 10°C
6. Compare phase-to-phase temperatures (should be within 5°C)

Action Levels:
- ΔT < 10°C: Normal, continue monitoring
- ΔT 10-20°C: Investigate at next maintenance window
- ΔT 20-30°C: Schedule corrective action within 30 days
- ΔT > 30°C: Immediate investigation required

3.3 COOLING SYSTEM MAINTENANCE

Fan Motors:
- Check bearings for smooth operation (no grinding sounds)
- Measure vibration: < 0.2 inches/second is acceptable
- Verify correct rotation direction
- Check electrical connections for tightness
- Lubricate bearings per manufacturer schedule (typically annually)

Radiators:
- Clean external surfaces annually (compressed air or water)
- Check for oil leaks at connections
- Verify all isolation valves are open during operation
- Inspect for physical damage or corrosion

Oil Pumps (if equipped):
- Check motor current draw (should be within ±10% of nameplate)
- Listen for unusual noises indicating bearing wear
- Verify oil flow through inspection window
- Check seal for leakage
- Lubricate motor bearings per schedule

3.4 BUSHING MAINTENANCE

Purpose: Prevent flashover and insulation failure
Frequency: Quarterly visual, annual electrical test

Visual Inspection:
- Check for cracks in porcelain
- Look for oil leakage at base
- Inspect for tracking marks (carbon trails)
- Verify oil level in oil-filled bushings
- Check cleanliness (wash if contaminated)

Electrical Testing:
- Power factor test (should be < 0.5% at 10 kV)
- Capacitance measurement (compare to baseline)
- Insulation resistance (megohm meter)

Cleaning Procedure:
1. De-energize and lockout transformer
2. Use clean water and soft brush
3. For heavy contamination, use approved solvent
4. Rinse thoroughly and dry
5. Do not use high-pressure water (can damage seals)

3.5 TAP CHANGER MAINTENANCE

Purpose: Ensure reliable voltage regulation
Frequency: Quarterly operation test, annual inspection

Operation Test:
1. Record current tap position
2. Operate through full range (raise to maximum, lower to minimum)
3. Listen for smooth, consistent operation
4. Verify position indicator accuracy
5. Check auto/manual selector operation
6. Return to original position

Annual Inspection (with transformer de-energized):
1. Measure contact resistance (should be < 500 microhms)
2. Inspect contacts for pitting or burning
3. Check mechanical linkage for wear
4. Verify limit switch operation
5. Lubricate mechanism per manufacturer recommendations
6. Test interlock functionality
7. Verify tap change does not occur under load (if LTC)

3.6 INTERNAL INSPECTION (Every 10-15 years)

Requires:
- De-energization and lockout
- Draining of oil
- Entry into confined space (permit required)
- Nitrogen purge of vapor space

Inspection Points:
- Core and coil condition
- Insulation integrity
- Internal connections and supports
- Tank interior for sludge or contamination
- Tap changer contacts and mechanism
- Pressure relief devices
- Internal sensors and monitors

This is a major undertaking requiring specialized contractors and should be planned well in advance.

4. RECORD KEEPING

Maintain comprehensive records including:
- As-built drawings and specifications
- All test results with trend data
- Maintenance activities (dates, personnel, findings)
- Operating conditions (load, temperature, events)
- Oil analysis results
- Thermography images
- Repair history
- Parts replaced (with serial numbers)
- Manufacturer correspondence

Use a Computerized Maintenance Management System (CMMS) to track all activities and set up automatic reminders for scheduled maintenance.

5. SPARE PARTS RECOMMENDATIONS

Critical Spares (keep in inventory):
- Oil samples bottles and DGA kits
- Pressure gauge
- Temperature gauge
- Gaskets for manhole and handhole covers
- Bushings (at least one per voltage class)
- Cooling fan motors (1 spare)
- Pressure relief device
- Oil filter elements
- Lightning arresters

Long-Lead Items (know supplier and lead time):
- Load tap changer contacts
- Internal coils or windings
- Transformer oil (compatible type)
- Radiator sections
- Oil pumps

6. SAFETY CONSIDERATIONS

- Confined space entry procedures for internal inspection
- Arc flash analysis and appropriate PPE
- Lock out/tag out procedures
- Oil handling and spill response
- PCB contamination (if unit manufactured before 1980)
- Environmental regulations for oil disposal

For technical support or parts, contact:
{manufacturer} Service Department
Phone: 1-800-{manufacturer}-SERV
Email: service@{manufacturer}.com

Document Version: 2.1
Publication Date: March 2024
Copyright © {manufacturer} Corporation. All rights reserved.
"""

TROUBLESHOOTING_CONTENT = """
TROUBLESHOOTING GUIDE

{manufacturer} Power Transformers - All Models
Diagnostic Procedures and Fault Resolution

1. SYSTEMATIC TROUBLESHOOTING APPROACH

Step 1: Identify the symptom
Step 2: Check for obvious causes
Step 3: Review recent changes or events
Step 4: Perform diagnostic tests
Step 5: Analyze results
Step 6: Implement corrective action
Step 7: Verify resolution
Step 8: Document findings

2. COMMON PROBLEMS AND SOLUTIONS

═══════════════════════════════════════════════════════════════════

PROBLEM: High Oil Temperature

Symptoms:
- Oil temperature gauge reads > 85°C
- High temperature alarm
- Oil temperature rising faster than load

Possible Causes:
1. Cooling system failure
2. Overload condition
3. Internal fault
4. Blocked cooling passages
5. Faulty temperature gauge

Diagnostic Steps:
1. Verify actual oil temperature using independent thermometer
2. Check transformer load vs nameplate rating
3. Verify all cooling fans are running
4. Check oil pump operation (if equipped with forced cooling)
5. Inspect radiators for air flow blockage
6. Review recent DGA results for fault gases
7. Perform infrared scan to identify hot spots

Resolution:
- If cooling failure: Repair/replace fans or pumps immediately
- If overload: Reduce load or transfer to parallel transformer
- If internal fault: De-energize and perform detailed investigation
- If gauge fault: Replace gauge but continue monitoring with alternate means

═══════════════════════════════════════════════════════════════════

PROBLEM: Unusual Noise or Vibration

Symptoms:
- Increased hum level
- Intermittent banging sounds
- Rhythmic clicking
- Excessive vibration

Possible Causes:
1. Loose core laminations
2. Loose connections or bushings
3. Internal arcing fault
4. Tap changer problem
5. Magnetostriction (normal hum amplified by resonance)

Diagnostic Steps:
1. Listen carefully to localize source
2. Check for recent changes in load or voltage
3. Measure vibration levels with accelerometer
4. Perform power quality analysis (look for harmonics)
5. Check all external connections for tightness
6. Review DGA for acetylene (indicates arcing)

Resolution:
- Loose core: Requires internal repair - schedule outage
- Loose connections: Tighten during next maintenance outage
- Internal arcing: IMMEDIATE de-energization required
- Tap changer: Inspect and repair tap changer mechanism
- Magnetostriction: May require damping pads or structural modifications

═══════════════════════════════════════════════════════════════════

PROBLEM: Low Insulation Resistance

Symptoms:
- Megger test shows < 1000 megohms
- High power factor (> 2%)
- Trending decrease in insulation resistance

Possible Causes:
1. Moisture contamination
2. Insulation degradation
3. External contamination on bushings
4. Oil contamination

Diagnostic Steps:
1. Clean bushings and retest
2. Perform oil moisture test
3. Check oil dielectric strength
4. Perform power factor test at multiple voltages
5. Check for external leakage paths
6. Review maintenance history

Resolution:
- Moisture: Oil processing or filtration
- Contaminated oil: Oil replacement or reconditioning
- Bushing contamination: Clean with approved solvent
- Insulation failure: May require transformer replacement

═══════════════════════════════════════════════════════════════════

PROBLEM: Oil Leaks

Symptoms:
- Visible oil around gaskets, bushings, or valves
- Decreasing oil level
- Oil stains on ground beneath transformer

Possible Causes:
1. Gasket failure
2. Loose bolts
3. Cracked bushing seal
4. Valve packing failure
5. Tank corrosion

Diagnostic Steps:
1. Clean area thoroughly and observe for active leak
2. Check all visible bolts for proper torque
3. Inspect gasket surfaces
4. Use UV dye if leak source is not obvious
5. Check for tank corrosion or cracks

Resolution:
- Gasket leak: Replace gasket (may require oil drain)
- Loose bolts: Torque to specification
- Bushing seal: Replace bushing or reseal
- Valve packing: Repack or replace valve
- Tank crack: Weld repair by qualified welder (requires oil drain)

═══════════════════════════════════════════════════════════════════

PROBLEM: Buchholz Relay Operation

Symptoms:
- Alarm or trip from Buchholz (sudden pressure) relay
- Visible gas collection in relay sight glass

Possible Causes:
1. Internal arcing fault
2. Local overheating
3. Air introduction during maintenance
4. Oil decomposition

Diagnostic Steps:
1. Do NOT re-energize without investigation
2. Collect gas sample from Buchholz relay
3. Perform dissolved gas analysis immediately
4. Inspect for external damage
5. Review recent maintenance activities
6. Check all electrical protective relay targets

Resolution:
- If fault gases present: Internal inspection required
- If air only: May be from maintenance - monitor closely
- If continuous gas generation: Internal fault - transformer replacement may be needed

═══════════════════════════════════════════════════════════════════

PROBLEM: Pressure Relief Device Operation

Symptoms:
- Pressure relief device has lifted
- Visible indicator or alarm
- Possible oil spray from relief valve

Possible Causes:
1. Severe internal fault
2. Through fault (external short circuit)
3. Device malfunction

Diagnostic Steps:
1. IMMEDIATELY isolate transformer
2. Document conditions at time of operation
3. Inspect for external damage
4. Perform insulation resistance tests
5. Perform turns ratio test
6. Perform DGA (expect high fault gas levels)

Resolution:
- Through fault only: Perform full testing, may return to service if tests pass
- Internal fault: Likely requires major repair or replacement
- Device malfunction: Test and recalibrate or replace device

3. DIAGNOSTIC TEST PROCEDURES

3.1 Dissolved Gas Analysis (DGA)
See detailed interpretation in Maintenance Guide
Key gases: H2, CH4, C2H6, C2H4, C2H2, CO, CO2

3.2 Power Factor / Dissipation Factor Test
Procedure: Apply AC voltage, measure power loss
Acceptance: < 0.5% at 10 kV, 20°C
High results indicate moisture or insulation degradation

3.3 Turns Ratio Test
Procedure: Apply voltage to one winding, measure others
Acceptance: Within ±0.5% of calculated ratio
Deviations indicate shorted turns

3.4 Winding Resistance Test
Procedure: Apply DC current, measure voltage drop
Purpose: Detect shorted turns, poor connections
Compare phase-to-phase: should be within 5%

3.5 Insulation Resistance (Megger) Test
Apply DC voltage (typically 2.5-5 kV for 1 minute)
Record resistance after 1 minute
Acceptance: > 1000 megohms (higher is better)

4. WHEN TO CALL FOR HELP

Contact manufacturer or specialist if:
- Internal fault is suspected
- Test results are significantly abnormal
- Major repair is required
- Replacement is being considered
- Second opinion is needed

{manufacturer} Emergency Hotline: 1-800-{manufacturer}-911
Available 24/7/365

Document Version: 1.5
Last Updated: February 2024
Copyright © {manufacturer} Corporation. All rights reserved.
"""

SPECIFICATIONS_CONTENT = """
TECHNICAL SPECIFICATIONS

{manufacturer} {model}
Power Transformer - Complete Technical Data

1. GENERAL INFORMATION

Equipment Type:          Power Transformer, Oil-Immersed
Manufacturer:            {manufacturer} Corporation
Model Number:            {model}
Standards Compliance:    IEEE C57.12.00, IEEE C57.12.90, IEC 60076

2. ELECTRICAL RATINGS

Rated Power:             {capacity} MVA
Rated Frequency:         60 Hz
Number of Phases:        3
Primary Voltage:         {voltage_high} kV
Secondary Voltage:       {voltage_low} kV
Connection Type:         Wye-Wye, Grounded
Impedance:               {impedance}% on {capacity} MVA base
BIL (Primary):           550 kV (for 138 kV class)
BIL (Secondary):         110 kV (for 13.8 kV class)

3. TEMPERATURE RATINGS

Temperature Rise (Oil):  {temp_rise}°C above ambient
Temperature Rise (Avg Winding): {temp_rise}°C above ambient
Hot Spot Temperature:    15°C above average winding
Ambient Temperature:     -30°C to +50°C
Insulation Class:        155°C (Class F)
Service Factor:          1.0 continuous, 1.15 for 4 hours, 1.25 for 30 minutes

4. COOLING SYSTEM

Cooling Type:            {cooling}
  ONAN: Self-cooled (natural oil circulation, natural air)
  ONAF: Oil Natural, Air Forced (fans)
  OFAF: Oil Forced, Air Forced (pumps and fans)

Cooling Stages:
  - Stage 1 (ONAN): 10 MVA base rating
  - Stage 2 (ONAF): 16.67 MVA with first fan stage
  - Stage 3 (ONAF): {capacity} MVA with all fans

Fan Specifications:
  - Type: Axial flow, direct drive
  - Quantity: 6 fans (3 per stage)
  - Motor: 0.37 kW, 460V, 3-phase
  - Air Flow: 1500 CFM per fan

5. MECHANICAL SPECIFICATIONS

Overall Dimensions:
  - Length: 4.8 meters
  - Width: 3.2 meters
  - Height: 5.1 meters (including bushings)
  - Ground Clearance: 0.5 meters

Weight:
  - Total Weight: {weight:,} kg
  - Core & Coils: {core_weight:,.0f} kg
  - Tank & Fittings: {tank_weight:,.0f} kg
  - Oil: {oil_weight:,.0f} kg
  - Shipping Weight: {shipping_weight:,.0f} kg

Tank Construction:
  - Material: Carbon steel plate, ASTM A36
  - Wall Thickness: 8-12 mm depending on location
  - Internal Finish: Cleaned and coated
  - External Finish: Epoxy primer + polyurethane top coat
  - Color: Gray (RAL 7035) or customer specified

6. INSULATION SYSTEM

Insulating Fluid:
  - Type: Mineral oil per ASTM D3487 Type II
  - Volume: {oil:,} liters
  - Dielectric Strength: Min. 30 kV (new oil)
  - Pour Point: -40°C
  - Flash Point: > 140°C

Solid Insulation:
  - Type: Thermally upgraded Kraft paper
  - Temperature Rating: 130°C continuous

Preservation System:
  - Type: Sealed tank with conservator
  - Gas Blanket: Dry nitrogen, 5 psig
  - Dehydrating Breather: Silica gel type

7. ACCESSORIES AND EQUIPMENT

Standard Equipment:
  ✓ Buchholz relay (sudden pressure)
  ✓ Pressure relief device
  ✓ Oil temperature gauge with contacts
  ✓ Winding temperature indicator (WTI)
  ✓ Oil level gauge (magnetic type)
  ✓ Drain and sampling valves
  ✓ Lifting lugs and jacking pads
  ✓ Nameplate (stainless steel)
  ✓ Terminal boards in control cabinet
  ✓ Cooling system control panel

Optional Equipment:
  ○ Tap changer (load or no-load)
  ○ Current transformers for protection
  ○ Partial discharge monitoring
  ○ Dissolved gas monitoring (online)
  ○ Fiber optic temperature sensors
  ○ Seismic withstand certification

8. BUSHINGS

High Voltage (Primary) Bushings:
  - Type: Oil-to-air, porcelain
  - Voltage Class: 138 kV or 230 kV
  - BIL: 550 kV or 900 kV
  - Current Rating: Match transformer
  - Quantity: 3 (one per phase)

Low Voltage (Secondary) Bushings:
  - Type: Draw-through bushing
  - Voltage Class: 15 kV
  - BIL: 110 kV
  - Current Rating: Match transformer
  - Quantity: 3 (one per phase)

Neutral Bushing:
  - Type: Post-type insulator
  - Quantity: 1 on HV, 1 on LV

9. PERFORMANCE DATA

No-Load Losses:          18 kW (typical)
Load Losses (at rated): 85 kW (typical)
Total Losses:            103 kW
Efficiency at Full Load: 99.59%
Exciting Current:        0.8% of rated current
Sound Level:             58 dB(A) at 0.3 meters (NEMA)

10. TESTING AND QUALITY ASSURANCE

Routine Tests (per IEEE):
  ✓ Turns ratio measurement
  ✓ Polarity and phase-relation
  ✓ Resistance measurement of windings
  ✓ No-load losses and exciting current
  ✓ Load losses and impedance voltage
  ✓ Applied voltage test
  ✓ Induced voltage test
  ✓ Sound level measurement
  ✓ Oil quality tests

Special Tests (on request):
  ○ Temperature rise test
  ○ Short circuit test
  ○ Lightning impulse test
  ○ Seismic qualification
  ○ Loss evaluation

Quality Certifications:
  - ISO 9001:2015 Quality Management
  - ISO 14001:2015 Environmental Management
  - OHSAS 18001 Occupational Health & Safety

11. INSTALLATION REQUIREMENTS

Foundation:
  - Type: Reinforced concrete pad
  - Minimum thickness: 300 mm
  - Load bearing: 150 kPa minimum
  - Dimensions: 5.5m × 4.0m
  - Oil containment: 120% of oil volume

Clearances:
  - Front (bushing side): 4.0 meters
  - Rear: 2.5 meters
  - Sides: 2.0 meters
  - Overhead: 6.0 meters (for crane access)

Environmental:
  - Operating altitude: Up to 1000m above sea level
  - Humidity: Up to 95% RH non-condensing
  - Seismic zone: Suitable for Zone 4 (with seismic option)
  - Wind loading: 150 km/h

12. MAINTENANCE ACCESS

  - Manhole: 450mm × 350mm on tank top
  - Handholes: Multiple locations for internal access
  - Drain valve: 50mm, located at lowest point
  - Sampling valve: 19mm, mid-height on tank side
  - All fasteners: Metric, stainless steel

13. SPARE PARTS

Recommended Spares:
  - Cooling fan motors (1 spare)
  - Temperature gauges (1 set)
  - Pressure gauge (1 unit)
  - Gaskets for all openings
  - Bushings (1 per voltage class)
  - Pressure relief device
  - Oil samples bottles (12)

Part Availability:
  Standard parts: 2-4 weeks
  Major components: 8-12 weeks
  Full replacement: 52-78 weeks

14. WARRANTY AND SUPPORT

Standard Warranty: 24 months from commissioning or 30 months from shipment
Extended Warranty: Available up to 10 years
Technical Support: 24/7 hotline, field service available
Training: Installation and maintenance training included

For more information:
{manufacturer} Corporation
Power Transformer Division
Web: www.{manufacturer}.com/transformers
Email: transformers@{manufacturer}.com
Phone: +1-800-{manufacturer}-PWR

Document Number: {manual_id}
Revision: A
Date: January 2024
© {manufacturer} Corporation. All rights reserved.
This document contains proprietary information and may not be reproduced without permission.
"""

def create_manual_pdf(spec, output_path):
    """Generate a comprehensive technical manual PDF"""
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitlePage',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=32
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading1 = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=20,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyJustified',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=10,
        leading=14
    )
    
    # Title page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(f"{spec['MANUFACTURER']} CORPORATION", title_style))
    story.append(Paragraph(f"{spec['EQUIPMENT_TYPE']}", subtitle_style))
    story.append(Paragraph(f"Model: {spec['MODEL']}", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    
    manual_type_display = spec['MANUAL_TYPE'].replace('_', ' ').title()
    story.append(Paragraph(f"{manual_type_display}", title_style))
    
    story.append(Spacer(1, 1.5*inch))
    
    # Document info box
    info_data = [
        ['Document Number:', spec['MANUAL_ID']],
        ['Revision:', 'A'],
        ['Date:', 'January 2024'],
        ['Status:', 'Released'],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(info_table)
    
    # Copyright notice
    story.append(Spacer(1, 1*inch))
    copyright_text = f"© {datetime.now().year} {spec['MANUFACTURER']} Corporation. All rights reserved.<br/>This document contains proprietary information."
    story.append(Paragraph(copyright_text, ParagraphStyle('Copyright', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    story.append(PageBreak())
    
    # Select content based on manual type
    mfg = spec['MANUFACTURER']
    model = spec['MODEL']
    
    if spec['MANUAL_TYPE'] == 'OPERATION_MANUAL':
        content_template = OPERATION_MANUAL_CONTENT
        content_vars = {
            'manufacturer': mfg,
            'model': model,
            'voltage_high': str(spec.get('VOLTAGE_RATING', '138/13.8 kV')).split('/')[0],
            'voltage_low': str(spec.get('VOLTAGE_RATING', '138/13.8 kV')).split('/')[-1],
            'capacity': spec.get('CAPACITY_MVA', 25),
            'cooling': spec.get('COOLING_TYPE', 'ONAN/ONAF'),
            'weight': spec.get('WEIGHT_KG', 45000),
            'oil': spec.get('OIL_VOLUME_L', 12500),
            'temp_rise': spec.get('TEMP_RISE_C', 65),
            'impedance': spec.get('IMPEDANCE_PCT', 10.5),
        }
    elif spec['MANUAL_TYPE'] == 'MAINTENANCE_GUIDE':
        content_template = MAINTENANCE_GUIDE_CONTENT
        content_vars = {'manufacturer': mfg, 'model': model}
    elif spec['MANUAL_TYPE'] == 'TROUBLESHOOTING':
        content_template = TROUBLESHOOTING_CONTENT
        content_vars = {'manufacturer': mfg, 'model': model}
    else:  # SPECIFICATIONS
        content_template = SPECIFICATIONS_CONTENT
        weight = spec.get('WEIGHT_KG', 45000)
        oil_volume = spec.get('OIL_VOLUME_L', 12500)
        content_vars = {
            'manufacturer': mfg,
            'model': model,
            'manual_id': spec['MANUAL_ID'],
            'capacity': spec.get('CAPACITY_MVA', 25),
            'voltage_high': str(spec.get('VOLTAGE_RATING', '138/13.8 kV')).split('/')[0],
            'voltage_low': str(spec.get('VOLTAGE_RATING', '138/13.8 kV')).split('/')[-1],
            'cooling': spec.get('COOLING_TYPE', 'ONAN/ONAF'),
            'weight': weight,
            'oil': oil_volume,
            'oil_volume': oil_volume,
            'temp_rise': spec.get('TEMP_RISE_C', 65),
            'impedance': spec.get('IMPEDANCE_PCT', 10.5),
            'core_weight': weight * 0.4,
            'tank_weight': weight * 0.25,
            'oil_weight': oil_volume * 0.9,
            'shipping_weight': weight * 1.1,
        }
    
    # Format content
    content_text = content_template.format(**content_vars)
    
    # Convert content to paragraphs
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.1*inch))
        elif line.startswith('═══'):
            # Separator line
            story.append(Spacer(1, 0.1*inch))
        elif line.endswith(':') and len(line) < 60 and line.isupper():
            # Section header
            story.append(Paragraph(line, heading1))
        else:
            # Regular paragraph
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    try:
        doc.build(story)
        return output_path
    except Exception as e:
        print(f"Error creating manual {output_path}: {e}")
        return None

def generate_technical_manuals():
    """Generate all technical manual PDFs"""
    
    print(f"\n📚 Generating {len(EQUIPMENT_SPECS)} technical manuals...\n")
    
    metadata_list = []
    
    for i, spec in enumerate(EQUIPMENT_SPECS):
        pdf_filename = f"{spec['MANUAL_ID']}.pdf"
        pdf_path = OUTPUT_DIR / pdf_filename
        
        print(f"✅ [{i+1}/{len(EQUIPMENT_SPECS)}] Creating: {pdf_filename}")
        
        result = create_manual_pdf(spec, pdf_path)
        
        if result:
            # Create metadata
            metadata = {
                'MANUAL_ID': spec['MANUAL_ID'],
                'MANUAL_TYPE': spec['MANUAL_TYPE'],
                'EQUIPMENT_TYPE': spec['EQUIPMENT_TYPE'],
                'MANUFACTURER': spec['MANUFACTURER'],
                'MODEL': spec['MODEL'],
                'VERSION': '1.0',
                'PUBLICATION_DATE': '2024-01-15',
                'FILE_PATH': f"@TECHNICAL_MANUALS_STAGE/{pdf_filename}",
                'FILE_SIZE_BYTES': pdf_path.stat().st_size,
                'PAGE_COUNT': 15 if spec['MANUAL_TYPE'] in ['OPERATION_MANUAL', 'MAINTENANCE_GUIDE'] else 8,
            }
            metadata_list.append(metadata)
    
    # Save metadata
    metadata_file = OUTPUT_DIR / "technical_manuals_metadata.json"
    with open(metadata_file, 'w') as f:
        for doc in metadata_list:
            f.write(json.dumps(doc) + '\n')
    
    print(f"\n✅ Generated {len(metadata_list)} technical manual PDFs")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📄 Metadata file: {metadata_file}")
    
    total_size = sum(p.stat().st_size for p in OUTPUT_DIR.glob("*.pdf") if p.is_file())
    print(f"💾 Total size: {total_size / 1024 / 1024:.2f} MB")
    
    # Statistics
    print("\n📊 Manual Statistics:")
    for mtype in ['OPERATION_MANUAL', 'MAINTENANCE_GUIDE', 'TROUBLESHOOTING', 'SPECIFICATIONS']:
        count = sum(1 for d in metadata_list if d['MANUAL_TYPE'] == mtype)
        print(f"   {mtype:20s}: {count}")
    
    return metadata_list

if __name__ == "__main__":
    generate_technical_manuals()

