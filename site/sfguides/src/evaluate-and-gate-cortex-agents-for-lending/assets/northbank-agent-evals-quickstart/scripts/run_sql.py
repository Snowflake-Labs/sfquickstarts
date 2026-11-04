#!/usr/bin/env python3
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run the quickstart SQL scripts against a Snowflake connection, statement by statement.

Usage: python3 scripts/run_sql.py --connection <name> sql/01_synthetic_data.sql [more files...]
Uses ~/.snowflake/connections.toml. Stops at the first failing statement.
"""
import argparse
import sys
import time

import snowflake.connector
from snowflake.connector.util_text import split_statements


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--connection", required=True)
    p.add_argument("--skip-regex", default=None, help="skip statements matching this regex")
    p.add_argument("files", nargs="+")
    a = p.parse_args()
    import re
    skip = re.compile(a.skip_regex, re.S | re.I) if a.skip_regex else None
    con = snowflake.connector.connect(connection_name=a.connection)
    cur = con.cursor()
    for f in a.files:
        print(f"== {f}")
        with open(f) as fh:
            for stmt, _ in split_statements(fh, remove_comments=True):
                s = stmt.strip()
                if not s:
                    continue
                head = " ".join(s.split())[:90]
                if skip and skip.search(s):
                    print(f"   SKIP {head}")
                    continue
                t = time.time()
                try:
                    cur.execute(s)
                    rows = cur.fetchmany(3) if cur.description else []
                    print(f"   ok {time.time()-t:5.1f}s  {head}")
                    for r in rows:
                        print(f"        {str(r)[:160]}")
                except Exception as e:  # noqa: BLE001
                    print(f"   FAIL {head}\n        {e}")
                    sys.exit(1)
    con.close()


if __name__ == "__main__":
    main()
