#!/usr/bin/env python3
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
Load ALL generated unstructured data into Snowflake
Reads JSON metadata files and creates complete INSERT statements
"""

import json
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
MAINT_LOGS_FILE = BASE_DIR / "generated_maintenance_logs" / "maintenance_logs_metadata.json"
TECH_MANUALS_FILE = BASE_DIR / "generated_technical_manuals" / "technical_manuals_metadata.json"
VISUAL_INSP_FILE = BASE_DIR / "generated_visual_inspections" / "visual_inspections_metadata.json"
CV_DETECTIONS_FILE = BASE_DIR / "generated_visual_inspections" / "cv_detections.json"

OUTPUT_SQL = BASE_DIR / "load_unstructured_data_full.sql"

def escape_sql_string(s):
    """Escape single quotes and backslashes for SQL"""
    if s is None:
        return 'NULL'
    # Convert to string, escape backslashes first, then single quotes
    s_str = str(s).replace("\\", "\\\\").replace("'", "''")
    # Remove any problematic characters
    s_str = s_str.replace("\x00", "")
    return f"'{s_str}'"

def format_array(arr):
    """Format Python list as JSON array for PARSE_JSON"""
    if not arr:
        return "PARSE_JSON('[]')"
    # Escape for JSON
    json_str = json.dumps(arr).replace("'", "''")
    return f"PARSE_JSON('{json_str}')"

def chunk_list(lst, chunk_size=50):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def main():
    print("=" * 80)
    print("LOADING ALL GENERATED UNSTRUCTURED DATA")
    print("=" * 80)
    
    sql_statements = []
    
    sql_statements.append("""-- ============================================================================
-- LOAD ALL UNSTRUCTURED DATA FROM PYTHON GENERATORS
-- Generated from JSON metadata files
-- ============================================================================

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA UNSTRUCTURED;

