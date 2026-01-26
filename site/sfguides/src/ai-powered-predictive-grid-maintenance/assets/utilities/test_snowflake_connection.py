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
Test Snowflake connection and validate deployment

This script tests the Snowflake connection and verifies that the
Grid Reliability platform is properly deployed.
"""

import snowflake.connector
import os
from pathlib import Path

def test_connection():
    """Test basic Snowflake connection"""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse='GRID_RELIABILITY_WH',
            database='UTILITIES_GRID_RELIABILITY',
            schema='RAW'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"Database: {result[0]}")
        print(f"Schema: {result[1]}")
        print(f"Warehouse: {result[2]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def validate_deployment():
    """Validate that all objects are deployed"""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse='GRID_RELIABILITY_WH',
            database='UTILITIES_GRID_RELIABILITY'
        )
        
        cursor = conn.cursor()
        
        # Check schemas
        cursor.execute("SHOW SCHEMAS IN DATABASE UTILITIES_GRID_RELIABILITY")
        schemas = [row[1] for row in cursor.fetchall()]
        print(f"\n✅ Schemas: {len(schemas)} found")
        print(f"   {', '.join(schemas)}")
        
        # Check tables
        tables_to_check = [
            ('RAW', 'ASSET_MASTER'),
            ('RAW', 'SENSOR_READINGS'),
            ('RAW', 'MAINTENANCE_HISTORY'),
            ('ML', 'MODEL_PREDICTIONS'),
            ('UNSTRUCTURED', 'MAINTENANCE_LOG_DOCUMENTS'),
            ('UNSTRUCTURED', 'TECHNICAL_MANUALS')
        ]
        
        print("\n📊 Table Row Counts:")
        for schema, table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                count = cursor.fetchone()[0]
                print(f"   {schema}.{table}: {count:,} rows")
            except Exception as e:
                print(f"   {schema}.{table}: ❌ Not found or error")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Grid Reliability - Snowflake Connection Test")
    print("=" * 60)
    
    if test_connection():
        validate_deployment()
    
    print("\n" + "=" * 60)

