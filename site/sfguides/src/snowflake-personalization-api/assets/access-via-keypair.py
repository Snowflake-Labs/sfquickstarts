# Note: This has been modified from the original to only return the token, it will not connect to SPCS

from generateJWT import JWTGenerator
from datetime import timedelta
import argparse
import logging
import sys
import requests
logger = logging.getLogger(__name__)

def main():
  args = _parse_args()
  token = _get_token(args)
  return token_exchange(token,endpoint=args.endpoint, role=args.role,
                  snowflake_account_url=args.snowflake_account_url,
                  snowflake_account=args.account)
  #spcs_url=f'https://{args.endpoint}{args.endpoint_path}'
  #connect_to_spcs(snowflake_jwt, spcs_url)

def _get_token(args):
  token = JWTGenerator(args.account, args.user, args.private_key_file_path, timedelta(minutes=args.lifetime),
            timedelta(minutes=args.renewal_delay)).get_token()
  logger.info("Key Pair JWT: %s" % token)
  return token

def token_exchange(token, role, endpoint, snowflake_account_url, snowflake_account):
  scope_role = f'session:role:{role}' if role is not None else None
  scope = f'{scope_role} {endpoint}' if scope_role is not None else endpoint
  data = {
    'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
    'scope': scope,
    'assertion': token,
  }
  logger.info(data)
  url = f'https://{snowflake_account}.snowflakecomputing.com/oauth/token'
  if snowflake_account_url:
    url =       f'{snowflake_account_url}/oauth/token'
  logger.info("oauth url: %s" %url)
  response = requests.post(url, data=data)
  logger.info("response status : %s" % response.status_code)
  logger.info("snowflake jwt : %s" % response.text)
  assert 200 == response.status_code, "unable to get snowflake token"
  return response.text

def connect_to_spcs(token, url):
  # Create a request to the ingress endpoint with authz.
  headers = {'Authorization': f'Snowflake Token="{token}"'}
  response = requests.post(f'{url}', headers=headers)
  logger.info("return code %s" % response.status_code)
  logger.info(response.text)

def _parse_args():
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  cli_parser = argparse.ArgumentParser()
  cli_parser.add_argument('--account', required=True,
              help='The account identifier (for example, "myorganization-myaccount" for '
                '"myorganization-myaccount.snowflakecomputing.com").')
  cli_parser.add_argument('--user', required=True, help='The user name.')
  cli_parser.add_argument('--private_key_file_path', required=True,
              help='Path to the private key file used for signing the JWT.')
  cli_parser.add_argument('--lifetime', type=int, default=59,
              help='The number of minutes that the JWT should be valid for.')
  cli_parser.add_argument('--renewal_delay', type=int, default=54,
              help='The number of minutes before the JWT generator should produce a new JWT.')
  cli_parser.add_argument('--role',
              help='The role we want to use to create and maintain a session for. If a role is not provided, '
                'use the default role.')
  cli_parser.add_argument('--endpoint', required=True,
              help='The ingress endpoint of the service')
  cli_parser.add_argument('--endpoint-path', default='/',
              help='The url path for the ingress endpoint of the service')
  cli_parser.add_argument('--snowflake_account_url', default=None,
              help='The account url of the account for which we want to log in. Type of '
                'https://myorganization-myaccount.snowflakecomputing.com')
  args = cli_parser.parse_args()
  return args

if __name__ == "__main__":
  main()