""")
    
    # =========================================================================
    # 1. Load Maintenance Log Documents
    # =========================================================================
    if MAINT_LOGS_FILE.exists():
        print(f"\n📄 Processing: {MAINT_LOGS_FILE.name}")
        maint_logs = []
        with open(MAINT_LOGS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    maint_logs.append(json.loads(line))
        
        print(f"   Found {len(maint_logs)} maintenance log records")
        
        # Split into chunks to avoid SQL statement size limits
        for chunk_idx, chunk in enumerate(chunk_list(maint_logs, 50)):
            sql_statements.append(f"\n-- Maintenance Logs Batch {chunk_idx + 1}\n")
            sql_statements.append("INSERT INTO MAINTENANCE_LOG_DOCUMENTS (\n")
            sql_statements.append("    DOCUMENT_ID, ASSET_ID, DOCUMENT_DATE, TECHNICIAN_NAME, MAINTENANCE_TYPE,\n")
            sql_statements.append("    SEVERITY_LEVEL, SUMMARY, ROOT_CAUSE_KEYWORDS, RECOMMENDED_ACTIONS,\n")
            sql_statements.append("    DOCUMENT_TEXT, FILE_PATH, FAILURE_OCCURRED\n")
            sql_statements.append(")\n")
            
            selects = []
            for log in chunk:
                doc_id = log['DOCUMENT_ID']
                asset_id = log['ASSET_ID']
                doc_date = log['DOCUMENT_DATE']
                tech = log['TECHNICIAN_NAME']
                maint_type = log['MAINTENANCE_TYPE']
                severity = log['SEVERITY_LEVEL']
                summary = log.get('DOCUMENT_TEXT', '')[:500]  # Use first 500 chars as summary
                keywords_json = json.dumps(log.get('ROOT_CAUSE_KEYWORDS', [])).replace("'", "''")
                actions_json = json.dumps(log.get('RECOMMENDED_ACTIONS', [])).replace("'", "''")
                doc_text = log['DOCUMENT_TEXT']
                file_path = log['FILE_PATH']
                failure = 'TRUE' if log.get('FAILURE_OCCURRED', False) else 'FALSE'
                
                sel = f"SELECT {escape_sql_string(doc_id)}, {escape_sql_string(asset_id)}, '{doc_date}', " \
                      f"{escape_sql_string(tech)}, {escape_sql_string(maint_type)}, " \
                      f"{escape_sql_string(severity)}, {escape_sql_string(summary)}, " \
                      f"PARSE_JSON('{keywords_json}'), PARSE_JSON('{actions_json}'), " \
                      f"{escape_sql_string(doc_text)}, {escape_sql_string(file_path)}, {failure}"
                selects.append(sel)
            
            sql_statements.append("\nUNION ALL\n".join(selects))
            sql_statements.append(";\n")
        
        sql_statements.append(f"\nSELECT 'Loaded ' || COUNT(*) || ' maintenance log documents' AS STATUS FROM MAINTENANCE_LOG_DOCUMENTS;\n")
        print(f"   ✓ Prepared {len(maint_logs)} maintenance log records")
    
    # =========================================================================
    # 2. Load Technical Manuals
    # =========================================================================
    if TECH_MANUALS_FILE.exists():
        print(f"\n📄 Processing: {TECH_MANUALS_FILE.name}")
        tech_manuals = []
        with open(TECH_MANUALS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tech_manuals.append(json.loads(line))
        
        print(f"   Found {len(tech_manuals)} technical manual records")
        
        sql_statements.append("\n-- Load Technical Manuals\n")
        sql_statements.append("INSERT INTO TECHNICAL_MANUALS (\n")
        sql_statements.append("    MANUAL_ID, MANUAL_TYPE, EQUIPMENT_TYPE, MANUFACTURER, MODEL,\n")
        sql_statements.append("    VERSION, PUBLICATION_DATE, FILE_PATH, DOCUMENT_TEXT\n")
        sql_statements.append(")\n")
        
        selects = []
        for manual in tech_manuals:
            manual_id = manual['MANUAL_ID']
            manual_type = manual['MANUAL_TYPE']
            equip_type = manual['EQUIPMENT_TYPE']
            manufacturer = manual['MANUFACTURER']
            model = manual['MODEL']
            version = manual.get('VERSION', '1.0')
            pub_date = manual['PUBLICATION_DATE']
            file_path = manual['FILE_PATH']
            
            # Generate document text from manual metadata
            doc_text = f"{manufacturer} {model} - {manual_type}\n\n" \
                      f"Equipment Type: {equip_type}\n" \
                      f"Version: {version}\n" \
                      f"Publication Date: {pub_date}\n\n" \
                      f"This technical manual provides comprehensive information for {equip_type.lower()} " \
                      f"equipment manufactured by {manufacturer}, model {model}."
            
            sel = f"SELECT {escape_sql_string(manual_id)}, {escape_sql_string(manual_type)}, " \
                  f"{escape_sql_string(equip_type)}, {escape_sql_string(manufacturer)}, " \
                  f"{escape_sql_string(model)}, {escape_sql_string(version)}, " \
                  f"'{pub_date}', {escape_sql_string(file_path)}, {escape_sql_string(doc_text)}"
            selects.append(sel)
        
        sql_statements.append("\nUNION ALL\n".join(selects))
        sql_statements.append(";\n")
        sql_statements.append(f"\nSELECT 'Loaded ' || COUNT(*) || ' technical manuals' AS STATUS FROM TECHNICAL_MANUALS;\n")
        print(f"   ✓ Prepared {len(selects)} technical manual records")
    
    # =========================================================================
    # 3. Load Visual Inspections
    # =========================================================================
    if VISUAL_INSP_FILE.exists():
        print(f"\n📄 Processing: {VISUAL_INSP_FILE.name}")
        inspections = []
        with open(VISUAL_INSP_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    inspections.append(json.loads(line))
        
        print(f"   Found {len(inspections)} visual inspection records")
        
        # Split into chunks
        for chunk_idx, chunk in enumerate(chunk_list(inspections, 50)):
            sql_statements.append(f"\n-- Visual Inspections Batch {chunk_idx + 1}\n")
            sql_statements.append("INSERT INTO VISUAL_INSPECTIONS (\n")
            sql_statements.append("    INSPECTION_ID, ASSET_ID, INSPECTION_DATE, INSPECTOR_NAME, INSPECTOR_ID,\n")
            sql_statements.append("    INSPECTION_METHOD, WEATHER_CONDITIONS, FILE_PATH, FILE_TYPE,\n")
            sql_statements.append("    FILE_SIZE_BYTES, RESOLUTION, GPS_LATITUDE, GPS_LONGITUDE, CV_PROCESSED\n")
            sql_statements.append(")\n")
            
            selects = []
            for insp in chunk:
                insp_id = insp['INSPECTION_ID']
                asset_id = insp['ASSET_ID']
                insp_date = insp['INSPECTION_DATE']
                inspector = insp['INSPECTOR_NAME']
                inspector_id = insp.get('INSPECTOR_ID', 'INSP001')
                method = insp.get('INSPECTION_METHOD', 'DRONE')
                weather = insp.get('WEATHER_CONDITIONS', 'Clear, sunny')
                file_path = insp['FILE_PATH']
                file_type = insp.get('FILE_TYPE', 'MP4')
                file_size = insp.get('FILE_SIZE_BYTES', 0)
                resolution = insp.get('RESOLUTION', '1920x1080')
                lat = insp.get('GPS_LATITUDE', 'NULL')
                lon = insp.get('GPS_LONGITUDE', 'NULL')
                cv_processed = 'TRUE' if insp.get('CV_PROCESSED', False) else 'FALSE'
                
                lat_str = str(lat) if lat != 'NULL' else 'NULL'
                lon_str = str(lon) if lon != 'NULL' else 'NULL'
                
                sel = f"SELECT {escape_sql_string(insp_id)}, {escape_sql_string(asset_id)}, " \
                      f"'{insp_date}', {escape_sql_string(inspector)}, {escape_sql_string(inspector_id)}, " \
                      f"{escape_sql_string(method)}, {escape_sql_string(weather)}, " \
                      f"{escape_sql_string(file_path)}, {escape_sql_string(file_type)}, " \
                      f"{file_size}, {escape_sql_string(resolution)}, {lat_str}, {lon_str}, {cv_processed}"
                selects.append(sel)
            
            sql_statements.append("\nUNION ALL\n".join(selects))
            sql_statements.append(";\n")
        
        sql_statements.append(f"\nSELECT 'Loaded ' || COUNT(*) || ' visual inspections' AS STATUS FROM VISUAL_INSPECTIONS;\n")
        print(f"   ✓ Prepared {len(inspections)} visual inspection records")
    
    # =========================================================================
    # 4. Load CV Detections
    # =========================================================================
    if CV_DETECTIONS_FILE.exists():
        print(f"\n📄 Processing: {CV_DETECTIONS_FILE.name}")
        detections = []
        with open(CV_DETECTIONS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    detections.append(json.loads(line))
        
        print(f"   Found {len(detections)} CV detection records")
        
        # Split into chunks
        for chunk_idx, chunk in enumerate(chunk_list(detections, 50)):
            sql_statements.append(f"\n-- CV Detections Batch {chunk_idx + 1}\n")
            sql_statements.append("INSERT INTO CV_DETECTIONS (\n")
            sql_statements.append("    DETECTION_ID, INSPECTION_ID, ASSET_ID, DETECTION_TYPE, CONFIDENCE_SCORE,\n")
            sql_statements.append("    BOUNDING_BOX, SEVERITY_LEVEL, REQUIRES_IMMEDIATE_ACTION, DETECTED_AT_COMPONENT,\n")
            sql_statements.append("    DESCRIPTION, MODEL_NAME, MODEL_VERSION\n")
            sql_statements.append(")\n")
            
            selects = []
            for det in chunk:
                det_id = det['DETECTION_ID']
                insp_id = det['INSPECTION_ID']
                asset_id = det['ASSET_ID']
                det_type = det['DETECTION_TYPE']
                conf = det['CONFIDENCE_SCORE']
                bbox = json.dumps(det.get('BOUNDING_BOX', {})).replace("'", "''")
                severity = det['SEVERITY_LEVEL']
                requires_action = 'TRUE' if det.get('REQUIRES_IMMEDIATE_ACTION', False) else 'FALSE'
                component = det.get('DETECTED_AT_COMPONENT', 'UNKNOWN')
                desc = det['DESCRIPTION']
                model_name = det.get('MODEL_NAME', 'yolov8_transformer_v3')
                model_version = det.get('MODEL_VERSION', 'v2.1')
                
                sel = f"SELECT {escape_sql_string(det_id)}, {escape_sql_string(insp_id)}, " \
                      f"{escape_sql_string(asset_id)}, {escape_sql_string(det_type)}, " \
                      f"{conf}, PARSE_JSON('{bbox}'), {escape_sql_string(severity)}, " \
                      f"{requires_action}, {escape_sql_string(component)}, {escape_sql_string(desc)}, " \
                      f"{escape_sql_string(model_name)}, {escape_sql_string(model_version)}"
                selects.append(sel)
            
            sql_statements.append("\nUNION ALL\n".join(selects))
            sql_statements.append(";\n")
        
        sql_statements.append(f"\nSELECT 'Loaded ' || COUNT(*) || ' CV detections' AS STATUS FROM CV_DETECTIONS;\n")
        print(f"   ✓ Prepared {len(detections)} CV detection records")
    
    # =========================================================================
    # 5. Verification
    # =========================================================================
    sql_statements.append("""
