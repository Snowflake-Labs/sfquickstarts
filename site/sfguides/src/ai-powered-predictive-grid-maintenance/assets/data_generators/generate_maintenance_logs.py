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
Generate realistic maintenance log PDFs for unstructured data demo
Creates 75 inspection reports linked to existing assets
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  reportlab not installed. Will generate JSON metadata only.")
    print("   To generate actual PDFs, install: pip install reportlab")

# Configuration
OUTPUT_DIR = Path(__file__).parent / "generated_maintenance_logs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load existing assets or generate sample
ASSETS_FILE = Path(__file__).parent / "generated_data" / "asset_master.json"

# Sample asset data if file doesn't exist
SAMPLE_ASSETS = [
    {"ASSET_ID": f"T-SS{i:03d}-001", "ASSET_TYPE": "Power Transformer", "MANUFACTURER": mfg, "MODEL": f"TXP-{cap}MVA",
     "CAPACITY_MVA": cap, "VOLTAGE_RATING_KV": volt, "INSTALLATION_DATE": f"20{10+i%15:02d}-{(i%12)+1:02d}-15",
     "LOCATION_SUBSTATION": f"{city} {['Central', 'North', 'South', 'East', 'West'][i%5]} SS",
     "LOCATION_CITY": city, "LOCATION_COUNTY": county, "CUSTOMERS_AFFECTED": cust, "CRITICALITY_SCORE": crit}
    for i, (mfg, cap, volt, city, county, cust, crit) in enumerate([
        ("ABB", 25, 138, "West Palm Beach", "Palm Beach", 12500, 92),
        ("GE", 30, 138, "Miami", "Miami-Dade", 15000, 88),
        ("Siemens", 25, 138, "Tampa", "Hillsborough", 13000, 85),
        ("ABB", 35, 230, "Fort Lauderdale", "Broward", 18000, 90),
        ("Westinghouse", 25, 138, "Orlando", "Orange", 14000, 87),
        ("GE", 30, 138, "Jacksonville", "Duval", 11000, 83),
        ("Siemens", 35, 230, "Tallahassee", "Leon", 9500, 81),
        ("ABB", 25, 138, "Naples", "Collier", 8000, 79),
        ("GE", 30, 138, "Fort Myers", "Lee", 10500, 82),
        ("Westinghouse", 35, 230, "Sarasota", "Sarasota", 12000, 84),
    ] * 10)  # Repeat to get 100 assets
]

# Maintenance templates and root causes
MAINTENANCE_TYPES = {
    'PREVENTIVE': {
        'weight': 0.45,
        'duration_range': (2, 6),
        'cost_range': (5000, 15000),
        'failure_rate': 0.0
    },
    'CORRECTIVE': {
        'weight': 0.30,
        'duration_range': (4, 12),
        'cost_range': (15000, 45000),
        'failure_rate': 0.2
    },
    'EMERGENCY': {
        'weight': 0.15,
        'duration_range': (6, 24),
        'cost_range': (35000, 120000),
        'failure_rate': 0.85
    },
    'INSPECTION': {
        'weight': 0.10,
        'duration_range': (1, 3),
        'cost_range': (2000, 5000),
        'failure_rate': 0.0
    }
}

