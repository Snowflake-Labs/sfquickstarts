# Assets for Kafka Connector Quickstart

This directory contains screenshots and images for the Getting Started with Openflow Kafka Connector quickstart.

## Required Screenshots

The following screenshots should be added during testing/validation:

1. **openflow_kafka_canvas.png** - Screenshot of Openflow Canvas showing:
   - ConsumeKafka processor configured
   - PutSnowflake processor configured
   - Connection between processors
   - Processors in running state

2. **kafka_connector_config.png** - Screenshot showing:
   - ConsumeKafka processor configuration panel
   - Key properties (brokers, topic, security protocol)

3. **snowflake_logs_table.png** - Screenshot of:
   - Query results showing log data in APPLICATION_LOGS table
   - Sample records with RECORD_METADATA and RECORD_CONTENT

4. **analytics_dashboard.png** (optional) - Screenshot showing:
   - Results of analytics queries
   - Log level distribution chart
   - Error rate timeline

5. **openflow_monitoring.png** - Screenshot showing:
   - Processor statistics
   - Data flow metrics
   - Queue status

## Image Guidelines

- **Format**: PNG preferred (GIF for animations)
- **Resolution**: 1920x1080 or similar (high DPI for clarity)
- **File Size**: Optimize images to < 500KB when possible
- **Naming**: Use descriptive, lowercase names with underscores
- **Content**: Blur any sensitive information (account IDs, passwords, IPs)

## Adding Images to Quickstart

To reference images in the quickstart markdown, use:

```markdown
![Description](assets/image_name.png)
```

Or for animated GIFs:

```markdown
![Process Description](assets/animation_name.gif)
```

## Placeholder

This README serves as a placeholder until actual screenshots are captured during quickstart testing and validation.