-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 
    'MAINTENANCE_LOG_DOCUMENTS' AS TABLE_NAME, 
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT ASSET_ID) AS UNIQUE_ASSETS
FROM MAINTENANCE_LOG_DOCUMENTS
UNION ALL
SELECT 'TECHNICAL_MANUALS', COUNT(*), COUNT(DISTINCT MANUFACTURER) FROM TECHNICAL_MANUALS
UNION ALL
SELECT 'VISUAL_INSPECTIONS', COUNT(*), COUNT(DISTINCT ASSET_ID) FROM VISUAL_INSPECTIONS
UNION ALL
SELECT 'CV_DETECTIONS', COUNT(*), COUNT(DISTINCT ASSET_ID) FROM CV_DETECTIONS
ORDER BY TABLE_NAME;

SELECT '✅ ALL UNSTRUCTURED DATA LOADED SUCCESSFULLY!' AS STATUS;
""")
    
    # Write to file
    print(f"\n{'=' * 80}")
    print("GENERATING SQL FILE...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write(''.join(sql_statements))
    
    file_size_mb = OUTPUT_SQL.stat().st_size / (1024 * 1024)
    print(f"✅ Generated SQL script: {OUTPUT_SQL}")
    print(f"📊 File size: {file_size_mb:.2f} MB")
    print(f"\n{'=' * 80}")
    print("NEXT STEP:")
    print(f"  snow sql -c USWEST_DEMOACCOUNT -f {OUTPUT_SQL.name}")
    print(f"{'=' * 80}\n")
    
if __name__ == "__main__":
    main()

