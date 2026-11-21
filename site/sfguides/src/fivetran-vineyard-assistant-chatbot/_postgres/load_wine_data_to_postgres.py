#!/usr/bin/env python3
"""
Load the California wine country dataset from the public Amazon S3 bucket
into a PostgreSQL database (AWS RDS, Google Cloud SQL, Azure Database for
PostgreSQL, or any other PostgreSQL 12+ server).

Creates <schema>.california_wine_country_visits (default schema: agriculture)
and loads all 743 rows. Safe to re-run: the table is dropped and recreated.

Connection settings come from the standard libpq environment variables:
  PGHOST, PGPORT (default 5432), PGDATABASE, PGUSER, PGPASSWORD, PGSSLMODE

Usage:
  pip install psycopg2-binary
  export PGHOST=<host> PGDATABASE=<db> PGUSER=<user> PGPASSWORD=<password>
  python3 load_wine_data_to_postgres.py [--schema agriculture]
"""
import argparse
import json
import re
import sys
import urllib.request

import psycopg2
from psycopg2.extras import execute_values

S3_URL = ("https://ft-s3-lab-bkt.s3.amazonaws.com/winedata/"
          "california_wine_country_visits_202409021224.json")
TABLE = "california_wine_country_visits"


def column_name(key):
    # "winery or vineyard" -> winery_or_vineyard
    return re.sub(r"[^a-z0-9_]+", "_", key.strip().lower())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", default="agriculture")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", args.schema):
        sys.exit("Schema must be lowercase letters, digits and underscores.")

    print("Downloading " + S3_URL)
    with urllib.request.urlopen(S3_URL, timeout=60) as resp:
        records = json.load(resp)
    keys = list(records[0].keys())
    cols = [column_name(k) for k in keys]
    print("Downloaded %d records, %d columns" % (len(records), len(cols)))

    # id is the only numeric field, everything else is text
    col_defs = ", ".join(
        '"%s" %s' % (c, "integer PRIMARY KEY" if c == "id" else "text")
        for c in cols)
    col_list = ", ".join('"%s"' % c for c in cols)
    rows = [tuple(r.get(k) for k in keys) for r in records]

    with psycopg2.connect(connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS %s" % args.schema)
            cur.execute("DROP TABLE IF EXISTS %s.%s" % (args.schema, TABLE))
            cur.execute("CREATE TABLE %s.%s (%s)" % (args.schema, TABLE, col_defs))
            execute_values(
                cur,
                "INSERT INTO %s.%s (%s) VALUES %%s" % (args.schema, TABLE, col_list),
                rows)
            cur.execute("SELECT count(*) FROM %s.%s" % (args.schema, TABLE))
            print("Loaded %d rows into %s.%s" % (cur.fetchone()[0], args.schema, TABLE))


if __name__ == "__main__":
    main()
