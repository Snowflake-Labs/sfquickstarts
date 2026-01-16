# Check OpenRouteService Prerequisite

## Description
Verify that the OpenRouteService Native App is installed and running before deploying the Route Optimization Demo.

## Trigger
Use this skill when:
- User wants to deploy the route optimization demo
- User asks to check if ORS is installed
- User mentions "check prerequisites" for the demo
- Before running any demo deployment skills

## Instructions

### Step 1: Check if OpenRouteService Native App exists

Run the following SQL to check if the native app is installed:

```sql
SHOW APPLICATIONS LIKE 'OPENROUTESERVICE_NATIVE_APP';
```

**If the result is empty (no rows returned):**
- The OpenRouteService Native App is NOT installed
- STOP and inform the user they need to install it first
- Provide the following guidance:

> **⚠️ OpenRouteService Native App Not Found**
> 
> The Route Optimization Demo requires the OpenRouteService Native App to be installed and running.
> 
> To install it, run the following command in Cortex Code:
> ```
> use the local skill from oss-install-openrouteservice-native-app/skills/deploy-route-optimizer
> ```
> 
> Or follow the full quickstart guide: [Install OpenRouteService Native App](../oss-install-openrouteservice-native-app/)
> 
> Once the Native App is installed and all 4 services are running, come back and run this demo deployment again.

**If the result shows the app exists, proceed to Step 2.**

### Step 2: Verify the app is activated and services are running

Check the application status:

```sql
SELECT 
    APPLICATION_NAME,
    STATUS,
    CREATED,
    UPGRADED
FROM SNOWFLAKE.ACCOUNT_USAGE.APPLICATIONS
WHERE APPLICATION_NAME = 'OPENROUTESERVICE_NATIVE_APP';
```

Also check if the routing functions are accessible by testing a simple call:

```sql
SELECT OPENROUTESERVICE_NATIVE_APP.APP.DIRECTIONS(
    ARRAY_CONSTRUCT(
        OBJECT_CONSTRUCT('lon', -122.4194, 'lat', 37.7749),
        OBJECT_CONSTRUCT('lon', -122.4094, 'lat', 37.7849)
    ),
    'driving-car'
) AS test_result;
```

**If the function call fails:**
- The app may not be activated or services may not be running
- Inform the user:

> **⚠️ OpenRouteService Services Not Running**
> 
> The OpenRouteService Native App is installed but the routing services are not responding.
> 
> Please:
> 1. Navigate to **Data Products > Apps > OPENROUTESERVICE_NATIVE_APP** in Snowsight
> 2. Grant any required privileges if prompted
> 3. Click **Activate** if not already activated
> 4. Use the **Service Manager** to ensure all 4 services show ✅ RUNNING:
>    - Data Downloader
>    - Open Route Service
>    - Routing Gateway
>    - VROOM Service
> 
> Once all services are running, come back and run this demo deployment again.

**If the function call succeeds, proceed to Step 3.**

### Step 3: Confirm prerequisite is satisfied

If both checks pass:
- Inform the user that the OpenRouteService prerequisite is satisfied
- The demo deployment can proceed

> **✅ OpenRouteService Prerequisite Satisfied**
> 
> The OpenRouteService Native App is installed and routing functions are working.
> 
> You can now proceed with deploying the Route Optimization Demo.

## Success Criteria
- OpenRouteService Native App exists in the account
- The DIRECTIONS function returns a valid response
- User is informed of the status and next steps

## Error Handling
- If app not found: Direct user to install quickstart
- If services not running: Direct user to activate and check Service Manager
- If function fails for other reasons: Display the error and suggest checking the Native App status
