// Quickstart: Snowflake + Iceberg Interoperability — SSV2 Weather Ingest
// Calls the Open-Meteo historical API for NYC airports and streams each response
// as a row into a Snowflake Iceberg V3 VARIANT table via Snowpipe Streaming V2
// (rowset / in-memory mode).
//
// Modes:
//   LIVE_MODE = true  → streams Q1 2025 data (9 rows) as an additional batch
//   SKIP_ARCHIVE = false (default) → streams 2024 full-year archive data (36 rows) first
//
//   Recommended workflow:
//     First run:   SKIP_ARCHIVE=false, LIVE_MODE=false → loads 36 archive rows
//     Second run:  SKIP_ARCHIVE=true,  LIVE_MODE=true  → streams 9 Q1 2025 rows (you will see the count grow)
//     One-shot:    SKIP_ARCHIVE=false, LIVE_MODE=true  → loads 36 + 9 = 45 rows in one shot
//
// Prerequisites:
//   1. Copy profile.json.example → profile.json and fill in your account details.
//      See README.md "Setup: profile.json" for field-by-field instructions.
//   2. Run scripts/02_ssv2_streaming_setup.sql to create the table and pipe.
//   3. Update DATABASE, SCHEMA, PIPE constants below if using different names.
//
// Run: mvn package && mvn exec:java -Dexec.mainClass="com.snowflake.snowpipestreaming.demo.SSV2WeatherIngest"
package com.snowflake.snowpipestreaming.demo;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.snowflake.ingest.streaming.SnowflakeStreamingIngestChannel;
import com.snowflake.ingest.streaming.SnowflakeStreamingIngestClient;
import com.snowflake.ingest.streaming.SnowflakeStreamingIngestClientFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

public class SSV2WeatherIngest {