ROOT_CAUSES = [
    # Thermal issues
    {"keyword": "Overheating", "indicators": ["elevated oil temperature", "thermal runaway", "hotspot detected"], 
     "severity": "HIGH", "actions": ["Replace cooling system", "Reduce load", "Add ventilation"]},
    {"keyword": "High Oil Temperature", "indicators": ["oil temp above 85°C", "radiator inefficiency"], 
     "severity": "HIGH", "actions": ["Clean radiators", "Check oil level", "Inspect cooling fans"]},
    
    # Insulation issues
    {"keyword": "Insulation Degradation", "indicators": ["low insulation resistance", "moisture ingress", "aging dielectric"], 
     "severity": "CRITICAL", "actions": ["Oil reclamation", "Replace bushings", "Transformer replacement"]},
    {"keyword": "Partial Discharge", "indicators": ["PD activity detected", "corona discharge", "insulation breakdown"], 
     "severity": "CRITICAL", "actions": ["Offline testing", "Bushing replacement", "Emergency repair"]},
    
    # Oil quality issues
    {"keyword": "Oil Contamination", "indicators": ["high moisture content", "acidic oil", "particulate matter"], 
     "severity": "MEDIUM", "actions": ["Oil filtering", "Oil replacement", "Seal repair"]},
    {"keyword": "Dissolved Gas Anomaly", "indicators": ["elevated H2 levels", "high CO/CO2 ratio", "acetylene present"], 
     "severity": "HIGH", "actions": ["DGA analysis", "Load reduction", "Immediate inspection"]},
    
    # Mechanical issues
    {"keyword": "Excessive Vibration", "indicators": ["abnormal vibration levels", "loose components", "bearing wear"], 
     "severity": "MEDIUM", "actions": ["Tighten connections", "Replace bearings", "Balance rotating parts"]},
    {"keyword": "Tank Corrosion", "indicators": ["rust on tank surface", "paint deterioration", "metal thinning"], 
     "severity": "MEDIUM", "actions": ["Sandblast and repaint", "Seal leaks", "Monitor corrosion rate"]},
    
    # Electrical issues
    {"keyword": "Overload Condition", "indicators": ["sustained high load", "exceeding nameplate rating"], 
     "severity": "HIGH", "actions": ["Load redistribution", "Capacity upgrade", "Parallel operation"]},
    {"keyword": "Winding Fault", "indicators": ["turn-to-turn short", "ground fault", "inter-winding short"], 
     "severity": "CRITICAL", "actions": ["Transformer replacement", "Winding repair", "Outage required"]},
    {"keyword": "Bushing Failure", "indicators": ["cracked porcelain", "oil leak at bushing", "flashover marks"], 
     "severity": "HIGH", "actions": ["Bushing replacement", "Emergency shutdown", "Load transfer"]},
    
    # Environmental
    {"keyword": "Weather Damage", "indicators": ["lightning strike", "flood damage", "extreme temperature"], 
     "severity": "MEDIUM", "actions": ["Assess damage", "Dry out equipment", "Replace damaged parts"]},
]

TECHNICIAN_NAMES = [
    "John Martinez", "Sarah Johnson", "Mike Chen", "Lisa Thompson", "David Rodriguez",
    "Emily Davis", "Robert Wilson", "Jennifer Garcia", "Chris Anderson", "Maria Lopez"
]

def generate_inspection_narrative(maintenance_type, root_cause, failure_occurred, asset):
    """Generate realistic technician narrative"""
    
    narratives = {
        'PREVENTIVE': [
            f"Performed routine quarterly inspection of transformer {asset['ASSET_ID']}. Visual inspection showed equipment in satisfactory condition. Oil sample collected for laboratory analysis. All cooling fans operational. Minor paint touch-up applied to tank exterior. No immediate concerns noted.",
            f"Conducted scheduled preventive maintenance on {asset['ASSET_ID']}. Checked all electrical connections, found all secure. Oil level and color satisfactory. Bushings clean with no signs of tracking. Radiators clean and unobstructed. Load tap changer tested - operating normally. Recommended continued monitoring.",
            f"Annual maintenance completed on {asset['ASSET_ID']}. Replaced air filters on cooling system. Cleaned radiator fins. Torque-checked all bolted connections. Oil dielectric test passed. No abnormalities detected. Equipment performing to specification. Next scheduled maintenance in 12 months."
        ],
        'CORRECTIVE': [
            f"Responded to abnormal readings from {asset['ASSET_ID']}. Investigation revealed {root_cause['indicators'][0]}. {root_cause['keyword']} identified as primary issue. Performed {root_cause['actions'][0].lower()}. Equipment returned to normal operation. Recommend follow-up inspection in 30 days to verify stability.",
            f"Corrective action taken on {asset['ASSET_ID']} following operations alert. Found evidence of {root_cause['indicators'][1]}. Root cause analysis indicates {root_cause['keyword'].lower()}. Implemented {root_cause['actions'][1].lower()} as remedial measure. Post-repair testing satisfactory. System restored to service.",
            f"Maintenance crew dispatched to {asset['ASSET_ID']} for reported issue. Discovered {root_cause['indicators'][0]} during inspection. {root_cause['keyword']} confirmed through diagnostic testing. Completed {root_cause['actions'][0].lower()}. Load tests performed successfully. Placed asset back online with continuous monitoring recommended."
        ],
        'EMERGENCY': [
            f"EMERGENCY RESPONSE: {asset['ASSET_ID']} experienced failure at {datetime.now().strftime('%H:%M')}. {root_cause['keyword']} identified as cause. {root_cause['indicators'][0]} was primary factor. Immediate isolation performed. Load transferred to backup transformer. {root_cause['actions'][0]} required. Estimated repair time: 48-72 hours. {asset['CUSTOMERS_AFFECTED']:,} customers temporarily affected.",
            f"Critical failure event on {asset['ASSET_ID']}. Operations detected {root_cause['indicators'][1]}. Emergency shutdown initiated per safety protocol. Assessment revealed {root_cause['keyword'].lower()} caused the outage. Backup power systems activated. {root_cause['actions'][1]} in progress. Coordinating with grid operations for load management. ETA to service restoration: 2-3 days.",
            f"URGENT REPAIR: {asset['ASSET_ID']} tripped offline unexpectedly. Field investigation found {root_cause['indicators'][0]}. {root_cause['keyword']} confirmed as failure mode. Significant damage observed. {root_cause['actions'][0]} underway. Parts ordered for expedited delivery. Customer impact: {asset['CUSTOMERS_AFFECTED']:,} accounts. Working around the clock to restore service."
        ],
        'INSPECTION': [
            f"Routine visual inspection of {asset['ASSET_ID']} completed. All external components appear normal. No oil leaks detected. Paint condition good. Gauge readings within normal limits. No maintenance actions required at this time. Equipment suitable for continued operation. Next inspection scheduled per maintenance calendar.",
            f"Walk-through inspection performed on {asset['ASSET_ID']}. Checked for obvious signs of deterioration or damage. All observed parameters normal. Cooling system functioning properly. No unusual sounds or odors noted. Asset appears to be operating satisfactorily. Documentation updated in asset management system.",
            f"Infrared thermal scan completed on {asset['ASSET_ID']}. No hotspots detected. Temperature distribution uniform across all components. This inspection is part of our predictive maintenance program. Results support continued normal operation. Recommend next thermal survey in 6 months."
        ]
    }
    
    # Select a narrative template
    if failure_occurred and maintenance_type == 'EMERGENCY':
        template = random.choice(narratives['EMERGENCY'])
    else:
        template = random.choice(narratives.get(maintenance_type, narratives['INSPECTION']))
    
    return template

