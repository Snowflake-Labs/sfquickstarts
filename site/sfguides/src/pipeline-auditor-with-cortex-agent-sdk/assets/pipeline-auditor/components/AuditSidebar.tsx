"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import {
  Box,
  Typography,
  Stack,
  Paper,
  Chip,
  alpha,
  useTheme,
  Divider,
  type Theme,
} from "@mui/material";
import {
  Storage as SqlIcon,
  Search as SearchIcon,
  Description as FileIcon,
  CheckCircleOutline as DoneIcon,
  RadioButtonUnchecked as PendingIcon,
  FiberManualRecord as ActiveIcon,
} from "@mui/icons-material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import type { AuditReport, ToolProgressEvent } from "@/lib/types";

// Theme-aware scrollbar styles matching ChatThread
function getScrollbarSx(theme: Theme) {
  const thumb = alpha(theme.palette.text.primary, 0.1);
  const thumbHover = alpha(theme.palette.text.primary, 0.2);
  return {
    "&::-webkit-scrollbar": { width: 6 },
    "&::-webkit-scrollbar-track": { bgcolor: "transparent" },
    "&::-webkit-scrollbar-thumb": {
      bgcolor: thumb,
      borderRadius: 3,
      "&:hover": { bgcolor: thumbHover },
    },
    scrollbarWidth: "thin" as const,
    scrollbarColor: `${thumb} transparent`,
  };
}

interface AuditSidebarProps {
  toolProgress: ToolProgressEvent[];
  report: AuditReport | null;
  stats: { durationMs: number; numTurns: number; toolCalls: number } | null;
  isLoading: boolean;
}

