"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  AppBar,
  Box,
  CircularProgress,
  Dialog,
  IconButton,
  Paper,
  Toolbar,
  Typography,
  Stack,
  Chip,
  alpha,
  useTheme,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Button,
  Tooltip,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Inventory as InventoryIcon,
  BugReport as FindingsIcon,
  AutoFixHigh as FixIcon,
  Close as CloseIcon,
  ContentCopy as CopyIcon,
  PlayArrow as RunIcon,
  Person as UserIcon,
  SmartToy as BotIcon,
} from "@mui/icons-material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Theme } from "@mui/material";
import type { AuditReport, Finding, Severity, OverallHealth } from "@/lib/types";
import type { SuggestFixState, FixMessage } from "@/hooks/useSuggestFix";
import { ChatInput } from "@/components/ChatInput";

interface ReportPanelProps {
  report: AuditReport;
  onSuggestFix?: (index: number, finding: Finding) => void;
  onDismissFix?: () => void;
  onSendFollowUp?: (message: string) => void;
  fixState?: SuggestFixState;
  canExecute?: boolean;
}

const severityColor: Record<Severity, string> = {
  critical: "#f44336",
  warning: "#ff9800",
  info: "#2196f3",
};

const severityIcon: Record<Severity, React.ReactNode> = {
  critical: <ErrorIcon sx={{ fontSize: 16 }} />,
  warning: <WarningIcon sx={{ fontSize: 16 }} />,
  info: <InfoIcon sx={{ fontSize: 16 }} />,
};

const healthConfig: Record<
  OverallHealth,
  { color: string; label: string; icon: React.ReactNode }
> = {
  healthy: {
    color: "#4caf50",
    label: "HEALTHY",
    icon: <CheckIcon sx={{ fontSize: 20 }} />,
  },
  needs_attention: {
    color: "#ff9800",
    label: "NEEDS ATTENTION",
    icon: <WarningIcon sx={{ fontSize: 20 }} />,
  },
  unhealthy: {
    color: "#f44336",
    label: "UNHEALTHY",
    icon: <ErrorIcon sx={{ fontSize: 20 }} />,
  },
};

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

// Markdown styles shared between messages
const markdownSx = (theme: Theme) => ({
  "& p": { margin: 0, lineHeight: 1.7 },
  "& p + p": { mt: 1.5 },
  "& code": {
    fontFamily: '"Fira Code", monospace',
    fontSize: "0.85rem",
    bgcolor: alpha(theme.palette.grey[500], 0.1),
    px: 0.5,
    py: 0.25,
    borderRadius: 0.5,
  },
  "& pre": {
    position: "relative",
    bgcolor: theme.palette.mode === "dark"
      ? alpha(theme.palette.grey[900], 0.8)
      : alpha(theme.palette.grey[200], 0.8),
    color: theme.palette.mode === "dark"
      ? theme.palette.text.secondary
      : theme.palette.text.primary,
    p: 2,
    borderRadius: 1,
    overflow: "auto",
    fontSize: "0.85rem",
    lineHeight: 1.5,
  },
  "& ul, & ol": { pl: 2.5, my: 1 },
  "& li": { mb: 0.5 },
});

// ---------------------------------------------------------------------------
// Context to pass execution capabilities into markdown code blocks
// ---------------------------------------------------------------------------
const ExecuteContext = React.createContext<{ canExecute: boolean; database: string }>({ canExecute: false, database: "" });

// ---------------------------------------------------------------------------
// Copy button for code blocks
// ---------------------------------------------------------------------------
function CopyCodeButton({ code }: { code: string }) {
  const theme = useTheme();
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code).catch(() => {});
  }, [code]);

  return (
    <Tooltip title="Copy" arrow placement="left">
      <IconButton
        size="small"
        onClick={handleCopy}
        sx={{
          position: "absolute",
          top: 6,
          right: 6,
          color: alpha(theme.palette.text.primary, 0.4),
          "&:hover": { color: alpha(theme.palette.text.primary, 0.8), bgcolor: alpha(theme.palette.text.primary, 0.08) },
        }}
      >
        <CopyIcon sx={{ fontSize: 16 }} />
      </IconButton>
    </Tooltip>
  );
}