def generate_recommendations(root_cause, severity, maintenance_type):
    """Generate follow-up recommendations"""
    
    base_recs = root_cause['actions'] if maintenance_type != 'INSPECTION' else ["Continue routine monitoring"]
    
    additional_recs = {
        'CRITICAL': ["Immediate review by engineering team", "Daily monitoring until stable", "Prepare backup equipment"],
        'HIGH': ["Increase monitoring frequency", "Schedule follow-up in 2 weeks", "Review similar assets"],
        'MEDIUM': ["Monitor trend over next 30 days", "Include in quarterly review", "Document for analysis"],
        'LOW': ["Continue standard monitoring", "No immediate action required"]
    }
    
    return base_recs + additional_recs.get(severity, additional_recs['MEDIUM'])

def create_pdf_document(doc_metadata, asset, output_path):
    """Generate actual PDF document using reportlab"""
    
    if not PDF_AVAILABLE:
        return None
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=6,
        spaceBefore=12
    )
    
    # Header
    story.append(Paragraph("FLORIDA POWER & LIGHT COMPANY", title_style))
    story.append(Paragraph("Equipment Maintenance Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Document info table
    info_data = [
        ['Document ID:', doc_metadata['DOCUMENT_ID']],
        ['Report Date:', doc_metadata['DOCUMENT_DATE']],
        ['Maintenance Type:', doc_metadata['MAINTENANCE_TYPE']],
        ['Technician:', f"{doc_metadata['TECHNICIAN_NAME']} (ID: {doc_metadata['TECHNICIAN_ID']})"],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Asset Information
    story.append(Paragraph("ASSET INFORMATION", heading_style))
    
    asset_data = [
        ['Asset ID:', asset['ASSET_ID']],
        ['Type:', f"{asset['ASSET_TYPE']} - {asset['CAPACITY_MVA']} MVA, {asset['VOLTAGE_RATING_KV']} kV"],
        ['Manufacturer:', f"{asset['MANUFACTURER']} - Model {asset['MODEL']}"],
        ['Location:', f"{asset['LOCATION_SUBSTATION']}, {asset['LOCATION_CITY']}, {asset['LOCATION_COUNTY']}"],
        ['Installation Date:', asset['INSTALLATION_DATE']],
        ['Customers Affected:', f"{asset['CUSTOMERS_AFFECTED']:,}"],
        ['Criticality Score:', f"{asset['CRITICALITY_SCORE']}/100"],
    ]
    
    asset_table = Table(asset_data, colWidths=[2*inch, 4*inch])
    asset_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
    ]))
    
    story.append(asset_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Maintenance Summary
    story.append(Paragraph("MAINTENANCE SUMMARY", heading_style))
    
    summary_data = [
        ['Duration:', f"{doc_metadata['DURATION_HOURS']:.1f} hours"],
        ['Cost:', f"${doc_metadata['COST_USD']:,.2f}"],
        ['Failure Occurred:', 'YES - Equipment Failure' if doc_metadata['FAILURE_OCCURRED'] else 'NO - Routine Maintenance'],
        ['Severity Level:', doc_metadata['SEVERITY_LEVEL']],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    
    # Build all table styles at once
    summary_styles = [
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
    ]
    
    if doc_metadata['FAILURE_OCCURRED']:
        summary_styles.append(('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#ffcccc')))
    
    summary_table.setStyle(TableStyle(summary_styles))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Technician Narrative
    story.append(Paragraph("TECHNICIAN NARRATIVE", heading_style))
    narrative_para = Paragraph(doc_metadata['DOCUMENT_TEXT'], styles['BodyText'])
    story.append(narrative_para)
    story.append(Spacer(1, 0.2*inch))
    
    # Root Cause Analysis (if applicable)
    if doc_metadata['ROOT_CAUSE_KEYWORDS']:
        story.append(Paragraph("ROOT CAUSE ANALYSIS", heading_style))
        causes_text = "<br/>".join([f"• {cause}" for cause in doc_metadata['ROOT_CAUSE_KEYWORDS']])
        story.append(Paragraph(causes_text, styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("RECOMMENDATIONS & FOLLOW-UP ACTIONS", heading_style))
    recs_text = "<br/>".join([f"• {rec}" for rec in doc_metadata['RECOMMENDED_ACTIONS']])
    story.append(Paragraph(recs_text, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    # Signature section
    story.append(Spacer(1, 0.3*inch))
    sig_data = [
        ['Technician Signature:', '__________________________', 'Date:', '__________'],
        ['Supervisor Approval:', '__________________________', 'Date:', '__________'],
    ]
    
    sig_table = Table(sig_data, colWidths=[1.5*inch, 2.5*inch, 0.75*inch, 1*inch])
    sig_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(sig_table)
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer = Paragraph(
        f"<font size=8>Utility Confidential | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Document ID: {doc_metadata['DOCUMENT_ID']}</font>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    story.append(footer)
    
    # Build PDF
    try:
        doc.build(story)
        return output_path
    except Exception as e:
        print(f"Error creating PDF {output_path}: {e}")
        return None

def generate_maintenance_logs(num_logs=75):
    """Generate maintenance log documents"""
    
    print(f"\n🔧 Generating {num_logs} maintenance log documents...\n")
    
    # Load assets
    if ASSETS_FILE.exists():
        with open(ASSETS_FILE, 'r') as f:
            assets = [json.loads(line) for line in f]
        print(f"✅ Loaded {len(assets)} assets from file")
    else:
        assets = SAMPLE_ASSETS
        print(f"✅ Using {len(assets)} sample assets (asset file not found)")
    
    documents = []
    metadata_list = []
    
    # Generate documents
    for i in range(num_logs):
        # Select random asset
        asset = random.choice(assets)
        
        # Select maintenance type
        maint_type = random.choices(
            list(MAINTENANCE_TYPES.keys()),
            weights=[MAINTENANCE_TYPES[t]['weight'] for t in MAINTENANCE_TYPES.keys()]
        )[0]
        
        # Random date in last 2 years
        days_ago = random.randint(1, 730)
        doc_date = datetime.now() - timedelta(days=days_ago)
        
        # Select root cause
        root_cause = random.choice(ROOT_CAUSES)
        
        # Determine if failure occurred
        failure_occurred = random.random() < MAINTENANCE_TYPES[maint_type]['failure_rate']
        
        # Generate document metadata
        doc_id = f"MAINT-{asset['ASSET_ID']}-{doc_date.strftime('%Y%m%d')}-{i+1:03d}"
        technician = random.choice(TECHNICIAN_NAMES)
        tech_id = f"TECH{random.randint(1000, 9999)}"
        
        duration = random.uniform(*MAINTENANCE_TYPES[maint_type]['duration_range'])
        cost = random.uniform(*MAINTENANCE_TYPES[maint_type]['cost_range'])
        
        # Generate narrative
        narrative = generate_inspection_narrative(maint_type, root_cause, failure_occurred, asset)
        
        # Generate recommendations
        recommendations = generate_recommendations(
            root_cause, 
            root_cause['severity'] if failure_occurred or maint_type == 'CORRECTIVE' else 'LOW',
            maint_type
        )
        
        # Create metadata dictionary
        doc_metadata = {
            'DOCUMENT_ID': doc_id,
            'ASSET_ID': asset['ASSET_ID'],
            'DOCUMENT_TYPE': 'INSPECTION_REPORT',
            'DOCUMENT_DATE': doc_date.strftime('%Y-%m-%d'),
            'TECHNICIAN_NAME': technician,
            'TECHNICIAN_ID': tech_id,
            'MAINTENANCE_TYPE': maint_type,
            'DURATION_HOURS': round(duration, 2),
            'COST_USD': round(cost, 2),
            'FAILURE_OCCURRED': failure_occurred,
            'DOCUMENT_TEXT': narrative,
            'ROOT_CAUSE_KEYWORDS': [root_cause['keyword']] + root_cause['indicators'][:2] if (failure_occurred or maint_type == 'CORRECTIVE') else [],
            'SEVERITY_LEVEL': root_cause['severity'] if (failure_occurred or maint_type == 'CORRECTIVE') else 'LOW',
            'RECOMMENDED_ACTIONS': recommendations,
            'PARTS_MENTIONED': []  # Could extract from narrative
        }
        
        # Create PDF
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = OUTPUT_DIR / pdf_filename
        
        if PDF_AVAILABLE:
            result = create_pdf_document(doc_metadata, asset, pdf_path)
            if result:
                doc_metadata['FILE_PATH'] = f"@MAINTENANCE_DOCS_STAGE/{pdf_filename}"
                doc_metadata['FILE_SIZE_BYTES'] = pdf_path.stat().st_size
                doc_metadata['FILE_FORMAT'] = 'PDF'
                print(f"✅ [{i+1}/{num_logs}] Created: {pdf_filename}")
            else:
                print(f"⚠️  [{i+1}/{num_logs}] Failed to create PDF: {pdf_filename}")
        else:
            doc_metadata['FILE_PATH'] = f"@MAINTENANCE_DOCS_STAGE/{pdf_filename}"
            doc_metadata['FILE_SIZE_BYTES'] = 0
            doc_metadata['FILE_FORMAT'] = 'PDF'
            print(f"📝 [{i+1}/{num_logs}] Metadata: {pdf_filename}")
        
        metadata_list.append(doc_metadata)
    
    # Save metadata to JSON
    metadata_file = OUTPUT_DIR / "maintenance_logs_metadata.json"
    with open(metadata_file, 'w') as f:
        for doc in metadata_list:
            f.write(json.dumps(doc) + '\n')
    
    print(f"\n✅ Generated {len(metadata_list)} maintenance log documents")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📄 Metadata file: {metadata_file}")
    
    if PDF_AVAILABLE:
        total_size = sum(p.stat().st_size for p in OUTPUT_DIR.glob("*.pdf") if p.is_file())
        print(f"💾 Total PDF size: {total_size / 1024 / 1024:.2f} MB")
    
    # Generate summary statistics
    print("\n📊 Document Statistics:")
    print(f"   Preventive:  {sum(1 for d in metadata_list if d['MAINTENANCE_TYPE'] == 'PREVENTIVE'):3d}")
    print(f"   Corrective:  {sum(1 for d in metadata_list if d['MAINTENANCE_TYPE'] == 'CORRECTIVE'):3d}")
    print(f"   Emergency:   {sum(1 for d in metadata_list if d['MAINTENANCE_TYPE'] == 'EMERGENCY'):3d}")
    print(f"   Inspection:  {sum(1 for d in metadata_list if d['MAINTENANCE_TYPE'] == 'INSPECTION'):3d}")
    print(f"   With Failures: {sum(1 for d in metadata_list if d['FAILURE_OCCURRED']):3d}")
    
    return metadata_list

if __name__ == "__main__":
    generate_maintenance_logs(75)

