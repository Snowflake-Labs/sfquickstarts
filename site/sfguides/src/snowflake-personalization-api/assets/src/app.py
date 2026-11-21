import os
import logging

from flask import Flask, jsonify, make_response, send_file, request, abort
from flask_caching import Cache
import snowflake.connector
from snowflake.connector import DictCursor

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# use in-memory cache, defaulted to 3min
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 180

cache = Cache(app)

# connect to Snowflake using internal SPCS token
def connect() -> snowflake.connector.SnowflakeConnection:
    if os.path.isfile("/snowflake/session/token"):
        creds = {
            'host': os.getenv('SNOWFLAKE_HOST'),
            'port': os.getenv('SNOWFLAKE_PORT'),
            'protocol': "https",
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'authenticator': "oauth",
            'token': open('/snowflake/session/token', 'r').read(),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'client_session_keep_alive': True
        }
    else:
        creds = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'client_session_keep_alive': True
        }
    return snowflake.connector.connect(**creds)

conn = connect()

# endpoint for querying the hybrid table
@app.route('/customer/<cust_id>')
@cache.memoize(timeout=180)
def get_customer(cust_id):
    sql_string = '''
        SELECT
            C_CUSTOMER_SK,
            C_CUSTOMER_ID,
            C_CURRENT_CDEMO_SK,
            C_CURRENT_HDEMO_SK,
            C_CURRENT_ADDR_SK,
            C_FIRST_SHIPTO_DATE_SK,
            C_FIRST_SALES_DATE_SK,
            C_SALUTATION,
            C_FIRST_NAME,
            C_LAST_NAME,
            C_PREFERRED_CUST_FLAG,
            C_BIRTH_DAY,
            C_BIRTH_MONTH,
            C_BIRTH_YEAR,
            C_BIRTH_COUNTRY,
            C_LOGIN,
            C_EMAIL_ADDRESS,
            C_LAST_REVIEW_DATE
        FROM api.data.hybrid_customer
        WHERE C_CUSTOMER_SK in ({cust_id});
    '''
    sql = sql_string.format(cust_id=cust_id)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the QUERY_HISTORY for details.")

@app.route("/")
def default():
    return make_response(jsonify(result='Nothing to see here'))

# test HTML page
@app.route("/test")
def tester():
    return send_file("api_test.html")

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)

if __name__ == '__main__':
    app.run(port=8001, host='0.0.0.0')