export function AuditSidebar({
  toolProgress,
  report,
  stats,
  isLoading,
}: AuditSidebarProps) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        width: 400,
        flexShrink: 0,
        borderLeft: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
        overflow: "auto",
        p: 2,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        ...getScrollbarSx(theme),
      }}
    >
      {/* Header */}
      <Typography
        variant="overline"
        sx={{ color: "text.secondary", letterSpacing: 1.5, fontSize: "0.65rem" }}
      >
        Live Audit Metrics
      </Typography>

      {/* Live stats — visible during and after audit */}
      <LiveStats toolProgress={toolProgress} isLoading={isLoading} />

      {/* Tool call waterfall — real-time */}
      {toolProgress.length > 0 && (
        <ToolWaterfall toolProgress={toolProgress} isLoading={isLoading} />
      )}

      {/* After audit: report charts — appear instantly when report arrives */}
      {report && (
        <Box sx={{ animation: "fadeSlideIn 0.4s ease-out", "@keyframes fadeSlideIn": { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } } }}>
          <FindingsDonut report={report} />
        </Box>
      )}
      {report && (
        <Box sx={{ animation: "fadeSlideIn 0.5s ease-out" }}>
          <CategoryBreakdown report={report} />
        </Box>
      )}
      {report && (
        <Box sx={{ animation: "fadeSlideIn 0.6s ease-out" }}>
          <InventoryStats report={report} />
        </Box>
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Audit Phase — infer current phase from tool call content
// ---------------------------------------------------------------------------
const PHASES = [
  { key: "discovery", label: "Discovery", patterns: ["INFORMATION_SCHEMA", "SHOW SCHEMAS", "SHOW DYNAMIC", "SHOW TASKS", "SHOW INTERACTIVE"] },
  { key: "freshness", label: "Freshness", patterns: ["last_altered", "freshness", "DATEDIFF", "hours_since"] },
  { key: "dt_health", label: "DT Health", patterns: ["DYNAMIC_TABLE", "refresh_history", "REFRESH_HISTORY", "scheduling_state"] },
  { key: "tasks", label: "Tasks", patterns: ["TASK_HISTORY", "task_history", "SHOW TASKS"] },
  { key: "report", label: "Report", patterns: [] },
] as const;

export function AuditPhase({ toolProgress, isLoading }: { toolProgress: ToolProgressEvent[]; isLoading: boolean }) {
  const theme = useTheme();

  const currentPhaseIndex = useMemo(() => {
    if (!isLoading && toolProgress.length > 0) return PHASES.length - 1; // report
    // Check last few tool calls to determine phase
    const recent = toolProgress.slice(-3);
    for (let p = PHASES.length - 2; p >= 0; p--) {
      const phase = PHASES[p];
      if (phase.patterns.length === 0) continue;
      for (const tp of recent) {
        const text = `${tp.sqlPreview || ""} ${tp.description || ""}`.toUpperCase();
        if (phase.patterns.some((pat) => text.includes(pat.toUpperCase()))) return p;
      }
    }
    // Default: check all tool calls for highest phase reached
    for (let p = PHASES.length - 2; p >= 0; p--) {
      const phase = PHASES[p];
      if (phase.patterns.length === 0) continue;
      for (const tp of toolProgress) {
        const text = `${tp.sqlPreview || ""} ${tp.description || ""}`.toUpperCase();
        if (phase.patterns.some((pat) => text.includes(pat.toUpperCase()))) return p;
      }
    }
    return toolProgress.length > 0 ? 0 : -1;
  }, [toolProgress, isLoading]);

  if (currentPhaseIndex < 0) return null;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
      }}
    >
      <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap" useFlexGap>
        {PHASES.map((phase, i) => {
          const isDone = i < currentPhaseIndex;
          const isActive = i === currentPhaseIndex;
          return (
            <Stack key={phase.key} direction="row" alignItems="center" spacing={0.25}>
              {i > 0 && (
                <Box
                  sx={{
                    width: 12,
                    height: 1,
                    bgcolor: isDone
                      ? theme.palette.primary.main
                      : alpha(theme.palette.divider, 0.3),
                  }}
                />
              )}
              <Chip
                icon={
                  isDone ? (
                    <DoneIcon sx={{ fontSize: "14px !important" }} />
                  ) : isActive ? (
                    <ActiveIcon sx={{ fontSize: "8px !important", animation: "pulse 1.5s infinite", "@keyframes pulse": { "0%, 100%": { opacity: 1 }, "50%": { opacity: 0.4 } } }} />
                  ) : (
                    <PendingIcon sx={{ fontSize: "14px !important" }} />
                  )
                }
                label={phase.label}
                size="small"
                sx={{
                  fontSize: "0.6rem",
                  height: 22,
                  fontWeight: isActive ? 700 : 400,
                  bgcolor: isActive
                    ? alpha(theme.palette.primary.main, 0.12)
                    : isDone
                    ? alpha(theme.palette.primary.main, 0.05)
                    : "transparent",
                  color: isActive
                    ? theme.palette.primary.main
                    : isDone
                    ? theme.palette.text.primary
                    : theme.palette.text.disabled,
                  border: isActive
                    ? `1px solid ${alpha(theme.palette.primary.main, 0.3)}`
                    : `1px solid ${alpha(theme.palette.divider, 0.15)}`,
                  "& .MuiChip-icon": {
                    color: isActive
                      ? theme.palette.primary.main
                      : isDone
                      ? theme.palette.primary.main
                      : theme.palette.text.disabled,
                  },
                }}
              />
            </Stack>
          );
        })}
      </Stack>
    </Paper>
  );
}

