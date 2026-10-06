install:
  commands:
    - ["npm", "ci", "--include=dev"]

build:
  commands:
    - ["npm", "run", "build"]
    # For standalone mode
    - ["cp", "-r", ".next/static", ".next/standalone/.next/static"]
    - ["cp", "-r", "public", ".next/standalone/public"]
    # Avoid packaging extra node_modules since standalone includes its own
    - ["rm", "-rf", "node_modules"]

run:
  command: ["node", ".next/standalone/server.js"]

# No `version:` key here means this is the build-only manifest: the phases above are
# the build/run config, and `snowflake.yml` says where the app is deployed. If
# `snow app setup` generated an `app.yml` with `version: 2` instead, that one file
# carries both — keep the phases above and add the generated deployment keys to it,
# leaving a single `app.yml`. See the skill's references/manifests.md.

# Secrets read via getSecret(name, type) in lib/snowflake.ts must be declared here so
# the SPCS runtime mounts them under /secrets/<name>/. Map a logical `name` to an
# existing Snowflake SECRET object. `secrets:` (and `environment_variables:`) are
# TOP-LEVEL keys — siblings of install/run at column 0, in both manifest layouts.
# Do NOT nest them under `run:`. Uncomment when the app uses secrets.
# See README → Secrets.
# secrets:
#   - name: SOME_API_KEY
#     secret: DB.SCHEMA.API_KEY
#   - name: SOME_USER_PASS
#     secret: DB.SCHEMA.API_KEY_2
#
# environment_variables:
#   - name: LOG_LEVEL
#     value: "INFO"
