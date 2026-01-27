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
Generate visual inspection metadata and simulated computer vision outputs

NOTE: This generates the DATA FRAMEWORK for visual inspections.
Real implementation would integrate with:
- Drone inspection footage
- Handheld camera photos
- Thermal imaging cameras
- LiDAR scanners
- Computer vision models (YOLOv8, etc.)

For demo purposes, this generates realistic CV output data.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
OUTPUT_DIR = Path(__file__).parent / "generated_visual_inspections"
OUTPUT_DIR.mkdir(exist_ok=True)

# Sample assets (same as maintenance logs)
SAMPLE_ASSETS = [
    {"ASSET_ID": f"T-SS{i:03d}-001", "ASSET_TYPE": "Power Transformer", "MANUFACTURER": mfg,
     "LOCATION_SUBSTATION": f"{city} {['Central', 'North', 'South', 'East', 'West'][i%5]} SS",
     "LOCATION_CITY": city, "LOCATION_COUNTY": county, "LAT": lat, "LON": lon}
    for i, (mfg, city, county, lat, lon) in enumerate([
        ("ABB", "West Palm Beach", "Palm Beach", 26.7153, -80.0534),
        ("GE", "Miami", "Miami-Dade", 25.7617, -80.1918),
        ("Siemens", "Tampa", "Hillsborough", 27.9506, -82.4572),
        ("ABB", "Fort Lauderdale", "Broward", 26.1224, -80.1373),
        ("Westinghouse", "Orlando", "Orange", 28.5383, -81.3792),
        ("GE", "Jacksonville", "Duval", 30.3322, -81.6557),
        ("Siemens", "Tallahassee", "Leon", 30.4383, -84.2807),
        ("ABB", "Naples", "Collier", 26.1420, -81.7948),
        ("GE", "Fort Myers", "Lee", 26.6406, -81.8723),
        ("Westinghouse", "Sarasota", "Sarasota", 27.3364, -82.5307),
    ] * 10)  # 100 assets
]

# Inspection methods
INSPECTION_METHODS = [
    'DRONE', 'HANDHELD_CAMERA', 'THERMAL', 'LIDAR', 'VIDEO'
]

# Computer Vision detection types
CV_DETECTION_TYPES = {
    'CORROSION': {
        'severity_weights': {'CRITICAL': 0.1, 'HIGH': 0.2, 'MEDIUM': 0.4, 'LOW': 0.3},
        'components': ['TANK', 'RADIATOR', 'BUSHING_BASE', 'MOUNTING_BRACKETS'],
        'confidence_range': (0.75, 0.95),
        'immediate_action_prob': 0.15,
    },
    'CRACK': {
        'severity_weights': {'CRITICAL': 0.3, 'HIGH': 0.3, 'MEDIUM': 0.3, 'LOW': 0.1},
        'components': ['BUSHING', 'INSULATOR', 'TANK', 'GASKET'],
        'confidence_range': (0.80, 0.98),
        'immediate_action_prob': 0.45,
    },
    'LEAK': {
        'severity_weights': {'CRITICAL': 0.25, 'HIGH': 0.35, 'MEDIUM': 0.25, 'LOW': 0.15},
        'components': ['GASKET', 'VALVE', 'BUSHING_SEAL', 'RADIATOR_JOINT'],
        'confidence_range': (0.85, 0.99),
        'immediate_action_prob': 0.40,
    },
    'VEGETATION': {
        'severity_weights': {'CRITICAL': 0.05, 'HIGH': 0.15, 'MEDIUM': 0.40, 'LOW': 0.40},
        'components': ['CLEARANCE_ZONE', 'BASE', 'FENCE_LINE', 'ACCESS_ROAD'],
        'confidence_range': (0.90, 0.99),
        'immediate_action_prob': 0.08,
    },
    'HOTSPOT': {
        'severity_weights': {'CRITICAL': 0.35, 'HIGH': 0.40, 'MEDIUM': 0.20, 'LOW': 0.05},
        'components': ['BUSHING_CONNECTION', 'TAP_CHANGER', 'RADIATOR', 'LOAD_CONNECTION'],
        'confidence_range': (0.88, 0.98),
        'immediate_action_prob': 0.50,
    },
    'STRUCTURAL_DAMAGE': {
        'severity_weights': {'CRITICAL': 0.20, 'HIGH': 0.30, 'MEDIUM': 0.30, 'LOW': 0.20},
        'components': ['MOUNTING', 'FOUNDATION', 'SUPPORT_STRUCTURE', 'ENCLOSURE'],
        'confidence_range': (0.78, 0.96),
        'immediate_action_prob': 0.35,
    },
}

