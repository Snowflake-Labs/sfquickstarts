"use client";

import {
  Box,
  Typography,
  Stack,
  Paper,
  alpha,
  useTheme,
  LinearProgress,
} from "@mui/material";
import {
  Code as CodeIcon,
} from "@mui/icons-material";
import type { ToolProgressEvent } from "@/lib/types";

interface ToolProgressProps {
  toolProgress: ToolProgressEvent[];
  isLoading: boolean;
}

export function ToolProgress({ toolProgress, isLoading }: ToolProgressProps) {
  const theme = useTheme();

  if (toolProgress.length === 0 && !isLoading) return null;

  const lastFive = toolProgress.slice(-5);

  return (
    <Paper
      elevation={0}
      sx={{
        mx: 2,
        mb: 1,
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.primary.main, 0.03),
        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <CodeIcon sx={{ fontSize: 16, color: "primary.main" }} />
        <Typography
          variant="caption"
          sx={{ fontWeight: 600, color: "primary.main" }}
        >
          Tool Calls ({toolProgress.length})
        </Typography>
      </Stack>
      {isLoading && <LinearProgress sx={{ mb: 1, borderRadius: 1 }} />}
      <Stack spacing={0.5}>
        {lastFive.map((tp, i) => (
          <Typography
            key={i}
            variant="caption"
            sx={{
              color: "text.secondary",
              fontFamily: '"Fira Code", monospace',
              fontSize: "0.65rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            [{tp.elapsed}s] #{tp.count} {tp.toolName}
            {tp.sqlPreview ? ` — ${tp.sqlPreview}` : ""}
          </Typography>
        ))}
      </Stack>
    </Paper>
  );
}
