author: Becky O'Connor, Piotr Paczewski, Oleksii Bielov
id: oss-deploy-a-fleet-intelligence-solution-for-taxis
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/native-apps, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/geospatial, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Build a Fleet Intelligence Control Center for taxi operations using OpenRouteService. Deploy a multi-page Streamlit app with real-time driver tracking, route visualization, and H3 heat maps - powered by Snowflake Cortex AI and geospatial analytics.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-create-a-route-optimisation-and-vehicle-route-plan-simulator

# Deploy Fleet Intelligence Solution for Taxis

> 🚖 **Track. Analyze. Optimize.** Build a real-time taxi fleet control center with AI-powered insights - powered by OpenRouteService in Snowflake.

<!-- ------------------------ -->
## Overview 

![Fleet Intelligence Control Center](assets/control-center.png)

**Build a fully interactive Fleet Intelligence Control Center using the OpenRouteService Native App.**

This quickstart deploys a multi-page Streamlit application that simulates a taxi fleet operations dashboard. Track individual drivers, visualize routes in real-time, and analyze fleet density with interactive heat maps - all powered by Snowflake's geospatial capabilities.

### What You'll Build

🚖 **Fleet Intelligence Control Center** - A multi-page Streamlit dashboard that:
- Tracks individual driver journeys with route visualization
- Provides AI-powered trip analysis using Snowflake Cortex
- Displays fleet density heat maps with H3 hexagon visualization
- Shows driver performance metrics including speed and distance analytics

📊 **Fleet Analytics** - Real-time insights including:
- Driver route tracking with pickup/dropoff locations
- Time-based filtering to analyze trips by hour
- Speed distribution analysis across the fleet
- Interactive maps with pydeck visualization

### Prerequisites

> **_IMPORTANT:_** This demo requires the **OpenRouteService Native App** to be installed and running. If you haven't installed it yet, complete the [Install OpenRouteService Native App](../oss-install-openrouteservice-native-app/) quickstart first.

**Required:**
- OpenRouteService Native App deployed and activated
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed and configured
- Active Snowflake connection with ACCOUNTADMIN access
- Overture Maps Places and Addresses datasets from Snowflake Marketplace

### What You'll Learn 

- Deploy fleet analytics dashboards using Cortex Code skills
- Work with **Carto Overture Maps** datasets for realistic location data
- Use **Snowflake Cortex AI** for trip summaries and analysis
- Build multi-layer geospatial visualizations with Pydeck
- Create H3 hexagon heat maps for density analysis
- Track driver states (waiting, pickup, driving, dropoff, idle)

<!-- ------------------------ -->
## Deploy the Fleet Intelligence Solution

Use Cortex Code to deploy the Fleet Intelligence solution including database setup, data generation, and the Streamlit dashboard.

### Run the Deploy Skill

In the Cortex Code CLI, type:

```
deploy fleet intelligence dashboard
```

> **_NOTE:_** The skill will first verify that the OpenRouteService Native App is installed. If it's not found, it will provide instructions to install it first.

The skill uses interactive prompting to gather required information:

- **Number of drivers**: 20 to 500+ (default: 80)
- **Number of days**: 1 to 30+ (default: 1)
- **City**: San Francisco (default), New York, London, Paris, Chicago, or any custom city

Cortex Code will automatically:
- **Detect ORS Configuration** - Reads the current OpenRouteService map region and enabled routing profiles, then recommends a matching city. If the selected city doesn't match the configured region, it will guide you through changing the map
- **Verify** OpenRouteService Native App is installed and running
- **Acquire Marketplace Data** - Gets Carto Overture Maps Places and Addresses
- **Create Database** - Sets up `OPENROUTESERVICE_SETUP.FLEET_INTELLIGENCE_TAXIS` with required objects
- **Generate Sample Data** - Creates drivers, trips, and routes using ORS
- **Deploy Dashboard** - Creates the Taxi Control Center Streamlit app

### What Gets Installed

The deploy skill creates the following Snowflake objects:

**Marketplace Data**
| Component | Name | Description |
|-----------|------|-------------|
| Database | `OVERTURE_MAPS__PLACES` | Carto Overture Maps Places with POI data |
| Database | `OVERTURE_MAPS__ADDRESSES` | Carto Overture Maps Addresses |

**Fleet Intelligence Database**
| Component | Name | Description |
|-----------|------|-------------|
| Database | `OPENROUTESERVICE_SETUP` | Main setup database |
| Schema | `OPENROUTESERVICE_SETUP.FLEET_INTELLIGENCE_TAXIS` | Core data tables and views |
| Warehouse | `ROUTING_ANALYTICS` | Compute warehouse, XSMALL (auto-suspend 60s) |
| Stage | `STREAMLIT_STAGE` | Stage for Streamlit files |