# Inspectors
INSPECTORS = [
    ("Carlos Martinez", "INSP1001"),
    ("Sarah Kim", "INSP1002"),
    ("Robert Johnson", "INSP1003"),
    ("Jennifer Lee", "INSP1004"),
    ("Michael Chen", "INSP1005"),
]

# Weather conditions
WEATHER_CONDITIONS = [
    "Clear, sunny",
    "Partly cloudy",
    "Overcast",
    "Light rain",
    "Post-storm",
    "Foggy",
]

def generate_bounding_box():
    """Generate random bounding box coordinates (normalized 0-1)"""
    x = random.uniform(0.1, 0.7)
    y = random.uniform(0.1, 0.7)
    w = random.uniform(0.05, 0.3)
    h = random.uniform(0.05, 0.3)
    return {
        "x": round(x, 4),
        "y": round(y, 4),
        "width": round(w, 4),
        "height": round(h, 4)
    }

def generate_cv_detections(inspection_id, asset_id, inspection_method, num_detections):
    """Generate simulated computer vision detections for an inspection"""
    
    detections = []
    
    # Thermal inspections primarily detect hotspots
    if inspection_method == 'THERMAL':
        detection_types = ['HOTSPOT'] * 3 + list(CV_DETECTION_TYPES.keys())
    # Drone inspections good for vegetation and structural issues
    elif inspection_method == 'DRONE':
        detection_types = ['VEGETATION', 'STRUCTURAL_DAMAGE', 'CORROSION'] * 2 + list(CV_DETECTION_TYPES.keys())
    # LiDAR for structural analysis
    elif inspection_method == 'LIDAR':
        detection_types = ['STRUCTURAL_DAMAGE', 'CRACK'] * 2 + list(CV_DETECTION_TYPES.keys())
    else:
        detection_types = list(CV_DETECTION_TYPES.keys())
    
    for i in range(num_detections):
        detection_type = random.choice(detection_types)
        spec = CV_DETECTION_TYPES[detection_type]
        
        # Determine severity
        severity = random.choices(
            list(spec['severity_weights'].keys()),
            weights=list(spec['severity_weights'].values())
        )[0]
        
        # Determine if immediate action required
        immediate_action = random.random() < spec['immediate_action_prob'] and severity in ['CRITICAL', 'HIGH']
        
        # Generate confidence score
        confidence = random.uniform(*spec['confidence_range'])
        
        # Select component
        component = random.choice(spec['components'])
        
        # Generate description
        descriptions = {
            'CORROSION': [
                f"Surface corrosion detected on {component.lower().replace('_', ' ')}. Rust visible with paint degradation.",
                f"Moderate to severe corrosion present. Metal oxidation advancing on {component.lower().replace('_', ' ')}.",
                f"Corrosion patterns suggest moisture ingress. Located on {component.lower().replace('_', ' ')}.",
            ],
            'CRACK': [
                f"Linear crack detected in {component.lower().replace('_', ' ')}. Length approximately 15-25cm.",
                f"Multiple hairline cracks visible on {component.lower().replace('_', ' ')} surface.",
                f"Structural crack identified. Propagation risk on {component.lower().replace('_', ' ')}.",
            ],
            'LEAK': [
                f"Active oil leak detected at {component.lower().replace('_', ' ')}. Visible staining and dripping.",
                f"Evidence of historical leakage on {component.lower().replace('_', ' ')}. Surface contamination present.",
                f"Seal failure on {component.lower().replace('_', ' ')} allowing fluid escape.",
            ],
            'VEGETATION': [
                f"Tree branches encroaching within clearance zone near {component.lower().replace('_', ' ')}.",
                f"Excessive vegetation growth detected. Clearance violation at {component.lower().replace('_', ' ')}.",
                f"Grass and brush overgrowth affecting access to {component.lower().replace('_', ' ')}.",
            ],
            'HOTSPOT': [
                f"Thermal anomaly detected at {component.lower().replace('_', ' ')}. Temperature differential: {random.randint(15, 40)}°C above ambient.",
                f"Elevated temperature on {component.lower().replace('_', ' ')}. Possible loose connection or high resistance.",
                f"Hot spot identified via infrared scan. {component.lower().replace('_', ' ')} operating {random.randint(20, 50)}°C above normal.",
            ],
            'STRUCTURAL_DAMAGE': [
                f"Physical damage observed on {component.lower().replace('_', ' ')}. Deformation or breakage present.",
                f"Structural integrity compromised at {component.lower().replace('_', ' ')}. Requires engineering assessment.",
                f"Deterioration of {component.lower().replace('_', ' ')} support structure. Potential stability concern.",
            ],
        }
        
        description = random.choice(descriptions[detection_type])
        
        # Model names based on detection type
        model_names = {
            'THERMAL': 'thermal_anomaly_detector_v2',
            'DRONE': 'yolov8_transformer_aerial_v3',
            'LIDAR': 'pointcloud_structural_analyzer_v1',
            'HANDHELD_CAMERA': 'yolov8_transformer_v2',
            'VIDEO': 'temporal_defect_detector_v1',
        }
        
        detection = {
            'DETECTION_ID': f"DET-{inspection_id}-{i+1:03d}",
            'INSPECTION_ID': inspection_id,
            'ASSET_ID': asset_id,
            'DETECTION_TYPE': detection_type,
            'CONFIDENCE_SCORE': round(confidence, 4),
            'BOUNDING_BOX': generate_bounding_box(),
            'SEVERITY_LEVEL': severity,
            'REQUIRES_IMMEDIATE_ACTION': immediate_action,
            'DETECTED_AT_COMPONENT': component,
            'DESCRIPTION': description,
            'MODEL_NAME': model_names.get(inspection_method, 'yolov8_transformer_v2'),
            'MODEL_VERSION': 'v2.1',
            'DETECTION_TIMESTAMP': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        detections.append(detection)
    
    return detections

def generate_visual_inspections(num_inspections=150):
    """Generate visual inspection metadata and CV detections"""
    
    print(f"\n📸 Generating {num_inspections} visual inspection records...\n")
    
    inspections_list = []
    all_detections = []
    
    for i in range(num_inspections):
        # Select random asset
        asset = random.choice(SAMPLE_ASSETS)
        
        # Random date in last 1 year
        days_ago = random.randint(1, 365)
        inspection_date = datetime.now() - timedelta(days=days_ago)
        
        # Select inspector and method
        inspector_name, inspector_id = random.choice(INSPECTORS)
        inspection_method = random.choice(INSPECTION_METHODS)
        
        # Generate inspection ID
        inspection_id = f"VIS-{asset['ASSET_ID']}-{inspection_date.strftime('%Y%m%d')}-{i+1:03d}"
        
        # Determine number of detections (0-5, weighted toward 1-2)
        num_detections = random.choices([0, 1, 2, 3, 4, 5], weights=[0.15, 0.30, 0.25, 0.15, 0.10, 0.05])[0]
        
        # File metadata (simulated)
        file_types = {
            'DRONE': 'MP4',
            'HANDHELD_CAMERA': 'JPG',
            'THERMAL': 'TIFF',
            'LIDAR': 'LAS',
            'VIDEO': 'MP4'
        }
        
        file_type = file_types[inspection_method]
        file_size = random.randint(5, 500) * 1024 * 1024  # 5-500 MB
        
        # Resolution
        resolutions = {
            'DRONE': '4K',
            'HANDHELD_CAMERA': '1920x1080',
            'THERMAL': '640x480',
            'LIDAR': 'N/A',
            'VIDEO': '1920x1080'
        }
        
        inspection_metadata = {
            'INSPECTION_ID': inspection_id,
            'ASSET_ID': asset['ASSET_ID'],
            'INSPECTION_DATE': inspection_date.strftime('%Y-%m-%d'),
            'INSPECTOR_NAME': inspector_name,
            'INSPECTOR_ID': inspector_id,
            'INSPECTION_METHOD': inspection_method,
            'WEATHER_CONDITIONS': random.choice(WEATHER_CONDITIONS),
            'FILE_PATH': f"@VISUAL_INSPECTION_STAGE/{asset['ASSET_ID']}/{inspection_date.strftime('%Y%m')}/{inspection_id}.{file_type.lower()}",
            'FILE_TYPE': file_type,
            'FILE_SIZE_BYTES': file_size,
            'RESOLUTION': resolutions[inspection_method],
            'GPS_LATITUDE': asset['LAT'] + random.uniform(-0.001, 0.001),
            'GPS_LONGITUDE': asset['LON'] + random.uniform(-0.001, 0.001),
            'CV_PROCESSED': True if num_detections > 0 else False,
            'CV_PROCESSING_TIMESTAMP': (inspection_date + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S'),
            'UPLOAD_TIMESTAMP': (inspection_date + timedelta(minutes=random.randint(5, 120))).strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        inspections_list.append(inspection_metadata)
        
        # Generate CV detections
        if num_detections > 0:
            detections = generate_cv_detections(inspection_id, asset['ASSET_ID'], inspection_method, num_detections)
            all_detections.extend(detections)
        
        if (i + 1) % 25 == 0:
            print(f"✅ Generated {i+1}/{num_inspections} inspections...")
    
    # Save inspections metadata
    inspections_file = OUTPUT_DIR / "visual_inspections_metadata.json"
    with open(inspections_file, 'w') as f:
        for inspection in inspections_list:
            f.write(json.dumps(inspection) + '\n')
    
    # Save CV detections
    detections_file = OUTPUT_DIR / "cv_detections.json"
    with open(detections_file, 'w') as f:
        for detection in all_detections:
            f.write(json.dumps(detection) + '\n')
    
    print(f"\n✅ Generated {len(inspections_list)} visual inspections")
    print(f"✅ Generated {len(all_detections)} CV detections")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📄 Inspections file: {inspections_file}")
    print(f"📄 Detections file: {detections_file}")
    
    # Statistics
    print("\n📊 Inspection Statistics:")
    for method in INSPECTION_METHODS:
        count = sum(1 for i in inspections_list if i['INSPECTION_METHOD'] == method)
        print(f"   {method:20s}: {count:3d}")
    
    print("\n📊 Detection Statistics:")
    total_critical = sum(1 for d in all_detections if d['SEVERITY_LEVEL'] == 'CRITICAL')
    total_high = sum(1 for d in all_detections if d['SEVERITY_LEVEL'] == 'HIGH')
    total_immediate = sum(1 for d in all_detections if d['REQUIRES_IMMEDIATE_ACTION'])
    
    print(f"   Total Detections:         {len(all_detections)}")
    print(f"   Critical Severity:        {total_critical}")
    print(f"   High Severity:            {total_high}")
    print(f"   Requires Immediate Action: {total_immediate}")
    
    print("\n📊 Detection Types:")
    for dtype in CV_DETECTION_TYPES.keys():
        count = sum(1 for d in all_detections if d['DETECTION_TYPE'] == dtype)
        print(f"   {dtype:20s}: {count:3d}")
    
    print("\n💡 INTEGRATION NOTES:")
    print("   ✓ Schema created for visual inspection metadata")
    print("   ✓ Schema created for CV detection results")
    print("   ✓ Simulated data demonstrates CV output structure")
    print("   ✓ Ready for real image/video integration")
    print("   ✓ Compatible with YOLOv8, thermal cameras, LiDAR scanners")
    print("\n   To integrate real images:")
    print("   1. Upload images/videos to @VISUAL_INSPECTION_STAGE")
    print("   2. Run CV models (YOLOv8, thermal analysis, etc.)")
    print("   3. Insert detection results into CV_DETECTIONS table")
    print("   4. ML pipeline automatically incorporates visual features")
    
    return inspections_list, all_detections

if __name__ == "__main__":
    generate_visual_inspections(150)

