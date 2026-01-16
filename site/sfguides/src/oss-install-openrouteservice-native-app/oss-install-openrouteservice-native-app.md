author: Becky O'Connor and Piotr Paczewski
id: oss-install-openrouteservice-native-app
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/native-apps, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/geospatial, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Deploy an OpenRouteService Native App in Snowflake using Cortex Code skills. Create a self-contained routing engine with directions, optimization, and isochrones - no external APIs required.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-create-a-route-optimisation-and-vehicle-route-plan-simulator

# Install OpenRouteService Native App with Cortex Code

> 🚀 **Install. Customize. Optimize.** Use natural language to deploy a complete route optimization solution in Snowflake - no code, no external APIs, just results.

<!-- ------------------------ -->
## Overview 

![alt text](assets/overview-map.png)

**Deploy a complete route optimization platform in minutes using just natural language commands.**

This solution installs an [Open Route Service](https://openrouteservice.org/) Native App directly in your Snowflake account using **Cortex Code** - Snowflake's AI-powered CLI. No complex setup, no external APIs, no data leaving Snowflake.

### What You'll Build

🚚 **Route Optimization Simulator** - A fully interactive Streamlit app that simulates vehicle routing scenarios using real-world business locations from the **Carto Overture Maps** dataset.

📍 **Three Powerful Routing Functions:**
- **Directions** - Calculate optimal routes between multiple waypoints
- **Optimization** - Match delivery jobs to vehicles based on time windows, capacity, and skills
- **Isochrones** - Generate catchment polygons showing reachable areas within a given drive time

🗺️ **Any Location, Any Industry** - Customize to Paris, London, New York, or anywhere in the world. Configure for food distribution, healthcare logistics, retail delivery, or your specific use case.

### Why This Matters

| Traditional Approach | This Solution |
|---------------------|---------------|
| External API dependencies | Self-contained Native App |
| Data leaves your environment | Everything stays in Snowflake |
| Complex integration work | Deploy with natural language commands |
| Pay-per-call API limits | Unlimited calls, you control compute |
| Hours of setup | Minutes to deploy |

### Prerequisites

> **_NOTE:_** Cortex Code is currently in **Private Preview**. Contact your Snowflake account team for access.

**This is what you will need**:

-   **ACCOUNTADMIN** access to your Snowflake account
    
-   [Snowpark Container Services Activated](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)

> **_NOTE:_** This is enabled by default with the exception of Free Trials where you would need to contact your snowflake representative to activate it.  

-   [External Access Integration Activated](https://docs.snowflake.com/en/sql-reference/sql/create-external-access-integration) - Required to download map files from provider account

-   **Cortex Code CLI** installed and configured
    - Installation: Once you have access, install via the provided instructions
    - Add to your PATH: `export PATH="$HOME/.local/bin:$PATH"` (add to `~/.zshrc` or `~/.bashrc`)
    - Verify: `cortex --version`

> **_TODO:_** 📝 This section requires update once the official Cortex Code installation method is publicly available. The current instructions are for Private Preview access only.

-   **Container Runtime** - One of the following:
    - [Podman](https://podman.io/) (recommended): `brew install podman` (macOS) 
    - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

-   [VSCode](https://code.visualstudio.com/download) recommended for running Cortex Code commands

### Route Planning And Optimization Architecture

The architecture below shows the solution which uses a native app and container services to power sophisticated routing and optimisation functions. 

![alt text](assets/architecture-diagram.png)

This is a self-contained service which is managed by you. There are no API calls outside of Snowflake and no API limitations. This solution uses a medium CPU pool which is capable of running unlimited service calls within **San Francisco** (the default map). If you wish to use a larger map such as Europe or the World, you can increase the size of the compute.


### What You'll Learn 

- Deploy a Snowflake Native App using **Cortex Code** AI-powered CLI with natural language commands
- Use **Snowpark Container Services** to run OpenRouteService as a self-managed routing engine
- A more advanced understanding of **Geospatial** data in Snowflake
- Using **AISQL** functions with Snowpark to explore routing capabilities
- Work with 3 routing functions deployed via the Native App:
  - **Directions** - Simple and multi-waypoint routing based on road network and vehicle profile
  - **Optimization** - Route optimization matching demands with vehicle availability
  - **Isochrones** - Catchment area analysis based on travel time
- Creating a location centric application using Streamlit 
- An insight to the Carto Overture Places dataset to build an innovative route planning simulation solution

### What You'll Build 
- A **Route Optimization Simulator** Streamlit application to simulate route plans for potential customers anywhere in the world. This could be for a potential new depot or simply to try out route optimisation which you will later replace with a real data pipeline.

<!-- ------------------------ -->
## Deploy the Route Optimizer

![Cortex Code Deployment](assets/architecture-diagram.png)

Use Cortex Code, Snowflake's AI-powered CLI, to deploy the Native App using natural language commands and automated skills.

### Setup Cortex Code

1. **Fork and clone the repository**:
   - **Fork the repo**: Go to [GitHub](https://github.com/Snowflake-Labs/sfguide-create-a-route-optimisation-and-vehicle-route-plan-simulator) and click **Fork** to create your own copy
   - **Clone your fork** using the integrated terminal:
     ```bash
     git clone https://github.com/<YOUR-USERNAME>/sfguide-create-a-route-optimisation-and-vehicle-route-plan-simulator
     cd sfguide-create-a-route-optimisation-and-vehicle-route-plan-simulator
     ```
   - **Without Git**: Download the ZIP from the repository and extract it, then navigate to the folder in VS Code

   After cloning, open the folder in VS Code. You should see the following structure in your Explorer:

   ![Cloned Repository Structure](assets/cloned_objects.png)

   > **_IMPORTANT:_** If you plan to customize the deployment (change location, vehicles, or industries), you **must fork the repository first**. Cloning the original repo directly won't give you permission to create branches or push your customizations.

2. **Launch Cortex Code CLI** in the VS Code terminal:
   ```bash
   cortex
   ```

3. **Connect to Snowflake** - Cortex Code will prompt you to select or create a connection.  once a connection has ben created using one of the authentication methods, you will now be able to start cortex code in the terminal by using the **cortex** command which will give you a similar screen as below.

![Cortex Code Logged In](assets/co-co-logged-in.png)

### Understanding Cortex Code Skills

Before running any commands, it's helpful to understand what **skills** are and how they power this solution.

**What are Skills?**

Skills are structured specifications that instruct Cortex Code how to perform a procedure. Think of them as detailed recipes - they define the exact steps, parameters, and verification checks needed to accomplish a task. Each skill is a markdown file that describes:

- **What the skill does** - A clear description of the outcome
- **Step-by-step instructions** - The exact sequence of actions to perform
- **Stopping points** - Where to pause for user input or verification
- **Success criteria** - How to verify the task completed correctly

**Benefits of Using Skills**

| Benefit | Description |
|---------|-------------|
| **Consistency** | Skills ensure the same steps are followed every time, reducing human error |
| **Reusability** | Once created, skills can be shared and reused across projects and teams |
| **Transparency** | You can read the skill file to understand exactly what will happen before running it |
| **Customizability** | Skills can be modified to fit your specific requirements |
| **AI-Assisted Creation** | Cortex Code can help you create new skills from natural language descriptions |

**How This Solution Uses Skills**

This repository demonstrates how skills can manage the **complete lifecycle** of an end-to-end Snowflake analytical solution - from installation through customization to uninstallation. The 6 pre-built skills in the `skills/` folder cover every stage:

| Stage | Skills | What They Do |
|-------|--------|--------------|
| **🔍 Prerequisites** | `check-prerequisites` | Verify dependencies, container runtime, and Snowflake access |
| **📦 Install** | `deploy-route-optimizer`, `deploy-demo` | Deploy Native App, container services, notebooks, and Streamlits |
| **⚙️ Customize** | `customizations` (with 6 sub-skills) | Change map region, vehicle types, industries, and sample data |
| **🗑️ Uninstall** | `uninstall-route-optimizer` | Cleanly remove all resources from your Snowflake account |

To run any skill, simply tell Cortex Code:
```
use the local skill from skills/<skill-name>
```

For example:
```
use the local skill from openrouteservice/skills/deploy-route-optimizer
```

Cortex Code reads the skill's markdown file and executes each step, asking for input when needed and verifying success before moving on.

> **_TIP:_** Want to see what a skill does before running it? Open the skill's `.md` file in the `skills/` folder to review the exact steps.

### Verify Prerequisites (Optional)

Run the prerequisites check skill to ensure all dependencies are installed:
   ```
   use the local skill from openrouteservice/skills/check-prerequisites
   ```

### Deploy the Native App

Simply type the following command in Cortex Code:

```
use the local skill from openrouteservice/skills/deploy-route-optimizer
```

Cortex Code will automatically:
- Create the required database, stages, and image repository
- Upload configuration files
- Detect your container runtime (Docker or Podman)
- Build and push all 4 container images
- Deploy the Native App

The skill will guide you through any required steps, including:
- Selecting your preferred container runtime if both are available
- Authenticating with the Snowflake image registry
- Monitoring the build progress

### Activate the App

Once deployment completes, Cortex Code will provide a link to your app. You need to:

1. Navigate to **Data Products > Apps > OPENROUTESERVICE_NATIVE_APP** in Snowsight
2. Grant the required privileges via the UI
3. Click **Activate** and wait for the services to start

### Service Manager

After activation, the Native App provides a **Service Manager** dashboard to monitor and control all ORS services:

![Service Manager](assets/service-manager.png)

The Service Manager shows:
- **Service Status Dashboard** - Overview of all running, stopped, and error states
- **Individual Service Management** - Start/Stop controls for each service:
  - **Data Downloader** - Downloads and updates map data
  - **Open Route Service** - Core routing and directions engine
  - **Routing Gateway** - API gateway for routing requests
  - **VROOM Service** - Route optimization engine

Use the **Start All** / **Stop All** buttons for bulk operations, or manage services individually. Click **Refresh Status** to update the dashboard.

> **_TIP:_** All 4 services should show ✅ RUNNING status before using the routing functions.

### ORS Configuration

The Native App is configured via the `ors-config.yml` file which controls:

**Map Source File**
```yml
ors:
  engine:
    profile_default:
      build:  
        source_file: /home/ors/files/SanFrancisco.osm.pbf
```
The default deployment uses San Francisco. When you customize the map region, this path is updated automatically.

**Routing Profiles**

The configuration defines which vehicle types are available for routing:

| Profile | Description | Default |
|---------|-------------|---------|
| `driving-car` | Standard passenger vehicle | ✅ Enabled |
| `driving-hgv` | Heavy goods vehicle (trucks) | ✅ Enabled |
| `cycling-road` | Road bicycle | ✅ Enabled |
| `cycling-regular` | Regular bicycle | ❌ Disabled |
| `cycling-mountain` | Mountain bicycle | ❌ Disabled |
| `cycling-electric` | Electric bicycle | ❌ Disabled |
| `foot-walking` | Pedestrian walking | ❌ Disabled |
| `foot-hiking` | Hiking trails | ❌ Disabled |
| `wheelchair` | Wheelchair accessible | ❌ Disabled |

> **_NOTE:_** Enabling more profiles increases graph build time and compute resource usage. The default configuration covers most delivery and logistics use cases.

**Optimization Limits**

The config also controls route optimization capacity:
```yml
    matrix:
      maximum_visited_nodes: 100000000
      maximum_routes: 250000
```
These settings support complex route optimizations with many vehicles and delivery points.

### Function Tester

The Native App includes a built-in **Function Tester** Streamlit application for testing the routing functions interactively.

![Function Tester](assets/function-tester.png)

To access the Function Tester:
1. Open **Data Products > Apps > OPENROUTESERVICE_NATIVE_APP** in Snowsight
2. Navigate to the **Function Tester** page in the app

The Function Tester allows you to test all three routing functions:

**🗺️ DIRECTIONS**
- Select start and end locations from preset addresses
- Choose a routing profile (car, truck, bicycle)
- View the calculated route on an interactive map
- See step-by-step directions and distance/duration

**🚚 OPTIMIZATION**
- Configure multiple vehicles with different:
  - Time windows (start/end hours)
  - Capacity limits
  - Skill sets (refrigeration, hazardous goods, etc.)
- Add delivery jobs with:
  - Locations
  - Time windows
  - Required skills
- Run the optimization to see assigned routes per vehicle
- View detailed itinerary for each vehicle

**⏰ ISOCHRONES**
- Select a center point location
- Choose travel time in minutes
- Generate a catchment polygon showing how far you can travel
- Useful for delivery zone planning and coverage analysis

> **_TIP:_** The Function Tester comes pre-configured with San Francisco addresses. When you customize the map region, the Function Tester is automatically updated with region-specific coordinates.

<!-- ------------------------ -->
## Customize Your Deployment

The default deployment uses San Francisco with standard vehicle types and demo industries (Food, Healthcare, Cosmetics). Before deploying the demo, you can customize **three key areas**:

| Customization | Default | Example Custom |
|---------------|---------|----------------|
| 🗺️ **Map Region** | San Francisco | Paris, London, Tokyo, etc. |
| 🚚 **Vehicle Types** | Car, HGV, Road Bicycle | Add walking, wheelchair, electric bicycle |
| 🏭 **Industries** | Food, Healthcare, Cosmetics | Beverages, Electronics, Office Supplies |

> **_NOTE:_** This step is optional. If you skip customization, the demo will use the defaults.

To customize, run:

```
use the local skill from openrouteservice/skills/customizations
```

### Modular Customization Architecture

The customization system uses a **modular architecture** with individual sub-skills that can be run independently or orchestrated together:

```
skills/customizations/
├── customizations.md    ← Main orchestrator (entry point)
├── location.md          ← Download new map, rebuild graphs
├── vehicles.md          ← Configure routing profiles  
├── industries.md        ← Customize industry categories
├── streamlits.md        ← Update Function Tester & Simulator
├── aisql-notebook.md    ← Update AI prompts for your region
└── carto-notebook.md    ← Update POI data source
```

### How the Customization Works

The main `customizations` skill orchestrates the process by asking **three yes/no questions**, then runs only the relevant sub-skills:

1. **"Do you want to customize the LOCATION (map region)?"**
   - If YES → Runs `location.md` → `vehicles.md`
   - If NO → Skips map download entirely

2. **"Do you want to customize VEHICLE TYPES (routing profiles)?"**
   - If YES → Runs `vehicles.md`
   - If NO → Keeps default profiles (car, HGV, road bicycle)

3. **"Do you want to customize INDUSTRIES for the demo?"**
   - If YES → Runs `industries.md`
   - If NO → Keeps default industries (Food, Healthcare, Cosmetics)

**For ANY customization:** The orchestrator ALWAYS runs `streamlits.md`, `aisql-notebook.md`, and `carto-notebook.md` to ensure all components are updated consistently, followed by `deploy-demo` to apply changes to Snowflake.

### Which Sub-Skills Run Based on Your Choices

| Your Choices | Sub-Skills Executed | What Gets Updated |
|--------------|---------------------|-------------------|
| **Location = YES** | `location` → `vehicles` → `streamlits` → `aisql-notebook` → `carto-notebook` → **deploy-route-optimizer** → **deploy-demo** | Map downloaded, graphs rebuilt, Native App updated, all demo content updated |
| **Vehicles = YES** | `vehicles` → `streamlits` → `aisql-notebook` → `carto-notebook` → **deploy-route-optimizer** → **deploy-demo** | Routing profiles modified, Native App updated, all demo content updated |
| **Industries = YES** | `industries` → `streamlits` → `aisql-notebook` → `carto-notebook` → **deploy-demo** | Industry config updated, demo content updated (no Native App change) |
| **Location/Vehicles + Industries** | All relevant sub-skills → **deploy-route-optimizer** → **deploy-demo** | Everything updated |
| **Nothing** | None | Exit (no changes) |

> **_IMPORTANT:_** 
> - For ANY customization, all Streamlit apps and notebooks are updated, and `deploy-demo` MUST be run
> - If Location OR Vehicles change, `deploy-route-optimizer` MUST also be run to push the updated `function_tester.py` to the Native App (images don't need rebuilding - only app code is updated)

> **If using Git (with your fork):** Changes are saved to a feature branch (e.g., `feature/ors-paris`), allowing you to switch back to `main` for defaults. Make sure you cloned **your fork** (not the original repo) to have permission to create branches and push changes.
> **If not using Git:** Changes are made directly to local files. Keep a backup if needed.

### Running Individual Sub-Skills

You can also run specific customizations directly without going through the orchestrator:

```bash
# Just change the map region
use the local skill from openrouteservice/skills/customizations/location

# Just modify vehicle profiles
use the local skill from openrouteservice/skills/customizations/vehicles

# Just change industries for the demo
use the local skill from demo_example/skills/customizations/industries

# Just update the Streamlit apps with new coordinates
use the local skill from demo_example/skills/customizations/streamlits

# Just update the AISQL notebook prompts
use the local skill from demo_example/skills/customizations/aisql-notebook

# Just update the Carto POI data notebook
use the local skill from demo_example/skills/customizations/carto-notebook
```

> **_IMPORTANT:_** When running sub-skills independently, be aware of dependencies:
> - After running `location`, you should also run `vehicles` → `streamlits` → `aisql-notebook` → `carto-notebook` → **deploy-route-optimizer** → `deploy-demo`
> - After running `vehicles`, you should also run `streamlits` → `aisql-notebook` → `carto-notebook` → **deploy-route-optimizer** → `deploy-demo`
> - After running `industries`, you should also run `streamlits` → `aisql-notebook` → `carto-notebook` → `deploy-demo`
> - **For Location/Vehicles changes:** `deploy-route-optimizer` is needed to push updated `function_tester.py` to the Native App
> - **For ANY customization:** All Streamlits and notebooks must be updated, and `deploy-demo` MUST be run

### Example: Customizing to Paris with All Options

When you run `use the local skill from openrouteservice/skills/customizations` and answer YES to all three questions, the orchestrator runs the sub-skills in order:

**Step 1: Location Sub-Skill** (`location.md`)
- Choose **Paris** or **Île-de-France** from Geofabrik
- Downloads and uploads the OpenStreetMap data
- Updates `ors-config.yml` with new map path

**Step 2: Vehicles Sub-Skill** (`vehicles.md`)
- Choose which routing profiles to enable:
  - `driving-car` - Standard passenger vehicle ✅
  - `driving-hgv` - Heavy goods vehicle (trucks) ✅
  - `cycling-road` - Road bicycles ✅
  - `foot-walking` - Pedestrian (optional)
  - `wheelchair` - Wheelchair accessible (optional)
- Updates routing profile configuration

**Step 3: Industries Sub-Skill** (`industries.md`)
- Add or modify industry categories for your use case
- Configures product types, customer types, and vehicle skills for each industry

**Step 4: Streamlits Sub-Skill** (`streamlits.md`)
- Updates Function Tester with Paris coordinates
- Updates Simulator with Paris as default city

**Step 5: AISQL Notebook Sub-Skill** (`aisql-notebook.md`)
- Updates all AI prompts to generate Paris-based sample data

**Step 6: Carto Notebook Sub-Skill** (`carto-notebook.md`)
- Updates POI data source with Paris geohash filter

**Step 7: Save & Deploy**
- Optionally creates Git feature branch
- Prompts to run `deploy-demo` to apply changes

**⏳ Wait for Services to Restart**

After the map is uploaded (if location was changed) or profiles were modified (if vehicles were changed), the services need to rebuild the routing graphs. You can monitor progress in the Service Manager:

1. Navigate to **Data Products > Apps > OPENROUTESERVICE_NATIVE_APP**
2. Check the **Service Manager** - all 4 services should show ✅ RUNNING
3. The **Open Route Service** will take the longest as it builds the graph files

Once services are running, the Function Tester will show **Paris addresses** instead of San Francisco!

> **_TIP:_** If you only want to change industries (and keep San Francisco with default vehicles), answer NO to location and vehicles. This skips map download and graph building entirely - making it much faster!

### Map Download & Resource Scaling (Location Changes Only)

If you selected YES to location customization, the skill downloads OpenStreetMap data from Geofabrik or BBBike. The bigger the map file, the longer it takes to:
- **Download** the OSM data from the source
- **Upload** to the Snowflake stage
- **Generate graph files** for route calculations

| Map Size | Example Regions | Download Time | Graph Build Time | 
|----------|-----------------|---------------|------------------|
| < 100MB | San Francisco, Zurich | Minutes | 5-15 minutes |
| 100MB - 1GB | New York State, Switzerland | 10-30 minutes | 30-60 minutes |
| 1-5GB | Germany, France, California | 30-60 minutes | 1-3 hours |
| > 5GB | Great Britain, entire countries | 1-2 hours | 3-8+ hours |

> **_IMPORTANT:_** For country-wide or large region maps, graph generation can take **several hours**. The services will show as "running" while building graphs in the background.

**Automatic Compute Scaling**

Cortex Code will detect the map size after download and offer to **resize the compute pool** to speed up graph generation:

| Map Size | Suggested Compute | Auto-Suspend Extension |
|----------|-------------------|------------------------|
| < 1GB | CPU_X64_S (default) | 1 hour |
| 1-5GB | HIGHMEM_X64_M | 8 hours |
| > 5GB | HIGHMEM_X64_M | 24 hours |

When prompted, you can accept the scaling recommendation to ensure graphs are computed as quickly as possible. The extended auto-suspend time prevents the service from shutting down mid-build.

> **_TIP:_** For quickest results, use the smallest map that covers your use case. A city-level map (e.g., New York) builds much faster than a country map (e.g., USA).

**Routing Profile Configuration**

The skill presents available routing profiles and lets you enable/disable them:

| Profile | Category | Description |
|---------|----------|-------------|
| `driving-car` | Driving | Standard passenger vehicle |
| `driving-hgv` | Driving | Heavy goods vehicles (trucks) |
| `cycling-regular` | Cycling | Standard bicycles |
| `cycling-road` | Cycling | Road bicycles |
| `cycling-mountain` | Cycling | Mountain bicycles |
| `cycling-electric` | Cycling | Electric bicycles |
| `foot-walking` | Foot | Pedestrian walking |
| `foot-hiking` | Foot | Hiking trails |
| `wheelchair` | Wheelchair | Wheelchair accessible routes |

> **_NOTE:_** Enabling more profiles increases graph build time. The default (driving-car, driving-hgv, cycling-road) covers most logistics use cases.

**Function Tester & Notebook Customization**

The skill automatically updates:

1. **Function Tester Streamlit** - Generates region-specific sample addresses for:
   - Start locations (5 landmarks/city centers)
   - End locations (5 different destinations)
   - Waypoints (20 locations across the region)

2. **AISQL Notebook** - Updates all AI prompts to generate sample data for your region:
   - For **country/state maps** (e.g., Germany, California): You'll be asked to choose a specific city within that region for realistic delivery scenarios
   - For **city maps** (e.g., New York, London): Uses the city directly

   This ensures AI-generated restaurants, delivery jobs, and customer locations are within drivable distance of each other.

**Industry Category Customization (Optional)**

The default industries are Healthcare, Food, and Cosmetics. The skill offers an optional step to customize industries for your specific use case.

**Each industry gets its own specific configuration:**

| Industry | Product Types (PA/PB/PC) | Customer Types | Vehicle Skills |
|----------|--------------------------|----------------|----------------|
| **Healthcare** | Flammable, Sharps, Temperature-controlled | Hospitals, Pharmacies, Dentists | Hazmat Handler, Cold Chain, Standard |
| **Food** | Fresh, Frozen, Non-perishable | Supermarkets, Restaurants, Butchers | Fresh Delivery, Refrigerated, Standard |
| **Cosmetics** | Hair products, Electronics, Make-up | Outlets, Fashion stores | Premium, Fragile, Standard |

**Example custom industries:**

| Industry | Product Types | Customer Types | Vehicle Skills |
|----------|--------------|----------------|----------------|
| **Beverages** | Alcoholic, Carbonated, Still Water | Bars, Restaurants, Hotels | Age Verification, Fragile Handler, Heavy Load |
| **Electronics** | High-Value, Fragile Equipment, Standard | Electronics Stores, Computer Shops | Secure Transport, Fragile Handler, Standard |
| **Pharmaceuticals** | Controlled, Temperature Sensitive, OTC | Pharmacies, Hospitals, Clinics | Licensed Carrier, Cold Chain, Standard |

> **_IMPORTANT:_** After customizing industries, you must run the `deploy-demo` skill to apply the changes. The skill will automatically prompt you to continue to deployment.

> **_TIP:_** The Streamlit app reads industries dynamically from the database - your custom industries appear automatically after deployment.

**Git Branch Management (Requires Your Fork)**

If you're using Git with **your forked repository**, customizations are saved to a feature branch (e.g., `feature/ors-paris`), preserving the original San Francisco configuration on `main`. To switch between regions:

```bash
git checkout feature/ors-paris    # Switch to Paris
git checkout main                 # Switch back to San Francisco
```

Then redeploy with Cortex Code to apply the configuration.

> **_NOTE:_** Branch creation and pushing requires write access. If you cloned the original Snowflake-Labs repo directly, you won't have permission to push branches. See the [Prerequisites](#prerequisites) section for fork instructions.

> **_NOTE:_** If you downloaded the repository as a ZIP (without Git), changes are made directly to your local files. Keep a backup if you want to preserve the original configuration.

Once your services are running with the new map (or if you skipped customization), you're ready to deploy the demo!

<!-- ------------------------ -->
## Next Steps: Deploy the Demo

🎉 **Congratulations!** Your OpenRouteService Native App is now installed and configured.

To deploy the Route Optimization Simulator demo with real-world POI data and interactive notebooks, continue to the next quickstart:

👉 **[Deploy Route Optimization Demo](../oss-deploy-route-optimization-demo/)**

The demo quickstart will:
- Acquire the **Carto Overture Maps Places** dataset with 50+ million POIs worldwide
- Deploy interactive **AISQL notebooks** to explore routing functions
- Create the **Route Optimization Simulator** Streamlit app

All demo content will use your configured map region (San Francisco by default, or your customized region like Paris).

<!-- ------------------------ -->
## Available Cortex Code Skills

For reference, here are the Cortex Code skills for the OpenRouteService Native App:

### OpenRouteService Skills

| Skill | Description | Command |
|-------|-------------|---------|
| `check-prerequisites` | Verify and install dependencies | `use the local skill from openrouteservice/skills/check-prerequisites` |
| `deploy-route-optimizer` | Deploy the ORS Native App | `use the local skill from openrouteservice/skills/deploy-route-optimizer` |
| `uninstall-route-optimizer` | Remove app and all dependencies | `use the local skill from openrouteservice/skills/uninstall-route-optimizer` |

### Customization Sub-Skills

These can be run individually for targeted updates to the Native App:

| Sub-Skill | Description | Command |
|-----------|-------------|---------|
| `location` | Download new map, rebuild graphs | `use the local skill from openrouteservice/skills/customizations/location` |
| `vehicles` | Configure routing profiles | `use the local skill from openrouteservice/skills/customizations/vehicles` |

> **_TIP:_** Use the main `customizations` skill to let Cortex Code orchestrate the process: `use the local skill from openrouteservice/skills/customizations`

### Demo Skills

For demo-related skills (deploying notebooks, Streamlit simulator, and demo customizations), see the **[Deploy Route Optimization Demo](../oss-deploy-route-optimization-demo/)** quickstart.

<!-- ------------------------ -->
## Uninstall the Route Optimizer

To remove the Route Optimizer Native App and all associated resources from your Snowflake account, use the uninstall skill:

```
use the local skill from openrouteservice/skills/uninstall-route-optimizer
```

This skill will:
- Remove the Native App (`OPENROUTESERVICE_NATIVE_APP`)
- Drop the Application Package (`OPENROUTESERVICE_NATIVE_APP_PKG`)
- Delete the setup database (`OPENROUTESERVICE_SETUP`) including all stages and image repository
- Delete the demo database (`VEHICLE_ROUTING_SIMULATOR`) including notebooks and Streamlit apps
- Remove the compute pool and all container services
- Optionally remove the Carto Overture Maps marketplace data (`OVERTURE_MAPS__PLACES`)
- Optionally remove the warehouse and local container images

> **_NOTE:_** The uninstall skill will ask for confirmation before removing resources. This is a destructive operation that cannot be undone.

<!-- ------------------------ -->
## Conclusion and Resources
### Conclusion

You've just deployed a **self-contained routing engine** in Snowflake using natural language commands - no complex configuration files, no external API dependencies, and no data leaving your Snowflake environment.

This solution demonstrates the power of combining:
- **Cortex Code** - AI-powered CLI that turns natural language into automated workflows
- **Snowpark Container Services** - Running OpenRouteService as a self-managed Native App
- **Native App Functions** - SQL-callable routing functions for directions, optimization, and isochrones

The key advantage of this approach is **flexibility without complexity**. Want to switch from San Francisco to Paris? Just run the location customization skill. Need to add walking or cycling routes? Enable additional routing profiles. The skill-based approach means you only run the steps you need.

### What You Learned

- **Deploy Native Apps with Cortex Code** - Use natural language skills to automate complex Snowflake deployments including container services, stages, and compute pools

- **Self-Managed Route Optimization** - Run OpenRouteService entirely within Snowflake with no external API calls, giving you unlimited routing requests and complete data privacy

- **Flexible Customization** - Use skills to customize location (any city in the world) and vehicle types (car, HGV, bicycle, walking)

- **Three Routing Functions:**
    - **Directions** - Point-to-point and multi-waypoint routing
    - **Optimization** - Match delivery jobs to vehicles based on time windows, capacity, and skills
    - **Isochrones** - Generate catchment polygons showing reachable areas

### Next Steps

Deploy the demo to see the routing functions in action with real-world POI data:

👉 **[Deploy Route Optimization Demo](../oss-deploy-route-optimization-demo/)**


### Related Resources


#### Source code

- [Source Code on Github](https://github.com/Snowflake-Labs/sfguide-Create-a-Route-Optimisation-and-Vehicle-Route-Plan-Simulator)


#### Further Related Material

- [Geospatial Functions](https://docs.snowflake.com/en/sql-reference/functions-geospatial)

- [Building Geospatial Multi-Layer Apps with Snowflake and Streamlit](/en/developers/guides/building-geospatial-mult-layer-apps-with-snowflake-and-streamlit/)

- [H3 Indexing](https://h3geo.org/docs/)

- [Streamlit](https://streamlit.io/)

- [Pydeck](https://deckgl.readthedocs.io/en/latest/index.html#)

- [Using Cortex and Streamlit With Geospatial Data](/en/developers/guides/using-snowflake-cortex-and-streamlit-with-geospatial-data/)

- [Getting started with Geospatial AI and ML using Snowflake Cortex](/en/developers/guides/geo-for-machine-learning/)