// ---------------------------------------------------------------------------
// Activity Feed — live log of tool calls with details
// ---------------------------------------------------------------------------
export function ActivityFeed({ toolProgress, isLoading }: { toolProgress: ToolProgressEvent[]; isLoading: boolean }) {
  const theme = useTheme();
  const feedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (feedRef.current && isLoading) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [toolProgress.length, isLoading]);

  const getIcon = (toolName: string) => {
    if (toolName === "sql_execute") return <SqlIcon sx={{ fontSize: 14, color: theme.palette.primary.main }} />;
    if (toolName === "read") return <FileIcon sx={{ fontSize: 14, color: theme.palette.secondary.main }} />;
    return <SearchIcon sx={{ fontSize: 14, color: theme.palette.text.secondary }} />;
  };

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        overflow: "hidden",
      }}
    >
      <Box sx={{ px: 1.5, pt: 1.5, pb: 0.5 }}>
        <Typography
          variant="caption"
          sx={{ fontWeight: 600, color: "text.secondary" }}
        >
          Activity Log ({toolProgress.length})
        </Typography>
      </Box>
      <Box
        ref={feedRef}
        sx={{
          px: 1,
          pb: 1,
        }}
      >
        <Stack spacing={0.5}>
          {toolProgress.map((tp, i) => (
            <Box
              key={i}
              sx={{
                px: 1,
                py: 0.5,
                borderRadius: 1,
                bgcolor: alpha(
                  tp.toolName === "sql_execute"
                    ? theme.palette.primary.main
                    : theme.palette.secondary.main,
                  0.04
                ),
                border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                animation: i === toolProgress.length - 1 && isLoading ? "fadeIn 0.3s ease-out" : undefined,
                "@keyframes fadeIn": { from: { opacity: 0, transform: "translateY(4px)" }, to: { opacity: 1, transform: "translateY(0)" } },
              }}
            >
              <Stack direction="row" alignItems="center" spacing={0.75}>
                {getIcon(tp.toolName)}
                <Typography
                  variant="caption"
                  sx={{
                    flex: 1,
                    fontWeight: 500,
                    fontSize: "0.75rem",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {tp.description || tp.toolName}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: "0.7rem",
                    color: "text.disabled",
                    fontFamily: '"Fira Code", monospace',
                    flexShrink: 0,
                  }}
                >
                  {tp.elapsed}s
                </Typography>
              </Stack>
              {tp.sqlPreview && (
                <Typography
                  variant="caption"
                  sx={{
                    display: "block",
                    mt: 0.25,
                    fontSize: "0.65rem",
                    fontFamily: '"Fira Code", monospace',
                    color: "text.disabled",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    pl: 2.5,
                  }}
                >
                  {tp.sqlPreview}
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </Box>
    </Paper>
  );
}

// ---------------------------------------------------------------------------
// Live Stats — elapsed timer + tool count
// ---------------------------------------------------------------------------
function LiveStats({ toolProgress, isLoading }: { toolProgress: ToolProgressEvent[]; isLoading: boolean }) {
  const theme = useTheme();
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());
  const frozenRef = useRef<number | null>(null);

  useEffect(() => {
    if (isLoading) {
      startRef.current = Date.now();
      frozenRef.current = null;
      const interval = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      // Freeze at final value
      if (frozenRef.current === null) {
        frozenRef.current = Math.floor((Date.now() - startRef.current) / 1000);
        setElapsed(frozenRef.current);
      }
    }
  }, [isLoading]);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <Stack direction="row" spacing={2}>
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          p: 1.5,
          borderRadius: 1.5,
          bgcolor: alpha(theme.palette.primary.main, 0.05),
          border: `1px solid ${alpha(theme.palette.primary.main, 0.15)}`,
          textAlign: "center",
        }}
      >
        <Typography
          variant="h5"
          sx={{
            fontFamily: '"Fira Code", monospace',
            fontWeight: 700,
            color: "primary.main",
          }}
        >
          {minutes}:{seconds.toString().padStart(2, "0")}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.6rem" }}>
          ELAPSED
        </Typography>
      </Paper>
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          p: 1.5,
          borderRadius: 1.5,
          bgcolor: alpha(theme.palette.secondary.main, 0.05),
          border: `1px solid ${alpha(theme.palette.secondary.main, 0.15)}`,
          textAlign: "center",
        }}
      >
        <Typography
          variant="h5"
          sx={{ fontWeight: 700, color: "secondary.main" }}
        >
          {toolProgress.length}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.6rem" }}>
          TOOL CALLS
        </Typography>
      </Paper>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tool call waterfall — horizontal bars showing per-call duration
