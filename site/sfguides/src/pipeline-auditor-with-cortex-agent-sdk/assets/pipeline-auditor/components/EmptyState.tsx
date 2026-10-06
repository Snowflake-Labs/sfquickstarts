"use client";

import {
  Box,
  Typography,
  Stack,
  Paper,
  Chip,
  alpha,
  useTheme,
} from "@mui/material";
import {
  AccountTree as PipelineIcon,
  Search as SearchIcon,
  HealthAndSafety as HealthIcon,
  Speed as FreshnessIcon,
  AutoFixHigh as FixIcon,
} from "@mui/icons-material";

const FEATURES = [
  {
    icon: <SearchIcon sx={{ fontSize: 20 }} />,
    label: "Pipeline Discovery",
    description: "Tables, dynamic tables, tasks, streams, pipes, and procedures",
  },
  {
    icon: <FreshnessIcon sx={{ fontSize: 20 }} />,
    label: "Freshness Analysis",
    description: "Detect stale data and monitor table update frequency",
  },
  {
    icon: <HealthIcon sx={{ fontSize: 20 }} />,
    label: "Health Monitoring",
    description: "Dynamic table refresh failures, task errors, and scheduling issues",
  },
  {
    icon: <FixIcon sx={{ fontSize: 20 }} />,
    label: "AI-Powered Fixes",
    description: "Get remediation suggestions for identified issues",
  },
];

export function EmptyState() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        p: 4,
      }}
    >
      <Box
        sx={{
          width: 64,
          height: 64,
          borderRadius: "50%",
          bgcolor: alpha(theme.palette.primary.main, 0.1),
          border: `3px solid ${alpha(theme.palette.primary.main, 0.2)}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mb: 2,
        }}
      >
        <PipelineIcon sx={{ fontSize: 32, color: "primary.main" }} />
      </Box>

      <Typography
        variant="h5"
        sx={{
          fontWeight: 700,
          mb: 1,
          background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        Pipeline Auditor
      </Typography>

      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 2, maxWidth: 420, textAlign: "center" }}
      >
        Comprehensive audit of your Snowflake data pipelines powered by the
        Cortex Code Agent SDK.
      </Typography>

      {/* How to start — steps in a highlighted bar */}
      <Paper
        elevation={0}
        sx={{
          mb: 2,
          px: 2.5,
          py: 1,
          borderRadius: 2,
          bgcolor: "transparent",
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.22)}, ${alpha(theme.palette.secondary.main, 0.18)})`,
          border: `1px solid ${alpha(theme.palette.primary.main, 0.35)}`,
          width: "100%",
          maxWidth: 520,
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="center"
          spacing={1.5}
        >
          {["Select Database & Schema", "Select Scopes", "Run Audit"].map((step, i) => (
            <Stack key={i} direction="row" alignItems="center" spacing={1.5}>
              {i > 0 && (
                <Box
                  sx={{
                    width: 16,
                    height: 1,
                    bgcolor: alpha(theme.palette.primary.main, 0.3),
                  }}
                />
              )}
              <Chip
                label={`${i + 1}`}
                size="small"
                sx={{
                  width: 20,
                  height: 20,
                  fontSize: "0.65rem",
                  fontWeight: 700,
                  bgcolor: "primary.main",
                  color: "primary.contrastText",
                  "& .MuiChip-label": { px: 0 },
                }}
              />
              <Typography variant="body2" sx={{ fontWeight: 600, fontSize: "0.75rem", whiteSpace: "nowrap" }}>
                {step}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </Paper>

      {/* Feature highlights — non-clickable */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1,
          width: "100%",
          maxWidth: 520,
          mb: 1.5,
        }}
      >
        {FEATURES.map((feature) => (
          <Paper
            key={feature.label}
            elevation={0}
            sx={{
              p: 1.25,
              borderRadius: 2,
              bgcolor: alpha(theme.palette.primary.main, 0.04),
              border: `1px solid ${alpha(theme.palette.primary.main, 0.15)}`,
              display: "flex",
              alignItems: "flex-start",
              gap: 0.75,
            }}
          >
            <Box sx={{ color: "primary.main", mt: 0.25, flexShrink: 0 }}>{feature.icon}</Box>
            <Box>
              <Typography variant="caption" sx={{ fontWeight: 600, fontSize: "0.75rem", display: "block" }}>
                {feature.label}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem", lineHeight: 1.25 }}>
                {feature.description}
              </Typography>
            </Box>
          </Paper>
        ))}
      </Box>

      <Stack direction="row" spacing={1}>
        <Chip
          label="Read-only audit"
          size="small"
          variant="outlined"
          sx={{ fontSize: "0.65rem" }}
        />
        <Chip
          label="Cortex Code Agent SDK"
          size="small"
          variant="outlined"
          sx={{ fontSize: "0.65rem" }}
        />
        <Chip
          label="Structured output"
          size="small"
          variant="outlined"
          sx={{ fontSize: "0.65rem" }}
        />
      </Stack>
    </Box>
  );
}