    private static final Logger logger = LoggerFactory.getLogger(SSV2WeatherIngest.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    // --- Configuration flags ---
    // LIVE_MODE: when true, streams Q1 2025 data (9 rows) after the archive batch
    private static final boolean LIVE_MODE    = false;
    // SKIP_ARCHIVE: when true, skips the 2024 archive batch (use when archive is pre-loaded)
    private static final boolean SKIP_ARCHIVE = false;

    // Snowflake connection config
    private static final String PROFILE_PATH = "profile.json";
    private static final String DATABASE = "ICEBERG_DEMO"; // e.g. ICEBERG_DEMO
    private static final String SCHEMA   = "PUBLIC"; // e.g. PUBLIC
    private static final String PIPE     = "nyc_weather_ssv2_pipe"; // e.g. nyc_weather_ssv2_pipe

    // Open-Meteo archive API
    private static final String BASE_URL = "https://archive-api.open-meteo.com/v1/archive";
    private static final String WEATHER_VARIABLES =
            "temperature_2m,apparent_temperature,precipitation," +
            "weathercode,windspeed_10m,winddirection_10m," +
            "relativehumidity_2m,snowfall,cloud_cover";

    // Archive batch: 2024 full year (3 airports × 12 months = 36 rows)
    private static final int ARCHIVE_YEAR        = 2024;
    private static final int ARCHIVE_START_MONTH = 1;
    private static final int ARCHIVE_END_MONTH   = 12;

    // Live batch: Q1 2025 (3 airports × 3 months = 9 rows)
    private static final int LIVE_YEAR        = 2025;
    private static final int LIVE_START_MONTH = 1;
    private static final int LIVE_END_MONTH   = 3;

    // Three NYC-area airports used throughout this quickstart
    private static final List<Map<String, Object>> AIRPORTS = List.of(
        Map.of("name", "JFK", "lat", 40.6413, "lon", -73.7781),
        Map.of("name", "LGA", "lat", 40.7773, "lon", -73.8740),
        Map.of("name", "EWR", "lat", 40.6895, "lon", -74.1745)
    );

    private static final int POLL_ATTEMPTS     = 60;
    private static final long POLL_INTERVAL_MS = TimeUnit.SECONDS.toMillis(2);

    /**
     * Entry point: fetches Open-Meteo data and streams rows through an SSV2 channel.
     * Behaviour depends on SKIP_ARCHIVE and LIVE_MODE flags — see class header.
     */
    public static void main(String[] args) throws Exception {
        // --- Collect rows to stream ---
        List<Map<String, Object>> allRows = new ArrayList<>();

        if (!SKIP_ARCHIVE) {
            logger.info("Archive batch: fetching {} airports × {} months of {}",
                    AIRPORTS.size(), ARCHIVE_END_MONTH - ARCHIVE_START_MONTH + 1, ARCHIVE_YEAR);
            List<Map<String, Object>> archiveRows =
                    fetchWeatherRows(ARCHIVE_YEAR, ARCHIVE_START_MONTH, ARCHIVE_END_MONTH);
            allRows.addAll(archiveRows);
            logger.info("Archive batch: {} rows fetched from Open-Meteo", archiveRows.size());
        } else {
            logger.info("SKIP_ARCHIVE=true — skipping 2024 archive batch (assumes pre-loaded)");
            System.out.println("Skipping archive batch — table should already have 36 rows.");
        }

        if (LIVE_MODE) {
            logger.info("Live batch: fetching {} airports × {} months of {} (Q1)",
                    AIRPORTS.size(), LIVE_END_MONTH - LIVE_START_MONTH + 1, LIVE_YEAR);
            List<Map<String, Object>> liveRows =
                    fetchWeatherRows(LIVE_YEAR, LIVE_START_MONTH, LIVE_END_MONTH);
            allRows.addAll(liveRows);
            logger.info("Live batch: {} rows fetched from Open-Meteo", liveRows.size());
        }

        if (allRows.isEmpty()) {
            logger.warn("No rows to stream (SKIP_ARCHIVE=true and LIVE_MODE=false). Exiting.");
            System.out.println("Nothing to stream. Set LIVE_MODE=true or SKIP_ARCHIVE=false.");
            return;
        }

        int totalRows = allRows.size();
        logger.info("Total rows to stream: {}", totalRows);

        // --- Load Snowflake credentials from profile.json ---
        Properties props = new Properties();
        JsonNode jsonNode = MAPPER.readTree(Files.readAllBytes(Paths.get(PROFILE_PATH)));
        jsonNode.fields().forEachRemaining(e -> props.put(e.getKey(), e.getValue().asText()));

        // --- Create SSV2 streaming ingest client (targets a pipe, not a table) ---
        // SSV2 client targets a pipe (not a table). The SDK writes Map<String,Object> directly as VARIANT.
        String clientName = "SSV2_INGEST_" + UUID.randomUUID();
        SnowflakeStreamingIngestClient client = SnowflakeStreamingIngestClientFactory
                .builder(clientName, DATABASE, SCHEMA, PIPE)
                .setProperties(props)
                .build();

        // --- Open a streaming channel ---
        // One channel per streaming session. Channel name is unique to avoid conflicts with concurrent writers.
        String channelName = "INGEST_CHANNEL_" + UUID.randomUUID();
        SnowflakeStreamingIngestChannel channel = client.openChannel(channelName, "0").getChannel();
        logger.info("SSV2 channel opened: {}", channelName);

        // --- Stream all rows via appendRow ---
        for (int i = 0; i < totalRows; i++) {
            // Each row is a Map matching the pipe's column order. SDK batches rows and writes Parquet micro-batches.
            channel.appendRow(allRows.get(i), String.valueOf(i + 1));
        }

        if (!SKIP_ARCHIVE && LIVE_MODE) {
            int archiveCount = (ARCHIVE_END_MONTH - ARCHIVE_START_MONTH + 1) * AIRPORTS.size();
            int liveCount = totalRows - archiveCount;
            System.out.println("Streamed " + archiveCount + " archive rows + "
                    + liveCount + " live rows = " + totalRows + " total.");
        } else {
            System.out.println("Streamed " + totalRows + " rows.");
        }
        logger.info("Streamed {} rows — polling for commit confirmation", totalRows);

        // --- Poll until Snowflake confirms all rows committed ---
        // Poll until Snowflake confirms all rows committed. The offset token is the durable commit guarantee.
        String expectedOffset = String.valueOf(totalRows);
        boolean committed = false;
        for (int attempt = 1; attempt <= POLL_ATTEMPTS; attempt++) {
            String latest = channel.getChannelStatus().getLatestOffsetToken();
            logger.debug("Poll {}/{} — latest offset: {}", attempt, POLL_ATTEMPTS, latest);

            if (expectedOffset.equals(latest)) {
                committed = true;
                break;
            }
            Thread.sleep(POLL_INTERVAL_MS);
        }

        // --- Clean up ---
        channel.close();
        client.close();

        if (committed) {
            if (SKIP_ARCHIVE && LIVE_MODE) {
                int liveCount = (LIVE_END_MONTH - LIVE_START_MONTH + 1) * AIRPORTS.size();
                int expectedTotal = ((ARCHIVE_END_MONTH - ARCHIVE_START_MONTH + 1) * AIRPORTS.size()) + liveCount;
                logger.info("Live batch committed: {} new rows. Expected table total: {}", liveCount, expectedTotal);
                System.out.println("Live batch: " + liveCount + " rows committed. Expected total in table: " + expectedTotal + ".");
            } else {
                logger.info("All {} rows committed to nyc_weather_ssv2", totalRows);
                System.out.println("All " + totalRows + " rows committed to nyc_weather_ssv2.");
            }
        } else {
            logger.error("Commit confirmation timed out after {} attempts", POLL_ATTEMPTS);
            System.err.println("Timed out waiting for commit. Check Snowflake table for partial data.");
            System.exit(1);
        }
    }

    /**
     * Calls the Open-Meteo archive API for each airport × month in the given range.
     * Returns row maps ready for appendRow() — one per airport per month.
     * The JSON response is parsed into a Map so the SDK writes it directly as VARIANT — no PARSE_JSON needed.
     *
     * @param year       Calendar year to fetch
     * @param startMonth First month (inclusive, 1-based)
     * @param endMonth   Last month (inclusive, 1-based)
     * @return List of row maps matching the pipe's column order
     */
    private static List<Map<String, Object>> fetchWeatherRows(int year, int startMonth, int endMonth)
            throws Exception {
        HttpClient http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .build();

        List<Map<String, Object>> rows = new ArrayList<>();

        for (int month = startMonth; month <= endMonth; month++) {
            YearMonth ym = YearMonth.of(year, month);
            String startDate = String.format("%d-%02d-01", year, month);
            String endDate   = String.format("%d-%02d-%02d", year, month, ym.lengthOfMonth());

            for (Map<String, Object> airport : AIRPORTS) {
                String name = (String) airport.get("name");
                double lat  = (double) airport.get("lat");
                double lon  = (double) airport.get("lon");

                String url = BASE_URL
                        + "?latitude="   + lat
                        + "&longitude="  + lon
                        + "&start_date=" + startDate
                        + "&end_date="   + endDate
                        + "&hourly="     + WEATHER_VARIABLES
                        + "&timezone=America%2FNew_York";

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .timeout(Duration.ofSeconds(30))
                        .GET()
                        .build();

                HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() != 200) {
                    throw new RuntimeException(
                        "Open-Meteo API returned HTTP " + response.statusCode()
                        + " for " + name + " " + startDate);
                }

                @SuppressWarnings("unchecked")
                Map<String, Object> parsedResponse = MAPPER.readValue(response.body(), Map.class);

                Map<String, Object> row = new HashMap<>();
                row.put("location",     name);
                row.put("latitude",     lat);
                row.put("longitude",    lon);
                row.put("weather_data", parsedResponse);
                row.put("ingested_at",  Instant.now().toString());
                rows.add(row);

                logger.info("Fetched {} {} → {}", name, startDate, endDate);
            }
        }
        return rows;
    }
}