// ---------------------------------------------------------------------------
function ToolWaterfall({
  toolProgress,
  isLoading,
}: {
  toolProgress: ToolProgressEvent[];
  isLoading: boolean;
}) {
  const theme = useTheme();

  // Compute individual duration for each call (delta from previous)
  const data = toolProgress.map((tp, i) => {
    const prevElapsed = i > 0 ? toolProgress[i - 1].elapsed : 0;
    const duration = Math.max(0.1, tp.elapsed - prevElapsed);
    return {
      name: `#${tp.count}`,
      tool: tp.toolName.replace("sql_execute", "SQL"),
      duration: Number(duration.toFixed(1)),
      description: tp.description || tp.toolName,
      sqlPreview: tp.sqlPreview || "",
      fill:
        tp.toolName === "sql_execute"
          ? theme.palette.primary.main
          : theme.palette.secondary.main,
    };
  });

  // Show last 15 calls
  const visible = data.slice(-15);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
      }}
    >
      <Typography
        variant="caption"
        sx={{ fontWeight: 600, color: "text.secondary", mb: 1, display: "block" }}
      >
        Tool Call Timeline {isLoading && "(live)"}
      </Typography>
      <ResponsiveContainer width="100%" height={Math.max(120, visible.length * 20)}>
        <BarChart data={visible} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
          <XAxis
            type="number"
            tick={{ fontSize: 9, fill: theme.palette.text.secondary }}
            tickFormatter={(v) => `${v}s`}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 9, fill: theme.palette.text.secondary }}
            width={30}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null;
              const d = payload[0].payload;
              return (
                <Box
                  sx={{
                    bgcolor: theme.palette.background.paper,
                    border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                    borderRadius: 1.5,
                    px: 1.5,
                    py: 1,
                    maxWidth: 220,
                  }}
                >
                  <Stack direction="row" alignItems="center" spacing={0.75} sx={{ mb: 0.5 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        bgcolor: d.fill,
                        flexShrink: 0,
                      }}
                    />
                    <Typography variant="caption" sx={{ fontWeight: 700, fontSize: "0.7rem" }}>
                      {d.name} &middot; {d.tool}
                    </Typography>
                  </Stack>
                  <Typography variant="caption" sx={{ display: "block", fontSize: "0.65rem", color: "text.secondary", whiteSpace: "normal", wordBreak: "break-word" }}>
                    {d.description}
                  </Typography>
                  <Typography variant="caption" sx={{ display: "block", fontSize: "0.7rem", fontWeight: 600, mt: 0.5, color: d.fill }}>
                    {d.duration}s
                  </Typography>
                  {d.sqlPreview && (
                    <Typography
                      variant="caption"
                      sx={{
                        display: "block",
                        mt: 0.5,
                        fontSize: "0.6rem",
                        fontFamily: '"Fira Code", monospace',
                        color: "text.disabled",
                        whiteSpace: "normal",
                        wordBreak: "break-all",
                        lineHeight: 1.4,
                      }}
                    >
                      {d.sqlPreview}
                    </Typography>
                  )}
                </Box>
              );
            }}
            cursor={{ fill: alpha(theme.palette.primary.main, 0.08) }}
          />
          <Bar dataKey="duration" radius={[0, 4, 4, 0]} maxBarSize={14}>
            {visible.map((entry, i) => (
              <Cell key={i} fill={entry.fill} fillOpacity={0.7} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}

// ---------------------------------------------------------------------------
// Findings donut — severity breakdown
// ---------------------------------------------------------------------------
function FindingsDonut({ report }: { report: AuditReport }) {
  const theme = useTheme();
  const data = [
    { name: "Critical", value: report.summary.critical, color: "#f44336" },
    { name: "Warning", value: report.summary.warning, color: "#ff9800" },
    { name: "Info", value: report.summary.info, color: theme.palette.primary.main },
  ].filter((d) => d.value > 0);

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
      }}
    >
      <Typography
        variant="caption"
        sx={{ fontWeight: 600, color: "text.secondary", mb: 0.5, display: "block" }}
      >
        Findings by Severity
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center" }}>
        <ResponsiveContainer width={120} height={120}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={30}
              outerRadius={50}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} fillOpacity={0.8} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload[0]) return null;
                const d = payload[0].payload;
                const pct = total > 0 ? ((d.value / total) * 100).toFixed(0) : "0";
                return (
                  <Box
                    sx={{
                      bgcolor: theme.palette.background.paper,
                      border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                      borderRadius: 1.5,
                      px: 1.5,
                      py: 1,
                    }}
                  >
                    <Stack direction="row" alignItems="center" spacing={0.75}>
                      <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: d.color, flexShrink: 0 }} />
                      <Typography variant="caption" sx={{ fontWeight: 700, fontSize: "0.7rem" }}>
                        {d.name}
                      </Typography>
                    </Stack>
                    <Typography variant="caption" sx={{ display: "block", fontSize: "0.7rem", fontWeight: 600, mt: 0.5, color: d.color }}>
                      {d.value} finding{d.value !== 1 ? "s" : ""} ({pct}%)
                    </Typography>
                  </Box>
                );
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <Stack spacing={0.5} sx={{ ml: 1 }}>
          {data.map((d) => (
            <Stack key={d.name} direction="row" alignItems="center" spacing={0.75}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  bgcolor: d.color,
                  flexShrink: 0,
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
                {d.name}
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 600, fontSize: "0.65rem" }}>
                {d.value}
              </Typography>
            </Stack>
          ))}
          <Divider sx={{ my: 0.25 }} />
          <Typography variant="caption" sx={{ fontWeight: 600, fontSize: "0.65rem" }}>
            {total} total
          </Typography>
        </Stack>
      </Box>
    </Paper>
  );
}