// ---------------------------------------------------------------------------
// Run SQL button + inline result for code blocks
// ---------------------------------------------------------------------------
function RunSqlButton({ sql }: { sql: string }) {
  const theme = useTheme();
  const { canExecute, database } = React.useContext(ExecuteContext);
  const [state, setState] = useState<"idle" | "running" | "success" | "error">("idle");
  const [result, setResult] = useState<{ rows?: unknown[]; rowCount?: number; error?: string } | null>(null);

  const handleRun = useCallback(async () => {
    if (state === "running") return;
    setState("running");
    setResult(null);
    try {
      const resp = await fetch("/api/execute-sql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ sql: sql.trim(), database }),
      });
      const data = await resp.json();
      if (data.success) {
        setState("success");
        setResult({ rows: data.rows, rowCount: data.rowCount });
      } else {
        setState("error");
        setResult({ error: data.error || "Execution failed" });
      }
    } catch (err) {
      setState("error");
      setResult({ error: err instanceof Error ? err.message : "Network error" });
    }
  }, [sql, database, state]);

  if (!canExecute) return null;

  return (
    <>
      <Tooltip title={state === "success" ? "Executed" : state === "error" ? "Failed — click to retry" : "Run SQL"} arrow placement="left">
        <IconButton
          size="small"
          onClick={handleRun}
          disabled={state === "running"}
          sx={{
            position: "absolute",
            top: 6,
            right: 30,
            color: state === "success"
              ? theme.palette.success.main
              : state === "error"
                ? theme.palette.error.main
                : alpha(theme.palette.text.primary, 0.4),
            "&:hover": {
              color: state === "success" ? theme.palette.success.light : theme.palette.primary.main,
              bgcolor: alpha(theme.palette.text.primary, 0.08),
            },
          }}
        >
          {state === "running" ? <CircularProgress size={16} color="inherit" /> : state === "success" ? <CheckIcon sx={{ fontSize: 16 }} /> : <RunIcon sx={{ fontSize: 16 }} />}
        </IconButton>
      </Tooltip>
      {result && (
        <Box sx={{ mt: 1, p: 1.5, borderRadius: 1, bgcolor: alpha(state === "error" ? theme.palette.error.main : theme.palette.success.main, 0.06), border: `1px solid ${alpha(state === "error" ? theme.palette.error.main : theme.palette.success.main, 0.15)}`, fontSize: "0.8rem" }}>
          {result.error ? (
            <Typography variant="caption" color="error" sx={{ fontFamily: "monospace", whiteSpace: "pre-wrap" }}>{result.error}</Typography>
          ) : (
            <>
              <Typography variant="caption" color="success.main" sx={{ fontWeight: 600 }}>
                {result.rowCount === 0 ? "Statement executed successfully." : `${result.rowCount} row${result.rowCount !== 1 ? "s" : ""} returned.`}
              </Typography>
              {result.rows && result.rows.length > 0 && result.rows.length <= 50 && (
                <Box sx={{ mt: 1, overflow: "auto", maxHeight: 260 }}>
                  <table style={{ borderCollapse: "collapse", fontSize: "0.75rem", whiteSpace: "nowrap" }}>
                    <thead>
                      <tr>{Object.keys(result.rows[0] as Record<string, unknown>).slice(0, 8).map((col) => (
                        <th key={col} style={{ padding: "4px 8px", textAlign: "left", borderBottom: `1px solid ${alpha(theme.palette.divider, 0.3)}`, color: theme.palette.text.secondary, fontWeight: 600 }}>{col}</th>
                      ))}</tr>
                    </thead>
                    <tbody>
                      {result.rows.slice(0, 20).map((row, i) => (
                        <tr key={i}>{Object.entries(row as Record<string, unknown>).slice(0, 8).map(([k, val]) => (
                          <td key={k} style={{ padding: "3px 8px", borderBottom: `1px solid ${alpha(theme.palette.divider, 0.15)}`, color: theme.palette.text.primary, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{val == null ? "NULL" : String(val)}</td>
                        ))}</tr>
                      ))}
                    </tbody>
                  </table>
                  {result.rows.length > 20 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
                      Showing 20 of {result.rows.length} rows.
                    </Typography>
                  )}
                </Box>
              )}
            </>
          )}
        </Box>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Custom pre renderer with copy + run buttons
// ---------------------------------------------------------------------------
function PreWithActions({ children, ...props }: React.HTMLAttributes<HTMLPreElement>) {
  let code = "";
  const extractText = (node: React.ReactNode): void => {
    if (typeof node === "string") {
      code += node;
    } else if (Array.isArray(node)) {
      node.forEach(extractText);
    } else if (node && typeof node === "object" && "props" in node) {
      extractText((node as React.ReactElement<{ children?: React.ReactNode }>).props.children);
    }
  };
  extractText(children);

  // Detect SQL: check for language-sql class or SQL keywords
  const isSql = (() => {
    if (children && typeof children === "object" && "props" in (children as React.ReactElement)) {
      const className = String((children as React.ReactElement<{ className?: string }>).props.className || "");
      if (className.includes("language-sql")) return true;
    }
    const trimmed = code.trim().toUpperCase();
    return /^(SELECT|SHOW|DESCRIBE|ALTER|CREATE|DROP|INSERT|UPDATE|DELETE|MERGE|WITH|CALL|SET|USE|GRANT|REVOKE)\b/.test(trimmed);
  })();

  // Run button disabled for now — keeping infrastructure for future use
  const isExecutable = false;

  return (
    <Box sx={{ position: "relative" }}>
      <pre {...props} style={{ position: "relative", ...(props.style || {}) }}>
        {children}
        <CopyCodeButton code={code.trim()} />
      </pre>
      {isExecutable && <RunSqlButton sql={code.trim()} />}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Fix message bubble
// ---------------------------------------------------------------------------
function FixMessageBubble({ msg }: { msg: FixMessage }) {
  const theme = useTheme();

  if (msg.role === "user") {
    return (
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Box
          sx={{
            width: 28, height: 28, borderRadius: "50%",
            bgcolor: alpha(theme.palette.primary.main, 0.15),
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0, mt: 0.5,
          }}
        >
          <UserIcon sx={{ fontSize: 16, color: "primary.main" }} />
        </Box>
        <Paper
          elevation={0}
          sx={{
            px: 2, py: 1.5, borderRadius: 2, maxWidth: "85%",
            bgcolor: alpha(theme.palette.primary.main, 0.08),
            border: `1px solid ${alpha(theme.palette.primary.main, 0.15)}`,
          }}
        >
          <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
            {msg.text}
          </Typography>
        </Paper>
      </Stack>
    );
  }

  return (
    <Stack direction="row" spacing={1.5} alignItems="flex-start">
      <Box
        sx={{
          width: 28, height: 28, borderRadius: "50%",
          bgcolor: alpha(theme.palette.secondary.main, 0.15),
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0, mt: 0.5,
        }}
      >
        <BotIcon sx={{ fontSize: 16, color: "secondary.main" }} />
      </Box>
      <Paper
        elevation={0}
        sx={{
          px: 2, py: 1.5, borderRadius: 2, flex: 1, minWidth: 0,
          bgcolor: theme.palette.mode === "dark"
            ? alpha(theme.palette.grey[800], 0.4)
            : alpha(theme.palette.grey[100], 0.8),
          border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
          ...markdownSx(theme),
        }}
      >
        <Typography variant="body2" component="div">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{ pre: PreWithActions }}
          >
            {msg.text}
          </ReactMarkdown>
        </Typography>
      </Paper>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Suggest Fix fullscreen dialog
// ---------------------------------------------------------------------------
function SuggestFixDialog({
  open,
  onClose,
  fixState,
  onSendFollowUp,
  canExecute = false,
  database = "",
}: {
  open: boolean;
  onClose: () => void;
  fixState: SuggestFixState;
  onSendFollowUp?: (message: string) => void;
  canExecute?: boolean;
  database?: string;
}) {
  const theme = useTheme();
  const finding = fixState.finding;
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [fixState.messages, fixState.loading]);

  return (
    <ExecuteContext.Provider value={{ canExecute, database }}>
    <Dialog fullScreen open={open} onClose={onClose}>
      <AppBar
        sx={{
          position: "relative",
          bgcolor: theme.palette.background.paper,
          color: theme.palette.text.primary,
          backgroundImage: "none",
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
        }}
        elevation={0}
      >
        <Toolbar sx={{ gap: 1.5 }}>
          <IconButton edge="start" onClick={onClose} sx={{ color: "text.primary" }}>
            <CloseIcon />
          </IconButton>
          <FixIcon sx={{ color: theme.palette.primary.main, fontSize: 22 }} />
          <Typography variant="h6" sx={{ fontWeight: 700, flex: 1 }}>
            Suggested Fix
          </Typography>
          {finding && (
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                icon={severityIcon[finding.severity] as React.ReactElement}
                label={finding.severity.toUpperCase()}
                size="small"
                sx={{
                  fontSize: "0.7rem",
                  height: 24,
                  fontWeight: 600,
                  bgcolor: alpha(severityColor[finding.severity], 0.1),
                  color: severityColor[finding.severity],
                  border: `1px solid ${alpha(severityColor[finding.severity], 0.3)}`,
                  "& .MuiChip-icon": { color: severityColor[finding.severity] },
                }}
              />
              <Chip
                label={finding.category.replace("_", " ")}
                size="small"
                variant="outlined"
                sx={{ fontSize: "0.7rem", height: 24 }}
              />
            </Stack>
          )}
        </Toolbar>
      </AppBar>

      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
          ...getScrollbarSx(theme),
        }}
      >
        {/* Finding context card */}
        {finding && (
          <Paper
            elevation={0}
            sx={{
              mx: 3,
              mt: 3,
              mb: 2,
              p: 2.5,
              borderRadius: 2,
              flexShrink: 0,
              bgcolor: alpha(severityColor[finding.severity], 0.04),
              border: `1px solid ${alpha(severityColor[finding.severity], 0.15)}`,
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 700, color: severityColor[finding.severity], mb: 1 }}
            >
              Finding
            </Typography>
            <Typography
              variant="body2"
              sx={{ fontFamily: '"Fira Code", monospace', fontSize: "0.85rem", mb: 0.5 }}
            >
              {finding.object}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {finding.message}
            </Typography>
          </Paper>
        )}

        {/* Chat messages */}
        <Box sx={{ px: 3, pb: 3, flex: 1 }}>
          <Stack spacing={2}>
            {fixState.messages.map((msg, i) => (
              <FixMessageBubble key={i} msg={msg} />
            ))}

            {fixState.loading && fixState.messages.length === 0 && (
              <Stack
                direction="row"
                spacing={2}
                alignItems="center"
                sx={{ py: 4, justifyContent: "center" }}
              >
                <CircularProgress size={24} />
                <Typography variant="body2" color="text.secondary">
                  CoCo is analyzing the finding...
                </Typography>
              </Stack>
            )}

            {fixState.loading && fixState.messages.length > 0 && (
              <Stack
                direction="row"
                spacing={1}
                alignItems="center"
                sx={{ justifyContent: "center" }}
              >
                <CircularProgress size={16} />
                <Typography variant="caption" color="text.secondary">
                  Generating...
                </Typography>
              </Stack>
            )}

            {fixState.error && (
              <Paper
                elevation={0}
                sx={{
                  p: 2.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.error.main, 0.06),
                  border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                }}
              >
                <Typography variant="body2" color="error">
                  {fixState.error}
                </Typography>
              </Paper>
            )}

            <div ref={bottomRef} />
          </Stack>
        </Box>
      </Box>

      {/* Chat input + close */}
      <Box
        sx={{
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
        }}
      >
        {onSendFollowUp && !fixState.loading && fixState.messages.length > 0 && (
          <ChatInput
            onSend={onSendFollowUp}
            disabled={fixState.loading}
            placeholder="Ask a follow-up about this fix..."
          />
        )}
        <Box sx={{ p: 1.5, display: "flex", justifyContent: "flex-end" }}>
          <Button variant="outlined" size="small" onClick={onClose} sx={{ textTransform: "none" }}>
            {fixState.loading ? "Cancel" : "Close"}
          </Button>
        </Box>
      </Box>
    </Dialog>
    </ExecuteContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Report panel
// ---------------------------------------------------------------------------
export function ReportPanel({ report, onSuggestFix, onDismissFix, onSendFollowUp, fixState, canExecute }: ReportPanelProps) {
  const theme = useTheme();
  const { summary, pipeline_inventory: inv, findings } = report;
  const health = healthConfig[summary.overall_health] || healthConfig.healthy;

  const fixDialogOpen = fixState ? fixState.activeIndex !== null : false;

  return (
    <Box sx={{ p: 2, overflow: "auto", height: "100%" }}>
      {/* Health Badge */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 2,
          borderRadius: 2,
          bgcolor: alpha(health.color, 0.08),
          border: `2px solid ${alpha(health.color, 0.3)}`,
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        <Box sx={{ color: health.color }}>{health.icon}</Box>
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 700, color: health.color }}
          >
            {health.label}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {report.database} &middot; {report.audit_timestamp}
          </Typography>
        </Box>
      </Paper>

      {/* Summary Cards */}
      <Stack direction="row" spacing={1.5} sx={{ mb: 2 }}>
        {[
          {
            label: "Objects",
            value: summary.total_objects,
            color: theme.palette.primary.main,
          },
          { label: "Critical", value: summary.critical, color: "#f44336" },
          { label: "Warning", value: summary.warning, color: "#ff9800" },
          { label: "Info", value: summary.info, color: "#2196f3" },
        ].map((card) => (
          <Paper
            key={card.label}
            elevation={0}
            sx={{
              flex: 1,
              p: 1.5,
              textAlign: "center",
              borderRadius: 1.5,
              bgcolor: alpha(card.color, 0.06),
              border: `1px solid ${alpha(card.color, 0.15)}`,
            }}
          >
            <Typography
              variant="h5"
              sx={{ fontWeight: 700, color: card.color }}
            >
              {card.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {card.label}
            </Typography>
          </Paper>
        ))}
      </Stack>

      {/* Pipeline Inventory */}
      <Accordion
        defaultExpanded
        sx={{
          mb: 2,
          boxShadow: "none",
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: "8px !important",
          "&:before": { display: "none" },
          overflow: "hidden",
        }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <InventoryIcon color="primary" fontSize="small" />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Pipeline Inventory
            </Typography>
            <Chip
              label={`${inv.schemas.length} schemas`}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.65rem", height: 20 }}
            />
          </Stack>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0 }}>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              <strong>Schemas:</strong> {inv.schemas.join(", ")}
            </Typography>
            <Divider />
            <Stack direction="row" spacing={2} flexWrap="wrap">
              <Chip
                label={`${inv.tables.length} tables`}
                size="small"
                sx={{ fontSize: "0.7rem" }}
              />
              <Chip
                label={`${inv.dynamic_tables.length} dynamic tables`}
                size="small"
                sx={{ fontSize: "0.7rem" }}
              />
              <Chip
                label={`${inv.tasks.length} tasks`}
                size="small"
                sx={{ fontSize: "0.7rem" }}
              />
              <Chip
                label={`${inv.views.length} views`}
                size="small"
                sx={{ fontSize: "0.7rem" }}
              />
            </Stack>

            {inv.dynamic_tables.length > 0 && (
              <>
                <Divider />
                <Typography
                  variant="caption"
                  sx={{ fontWeight: 600, mt: 1 }}
                >
                  Dynamic Tables
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>Name</TableCell>
                        <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>Schema</TableCell>
                        <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>Target Lag</TableCell>
                        <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>State</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {inv.dynamic_tables.map((dt, i) => (
                        <TableRow key={i}>
                          <TableCell sx={{ fontSize: "0.75rem" }}>{dt.name}</TableCell>
                          <TableCell sx={{ fontSize: "0.75rem" }}>{dt.schema}</TableCell>
                          <TableCell sx={{ fontSize: "0.75rem" }}>{dt.target_lag || "-"}</TableCell>
                          <TableCell sx={{ fontSize: "0.75rem" }}>
                            <Chip
                              label={dt.scheduling_state || "unknown"}
                              size="small"
                              color={dt.scheduling_state === "ACTIVE" ? "success" : "default"}
                              sx={{ fontSize: "0.65rem", height: 18 }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Stack>
        </AccordionDetails>
      </Accordion>

      {/* Findings Table */}
      <Accordion
        defaultExpanded
        sx={{
          boxShadow: "none",
          border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          borderRadius: "8px !important",
          "&:before": { display: "none" },
          overflow: "hidden",
        }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <FindingsIcon color="primary" fontSize="small" />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Findings
            </Typography>
            <Chip
              label={`${findings.length} total`}
              size="small"
              variant="outlined"
              sx={{ fontSize: "0.65rem", height: 20 }}
            />
          </Stack>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0 }}>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem", width: 30 }}>#</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem", width: 80 }}>Severity</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem", width: 110 }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>Object</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem" }}>Message</TableCell>
                  {onSuggestFix && (
                    <TableCell sx={{ fontWeight: 600, fontSize: "0.75rem", width: 50, textAlign: "center" }}>Fix</TableCell>
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                {findings.map((f: Finding, i: number) => {
                  const isActiveFixRow = fixState?.activeIndex === i;
                  const hasResult = isActiveFixRow && fixState.messages.length > 0;
                  const isBusy = !!fixState?.loading;
                  return (
                    <TableRow
                      key={i}
                      sx={{
                        "&:hover": {
                          bgcolor: alpha(severityColor[f.severity], 0.04),
                        },
                        ...(isActiveFixRow && {
                          bgcolor: alpha(theme.palette.primary.main, 0.04),
                        }),
                      }}
                    >
                      <TableCell sx={{ fontSize: "0.75rem" }}>{i + 1}</TableCell>
                      <TableCell>
                        <Chip
                          icon={severityIcon[f.severity] as React.ReactElement}
                          label={f.severity.toUpperCase()}
                          size="small"
                          sx={{
                            fontSize: "0.6rem",
                            height: 20,
                            fontWeight: 600,
                            bgcolor: alpha(severityColor[f.severity], 0.1),
                            color: severityColor[f.severity],
                            border: `1px solid ${alpha(severityColor[f.severity], 0.3)}`,
                            "& .MuiChip-icon": {
                              color: severityColor[f.severity],
                            },
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={f.category.replace("_", " ")}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: "0.65rem", height: 18 }}
                        />
                      </TableCell>
                      <TableCell
                        sx={{
                          fontSize: "0.75rem",
                          fontFamily: '"Fira Code", monospace',
                          maxWidth: 200,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {f.object}
                      </TableCell>
                      <TableCell sx={{ fontSize: "0.75rem" }}>
                        {f.message}
                      </TableCell>
                      {onSuggestFix && (
                        <TableCell sx={{ textAlign: "center", p: 0.5 }}>
                          {f.severity !== "info" ? (
                          <IconButton
                            size="small"
                            disabled={isBusy && !isActiveFixRow}
                            onClick={() => onSuggestFix(i, f)}
                            sx={{
                              color: hasResult
                                ? theme.palette.success.main
                                : isActiveFixRow && isBusy
                                  ? theme.palette.primary.main
                                  : "text.secondary",
                              "&:hover": {
                                color: hasResult
                                  ? theme.palette.success.light
                                  : theme.palette.primary.main,
                              },
                              opacity: isBusy && !isActiveFixRow ? 0.3 : 1,
                            }}
                          >
                            {isActiveFixRow && isBusy ? (
                              <CircularProgress size={18} color="inherit" />
                            ) : (
                              <FixIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                          ) : null}
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Suggest Fix Dialog */}
      {fixState && onDismissFix && (
        <SuggestFixDialog
          open={fixDialogOpen}
          onClose={onDismissFix}
          fixState={fixState}
          onSendFollowUp={onSendFollowUp}
          canExecute={canExecute}
          database={report.database}
        />
      )}
    </Box>
  );
}