**Data Tables**
| Table | Description |
|-------|-------------|
| `TAXI_LOCATIONS` | POIs and addresses from Overture Maps for the target city |
| `TAXI_LOCATIONS_NUMBERED` | Indexed location pool for deterministic trip assignment |
| `TAXI_DRIVERS` | Configured drivers with shift assignments |
| `DRIVER_TRIPS` | Trip assignments per driver |
| `DRIVER_TRIPS_WITH_COORDS` | Trips with pickup/dropoff coordinates |
| `DRIVER_ROUTES` | Raw ORS route responses |
| `DRIVER_ROUTES_PARSED` | Parsed route geometries and distances |
| `DRIVER_ROUTE_GEOMETRIES` | Routes with timing data |
| `DRIVER_LOCATIONS` | Interpolated GPS positions with driver states |

**Analytics Views**
| View | Description |
|------|-------------|
| `DRIVER_LOCATIONS_V` | Location points with LON/LAT and state |
| `TRIPS_ASSIGNED_TO_DRIVERS` | Trip routes with geometry |
| `ROUTE_NAMES` | Human-readable route descriptions |
| `TRIP_ROUTE_PLAN` | Route data for Heat Map page |
| `TRIP_SUMMARY` | Trip statistics and speed metrics |

**Streamlit Application**
| Component | Name | Description |
|-----------|------|-------------|
| Streamlit | `TAXI_CONTROL_CENTER` | Multi-page fleet dashboard |

<!-- ------------------------ -->
## Explore the Control Center

Once deployment completes, navigate to the Fleet Intelligence Control Center:

1. Go to **Projects > Streamlits** in Snowsight
2. Click on **TAXI_CONTROL_CENTER**

### Main Dashboard

The main page shows fleet overview statistics:
- **Total Trips** - Number of trips in the simulation
- **Active Drivers** - Drivers with assigned trips
- **Total Distance** - Combined distance driven across all routes
- **Location Points** - Number of location data points in the simulation

### Driver Routes Page

![Driver Performance Summary](assets/driver-perfmance-summary.png)

Track individual driver journeys:

1. **Select a Driver** from the sidebar dropdown
2. **Choose a Trip** to visualize the route
3. **View the Map** with:
   - Route geometry (orange line)
   - Pickup and dropoff locations (blue markers)
   - Current driver position (dark marker) controlled by a time slider

4. **Analyze Trip Details**:
   - Total distance traveled
   - Trip duration
   - Average speed
   - AI-generated trip summary using Cortex

![Individual Route Visualization](assets/individual-route.png)

### Fleet Heat Map Page

![Fleet Heat Map](assets/heatmap.png)

This page combines fleet statistics with an interactive density map.

**Top Section - Fleet Statistics:**
- **Top Streets** - Most popular pickup and dropoff locations
- **Route Distances** - Shortest and longest routes across all drivers

**Map Section - Driver Density:**

Use the sidebar controls to explore fleet distribution:

1. **Time Slice** - Select both **Hour** (0-23) and **Minute** (0-59) to see each driver's latest position at that moment
2. **Show Driver Locations** - Toggle clickable dots showing individual driver positions. Click a dot to display its route on the map
3. **H3 Resolution** - Adjust hexagon granularity (6-9) for density aggregation
4. **Colour Scheme** - Choose between "Contrast" and "Snowflake" palettes

**Analyze Patterns:**
- Peak hour driver concentrations via H3 hexagons
- Popular pickup/dropoff zones from the Top Streets charts
- Coverage gaps in the fleet

<!-- ------------------------ -->
## Understanding the Data Model

### Driver States

The simulation tracks realistic driver states throughout each trip:

| Point Index | State | Speed | Description |
|-------------|-------|-------|-------------|
| 0 | waiting | 0 km/h | Waiting for fare (2-8 min before trip) |
| 1 | pickup | 0 km/h | Passenger boarding |
| 2-12 | driving | Variable | En route with traffic simulation |
| 13 | dropoff | 0-3 km/h | Slowing for passenger exit |
| 14 | idle | 0 km/h | Brief idle after dropoff |

### Speed Distribution

Realistic traffic patterns are simulated:

| Speed Band | Percentage | Description |
|------------|------------|-------------|
| 0 km/h (Stationary) | ~23% | Waiting, pickup, dropoff, idle |
| 1-5 km/h (Crawling) | ~11% | Traffic jams, red lights |
| 6-15 km/h (Slow) | ~14% | Heavy traffic |
| 16-30 km/h (Moderate) | ~26% | Normal city driving |
| 31-45 km/h (Normal) | ~20% | Clear roads |
| 46+ km/h (Fast) | ~6% | Late night, highways |

### Shift Patterns

Drivers are distributed across 5 shifts for 24-hour coverage:

| Shift | Hours | % of Fleet | Coverage |
|-------|-------|------------|----------|
| Graveyard | 22:00-06:00 | 10% | Overnight |
| Early | 04:00-12:00 | 22.5% | Morning rush start |
| Morning | 06:00-14:00 | 27.5% | Full morning rush |
| Day | 11:00-19:00 | 22.5% | Midday + evening start |
| Evening | 15:00-23:00 | 17.5% | Evening rush |

<!-- ------------------------ -->
## Customize the Solution

### Change Number of Drivers

Edit the driver count in the shift patterns:

```sql
-- Default: 80 drivers total
SELECT 1 AS shift_id, 'Graveyard' AS shift_name, 22 AS shift_start, 6 AS shift_end, 8 AS driver_count UNION ALL
SELECT 2, 'Early', 4, 12, 18 UNION ALL
SELECT 3, 'Morning', 6, 14, 22 UNION ALL
SELECT 4, 'Day', 11, 19, 18 UNION ALL
SELECT 5, 'Evening', 15, 23, 14
```

### Change City

The solution comes pre-configured with 5 cities. Change the bounding box in the data generation:

| City | Longitude Range | Latitude Range |
|------|-----------------|----------------|
| San Francisco | -122.52 to -122.35 | 37.70 to 37.82 |
| New York City | -74.05 to -73.90 | 40.65 to 40.85 |
| London | -0.20 to 0.05 | 51.45 to 51.55 |
| Paris | 2.25 to 2.42 | 48.82 to 48.90 |
| Chicago | -87.75 to -87.55 | 41.80 to 41.95 |

You can also extend this to **any city worldwide** by adding a new entry to `city_config.py` with the city name, center coordinates, and zoom level, and providing a custom bounding box during data generation. See the [skill documentation](https://github.com/Snowflake-Labs/sfguide-Create-a-Route-Optimisation-and-Vehicle-Route-Plan-Simulator) for details on using custom locations.

> **_NOTE:_** When changing cities, ensure your OpenRouteService Native App has the corresponding map data installed. See the [Install OpenRouteService Native App](../oss-install-openrouteservice-native-app/) quickstart for location customization.

### Scaling Recommendations

| Drivers | Days | Est. Rows | Warehouse | Est. Time |
|---------|------|-----------|-----------|-----------|
| 20 | 1 | ~4K | SMALL | 2-3 min |
| 80 | 1 | ~18K | MEDIUM | 5-8 min |
| 80 | 7 | ~125K | LARGE | 20-30 min |
| 200 | 1 | ~45K | LARGE | 15-20 min |
| 200 | 7 | ~315K | XLARGE | 45-60 min |
| 500 | 7 | ~800K | XLARGE | 2-3 hours |

<!-- ------------------------ -->
## Generate Additional Data

### Regenerate Driver Locations

To regenerate driver location data with different parameters (e.g., more drivers, different city, more days), simply re-run the deploy skill in Cortex Code:

```
deploy fleet intelligence dashboard
```

The skill will prompt you for the new configuration and regenerate all data tables and routes.

<!-- ------------------------ -->
## Uninstall the Solution

To remove the Fleet Intelligence solution, ask Cortex Code to clean up the objects:

```
uninstall all objects created as part of the fleet intelligence skill
```

This will remove the `OPENROUTESERVICE_SETUP.FLEET_INTELLIGENCE_TAXIS` schema and its contents, and optionally remove the Overture Maps marketplace data and the warehouse.

> **_NOTE:_** The OpenRouteService Native App remains installed. You can uninstall it separately.

<!-- ------------------------ -->
## Available Cortex Code Skills

| Skill | Description | Command |
|-------|-------------|---------|
| `deploy-fleet-intelligence-taxis` | Deploy the full solution (data generation, routes, and Streamlit app) | `deploy fleet intelligence dashboard` |

<!-- ------------------------ -->
## Conclusion and Resources

### Conclusion

You've deployed a complete Fleet Intelligence Control Center that demonstrates:
- **OpenRouteService Native App** - Real road-following route generation
- **Carto Overture Maps** - Realistic city locations for simulation
- **Snowflake Cortex AI** - AI-powered trip summaries and analysis
- **Pydeck Visualization** - Interactive maps with multiple layer types
- **H3 Hexagons** - Spatial aggregation for density analysis

### What You Learned

- Deploy fleet analytics solutions using Cortex Code skills
- Generate simulated taxi fleet data with realistic patterns
- Track driver states and positions over time
- Build heat maps with H3 hexagon visualization
- Use AI for trip analysis and fleet insights

### Related Quickstarts

- [Install OpenRouteService Native App](/guide/oss-install-openrouteservice-native-app/) - Install the routing engine (prerequisite)
- [Deploy Route Optimization Demo](/guide/oss-deploy-route-optimization-demo/) - Build a delivery route optimization simulator

### Source Code

- [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-Create-a-Route-Optimisation-and-Vehicle-Route-Plan-Simulator) - Skills, scripts, and Streamlit apps

### OpenRouteService Resources

- [OpenRouteService Official Website](https://openrouteservice.org/) - Documentation and API reference
- [VROOM Project](https://github.com/VROOM-Project/vroom) - Vehicle Routing Open-source Optimization Machine

### Cortex Code & Snowflake

- [Snowflake Cortex](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview) - AI-powered features in Snowflake
- [Carto Overture Maps](https://www.carto.com/blog/overture-maps-data-in-snowflake) - POI and address data
- [H3 in Snowflake](https://docs.snowflake.com/en/sql-reference/functions/h3_latlng_to_cell) - Hexagonal hierarchical geospatial indexing