// ---------------------------------------------------------------------------
// Category breakdown — horizontal bar chart
// ---------------------------------------------------------------------------
function CategoryBreakdown({ report }: { report: AuditReport }) {
  const theme = useTheme();

  // Count findings per category
  const counts: Record<string, number> = {};
  for (const f of report.findings) {
    counts[f.category] = (counts[f.category] || 0) + 1;
  }

  const data = Object.entries(counts)
    .map(([category, count]) => ({
      category: category.replace("_", " "),
      count,
    }))
    .sort((a, b) => b.count - a.count);

  if (data.length === 0) return null;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
      }}
    >
      <Typography
        variant="caption"
        sx={{ fontWeight: 600, color: "text.secondary", mb: 1, display: "block" }}
      >
        Findings by Category
      </Typography>
      <ResponsiveContainer width="100%" height={data.length * 28 + 10}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
          <XAxis
            type="number"
            tick={{ fontSize: 9, fill: theme.palette.text.secondary }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fontSize: 9, fill: theme.palette.text.secondary }}
            width={75}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null;
              const d = payload[0].payload;
              return (
                <Box
                  sx={{
                    bgcolor: theme.palette.background.paper,
                    border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                    borderRadius: 1.5,
                    px: 1.5,
                    py: 1,
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: 700, fontSize: "0.7rem", textTransform: "capitalize" }}>
                    {d.category}
                  </Typography>
                  <Typography variant="caption" sx={{ display: "block", fontSize: "0.7rem", fontWeight: 600, mt: 0.5, color: theme.palette.primary.main }}>
                    {d.count} finding{d.count !== 1 ? "s" : ""}
                  </Typography>
                </Box>
              );
            }}
            cursor={{ fill: alpha(theme.palette.primary.main, 0.08) }}
          />
          <Bar
            dataKey="count"
            fill={theme.palette.primary.main}
            fillOpacity={0.6}
            radius={[0, 4, 4, 0]}
            maxBarSize={16}
          />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}

// ---------------------------------------------------------------------------
// Inventory stats — compact cards
// ---------------------------------------------------------------------------
function InventoryStats({ report }: { report: AuditReport }) {
  const theme = useTheme();
  const inv = report.pipeline_inventory;

  const items = [
    { label: "Schemas", value: inv.schemas.length, color: theme.palette.primary.main },
    { label: "Tables", value: inv.tables.length, color: theme.palette.primary.main },
    { label: "Dynamic Tables", value: inv.dynamic_tables.length, color: theme.palette.secondary.main },
    { label: "Tasks", value: inv.tasks.length, color: "#ff9800" },
    { label: "Views", value: inv.views.length, color: theme.palette.text.secondary },
  ];

  return (
    <Paper
      elevation={0}
      sx={{
        p: 1.5,
        borderRadius: 1.5,
        bgcolor: alpha(theme.palette.grey[500], 0.04),
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
      }}
    >
      <Typography
        variant="caption"
        sx={{ fontWeight: 600, color: "text.secondary", mb: 1, display: "block" }}
      >
        Pipeline Inventory
      </Typography>
      <Stack spacing={0.75}>
        {items.map((item) => (
          <Stack key={item.label} direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
              {item.label}
            </Typography>
            <Typography
              variant="caption"
              sx={{ fontWeight: 700, fontSize: "0.75rem", color: item.color }}
            >
              {item.value}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
}
