"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import {
  Box,
  Paper,
  Typography,
  Stack,
  alpha,
  useTheme,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  LinearProgress,
  Chip,
  Button,
  CircularProgress,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  AutoAwesome as ThinkingIcon,
  SmartToy as BotIcon,
  Assessment as ReportIcon,
  Timeline as TimelineIcon,
  Download as DownloadIcon,
  MailOutline as MailIcon,
  CheckCircle as CheckIcon,
  Storage as DatabaseIcon,
} from "@mui/icons-material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, AuditReport, ToolProgressEvent, Finding } from "@/lib/types";
import { ReportPanel } from "@/components/ReportPanel";
import type { SuggestFixState } from "@/hooks/useSuggestFix";
import { AuditPhase, ActivityFeed } from "@/components/AuditSidebar";

import type { Theme } from "@mui/material";

// Re-export Finding so callers don't need a separate import for the callback
export type { Finding };

// Theme-aware scrollbar styles
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

interface ChatThreadProps {
  messages: ChatMessage[];
  report?: AuditReport | null;
  toolProgress?: ToolProgressEvent[];
  isLoading?: boolean;
  onDownload?: () => void;
  onEmail?: () => Promise<void> | void;
  onSuggestFix?: (index: number, finding: Finding) => void;
  onDismissFix?: () => void;
  onSendFollowUp?: (message: string) => void;
  fixState?: SuggestFixState;
  canExecute?: boolean;
}

export function ChatThread({ messages, report, toolProgress = [], isLoading = false, onDownload, onEmail, onSuggestFix, onDismissFix, onSendFollowUp, fixState, canExecute }: ChatThreadProps) {
  const theme = useTheme();
  const reportRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevReportRef = useRef<AuditReport | null>(null);
  const wasLoadingRef = useRef(false);
  const [emailState, setEmailState] = useState<"idle" | "sending" | "sent">("idle");

  const handleEmail = useCallback(async (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!onEmail || emailState === "sending") return;
    setEmailState("sending");
    try {
      await onEmail();
      setEmailState("sent");
      setTimeout(() => setEmailState("idle"), 3000);
    } catch {
      setEmailState("idle");
    }
  }, [onEmail, emailState]);

  // Auto-scroll to report accordion when it first appears
  useEffect(() => {
    if (report && !prevReportRef.current) {
      prevReportRef.current = report;
      // Small delay to let the accordion render
      setTimeout(() => {
        reportRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, [report]);

  // Scroll to top when audit finishes (isLoading transitions false → lets user see the report)
  useEffect(() => {
    if (wasLoadingRef.current && !isLoading) {
      setTimeout(() => {
        containerRef.current?.scrollTo({ top: 0, behavior: "smooth" });
      }, 300);
    }
    wasLoadingRef.current = isLoading;
  }, [isLoading]);

  if (messages.length === 0) return null;

  return (
    <Box ref={containerRef} sx={{ p: 2, overflow: "auto", height: "100%", display: "flex", flexDirection: "column", ...getScrollbarSx(theme) }}>
      <Stack spacing={2} sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        {messages.map((msg) => (
          <Box key={msg.id} sx={{ flexShrink: 0 }}>
            {msg.role === "user" ? (
              <AuditConfigBanner text={msg.text} />
            ) : (
              <AssistantMessage message={msg} />
            )}
          </Box>
        ))}

        {/* Audit progress + activity feed — shows immediately when audit starts, collapses when done */}
        {(isLoading || toolProgress.length > 0) && (
          <Box sx={{ flexShrink: 0 }}>
            <AuditProgressAccordion toolProgress={toolProgress} isLoading={isLoading} />
          </Box>
        )}

        {/* Inline report accordion — appears after audit completes */}
        {report && (
          <Box ref={reportRef} sx={{ flexShrink: 0 }}>
            <Accordion
              defaultExpanded
              sx={{
                boxShadow: "none",
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                borderRadius: "12px !important",
                "&:before": { display: "none" },
                overflow: "hidden",
                bgcolor: alpha(theme.palette.primary.main, 0.02),
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  minHeight: 48,
                  "& .MuiAccordionSummary-content": { my: 1 },
                }}
              >
                <Stack direction="row" alignItems="center" spacing={1.5} sx={{ flex: 1 }}>
                  <ReportIcon sx={{ color: "primary.main", fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Audit Report
                  </Typography>
                  <Chip
                    label={report.summary.overall_health.replace("_", " ").toUpperCase()}
                    size="small"
                    sx={{
                      fontSize: "0.65rem",
                      height: 20,
                      fontWeight: 600,
                      bgcolor:
                        report.summary.overall_health === "healthy"
                          ? alpha("#4caf50", 0.15)
                          : report.summary.overall_health === "needs_attention"
                          ? alpha("#ff9800", 0.15)
                          : alpha("#f44336", 0.15),
                      color:
                        report.summary.overall_health === "healthy"
                          ? "#4caf50"
                          : report.summary.overall_health === "needs_attention"
                          ? "#ff9800"
                          : "#f44336",
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {report.summary.total_objects} objects &middot; {report.summary.critical} critical &middot; {report.summary.warning} warning
                  </Typography>
                  <Box sx={{ flex: 1 }} />
                  {onDownload && (
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon sx={{ fontSize: 16 }} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        onDownload();
                      }}
                      sx={{
                        textTransform: "none",
                        fontSize: "0.7rem",
                        borderRadius: 1.5,
                        borderColor: alpha(theme.palette.primary.main, 0.3),
                        "&:hover": { borderColor: "primary.main" },
                        mr: 1,
                      }}
                    >
                      Download Report
                    </Button>
                  )}
                  {onEmail && (
                    <Button
                      variant="outlined"
                      size="small"
                      disabled={emailState === "sending"}
                      startIcon={emailState === "sending" ? <CircularProgress size={14} /> : emailState === "sent" ? <CheckIcon sx={{ fontSize: 16, color: "success.main" }} /> : <MailIcon sx={{ fontSize: 16 }} />}
                      onClick={handleEmail}
                      sx={{
                        textTransform: "none",
                        fontSize: "0.7rem",
                        borderRadius: 1.5,
                        borderColor: emailState === "sent" ? alpha(theme.palette.success.main, 0.5) : alpha(theme.palette.primary.main, 0.3),
                        color: emailState === "sent" ? "success.main" : undefined,
                        "&:hover": { borderColor: emailState === "sent" ? "success.main" : "primary.main" },
                        mr: 1,
                      }}
                    >
                      Email Report
                    </Button>
                  )}
                </Stack>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0, ...getScrollbarSx(theme) }}>
                <Divider />
                <ReportPanel report={report} onSuggestFix={onSuggestFix} onDismissFix={onDismissFix} onSendFollowUp={onSendFollowUp} fixState={fixState} canExecute={canExecute} />
                {(onDownload || onEmail) && (
                  <Box sx={{ px: 2, py: 1.5, display: "flex", justifyContent: "flex-end", gap: 1, borderTop: `1px solid ${alpha(theme.palette.divider, 0.3)}` }}>
                    {onDownload && (
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon sx={{ fontSize: 16 }} />}
                      onClick={onDownload}
                      sx={{
                        textTransform: "none",
                        fontSize: "0.7rem",
                        borderRadius: 1.5,
                        borderColor: alpha(theme.palette.primary.main, 0.3),
                        "&:hover": { borderColor: "primary.main" },
                      }}
                    >
                      Download Report
                    </Button>
                    )}
                    {onEmail && (
                    <Button
                      variant="outlined"
                      size="small"
                      disabled={emailState === "sending"}
                      startIcon={emailState === "sending" ? <CircularProgress size={14} /> : emailState === "sent" ? <CheckIcon sx={{ fontSize: 16, color: "success.main" }} /> : <MailIcon sx={{ fontSize: 16 }} />}
                      onClick={() => handleEmail()}
                      sx={{
                        textTransform: "none",
                        fontSize: "0.7rem",
                        borderRadius: 1.5,
                        borderColor: emailState === "sent" ? alpha(theme.palette.success.main, 0.5) : alpha(theme.palette.primary.main, 0.3),
                        color: emailState === "sent" ? "success.main" : undefined,
                        "&:hover": { borderColor: emailState === "sent" ? "success.main" : "primary.main" },
                      }}
                    >
                      Email Report
                    </Button>
                    )}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          </Box>
        )}

      </Stack>
    </Box>
  );
}

// Theme-aware scrollbar styles for inner containers
function getInnerScrollbarSx(theme: Theme) {
  const thumb = alpha(theme.palette.text.primary, 0.08);
  return {
    "&::-webkit-scrollbar": { width: 4 },
    "&::-webkit-scrollbar-track": { bgcolor: "transparent" },
    "&::-webkit-scrollbar-thumb": {
      bgcolor: thumb,
      borderRadius: 2,
    },
    scrollbarWidth: "thin" as const,
    scrollbarColor: `${thumb} transparent`,
  };
}

function AuditProgressAccordion({
  toolProgress,
  isLoading,
}: {
  toolProgress: ToolProgressEvent[];
  isLoading?: boolean;
}) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const hasActivity = toolProgress.length > 0;

  // Auto-expand when first tool call arrives
  useEffect(() => {
    if (hasActivity && isLoading) {
      setExpanded(true);
    }
  }, [hasActivity, isLoading]);

  // Auto-collapse when audit completes or is stopped
  useEffect(() => {
    if (!isLoading && hasActivity) {
      setExpanded(false);
    }
  }, [isLoading, hasActivity]);

  return (
    <Accordion
      expanded={expanded}
      onChange={(_, exp) => setExpanded(exp)}
      sx={{
        boxShadow: "none",
        border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
        borderRadius: "12px !important",
        "&:before": { display: "none" },
        overflow: "hidden",
        bgcolor: alpha(theme.palette.info.main, 0.02),
        position: "relative",
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          minHeight: 48,
          flexShrink: 0,
          position: "relative",
          "& .MuiAccordionSummary-content": { my: 1 },
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <TimelineIcon sx={{ color: "info.main", fontSize: 20 }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Audit Progress
          </Typography>
          {!isLoading && toolProgress.length > 0 && (
            <Chip
              label={`${toolProgress.length} tool calls`}
              size="small"
              sx={{
                fontSize: "0.65rem",
                height: 20,
                fontWeight: 600,
                bgcolor: alpha(theme.palette.success.main, 0.15),
                color: theme.palette.success.main,
              }}
            />
          )}
        </Stack>
        {isLoading && (
          <LinearProgress
            sx={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: 2,
              bgcolor: alpha(theme.palette.info.main, 0.08),
              "& .MuiLinearProgress-bar": {
                bgcolor: theme.palette.info.main,
              },
            }}
          />
        )}
      </AccordionSummary>
      <AccordionDetails sx={{ p: 0, display: "flex", flexDirection: "column" }}>
        <Divider />
        <Box sx={{ px: 2, pt: 1.5, pb: 1, flexShrink: 0 }}>
          <AuditPhase toolProgress={toolProgress} isLoading={isLoading ?? false} />
        </Box>
        <Divider sx={{ mx: 2, flexShrink: 0 }} />
        <Box sx={{ px: 0 }}>
          <ActivityFeed toolProgress={toolProgress} isLoading={isLoading ?? false} />
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

const SCOPE_LABELS: Record<string, string> = {
  tables_freshness: "Tables & Freshness",
  dynamic_tables: "Dynamic Tables",
  tasks: "Tasks",
  views: "Views",
  streams: "Streams",
  pipes: "Pipes",
  procedures: "Stored Procedures",
};

function AuditConfigBanner({ text }: { text: string }) {
  const theme = useTheme();

  // Parse "Audit DB database, schema SCHEMA, scope A|B|C" or "Audit DB database, scope A|B"
  const dbMatch = text.match(/Audit\s+(\S+)\s+database/);
  const schemaMatch = text.match(/schema\s+(\S+?)(?:,|$)/);
  const scopeMatch = text.match(/scope\s+(.+)$/);
  const database = dbMatch?.[1] || "";
  const schema = schemaMatch?.[1] || "";
  const scopes = scopeMatch?.[1]?.split("|").filter(Boolean) || [];

  return (
    <Paper
      elevation={0}
      sx={{
        px: 2,
        py: 1,
        borderRadius: 2,
        bgcolor: alpha(theme.palette.primary.main, 0.04),
        border: `1px solid ${alpha(theme.palette.primary.main, 0.12)}`,
        display: "flex",
        alignItems: "center",
        gap: 1,
        overflow: "hidden",
      }}
    >
      <DatabaseIcon sx={{ fontSize: 18, color: "primary.main", flexShrink: 0 }} />
      <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: 0.5, flexShrink: 0 }}>
        Auditing
      </Typography>
      <Chip
        label={database}
        size="small"
        sx={{
          fontSize: "0.65rem",
          height: 20,
          fontWeight: 500,
          bgcolor: alpha(theme.palette.info.main, 0.08),
          color: "text.secondary",
          border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
          flexShrink: 0,
        }}
      />
      {schema && (
        <>
          <Typography sx={{ color: alpha(theme.palette.text.secondary, 0.4), fontSize: "0.9rem", flexShrink: 0 }}>
            /
          </Typography>
          <Chip
            label={schema}
            size="small"
            sx={{
              fontSize: "0.65rem",
              height: 20,
              fontWeight: 500,
              bgcolor: alpha(theme.palette.info.main, 0.08),
              color: "text.secondary",
              border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
              flexShrink: 0,
            }}
          />
        </>
      )}
      {scopes.length > 0 && (
        <Typography sx={{ color: alpha(theme.palette.text.secondary, 0.4), fontSize: "0.9rem", flexShrink: 0 }}>
          /
        </Typography>
      )}
      {scopes.length > 0 && scopes.map((s) => (
        <Chip
          key={s}
          label={SCOPE_LABELS[s] || s.replace(/_/g, " ")}
          size="small"
          sx={{
            fontSize: "0.65rem",
            height: 20,
            fontWeight: 500,
            bgcolor: alpha(theme.palette.info.main, 0.08),
            color: "text.secondary",
            border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
            flexShrink: 0,
          }}
        />
      ))}
    </Paper>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const theme = useTheme();
  const hasThinking =
    message.thinkingSteps && message.thinkingSteps.length > 0;
  const hasContent = message.text || hasThinking;

  // Don't render empty assistant bubbles (e.g. status-only or pre-content streaming)
  if (!hasContent) return null;

  return (
    <Stack direction="row" spacing={1.5} alignItems="flex-start">
      <Box
        sx={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          bgcolor: alpha(theme.palette.secondary.main, 0.15),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          mt: 0.5,
        }}
      >
        <BotIcon sx={{ fontSize: 16, color: "secondary.main" }} />
      </Box>
      <Box sx={{ flex: 1, minWidth: 0, maxWidth: "90%" }}>
        {/* Thinking Steps */}
        {hasThinking && (
          <Accordion
            defaultExpanded={false}
            sx={{
              mb: 1,
              boxShadow: "none",
              bgcolor: "transparent",
              border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
              borderRadius: "8px !important",
              "&:before": { display: "none" },
              overflow: "hidden",
            }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon fontSize="small" />}
              sx={{ minHeight: 36, "& .MuiAccordionSummary-content": { my: 0.5 } }}
            >
              <Stack direction="row" alignItems="center" spacing={1}>
                <ThinkingIcon sx={{ fontSize: 16, color: "secondary.main" }} />
                <Typography
                  variant="caption"
                  sx={{ fontWeight: 600, color: "secondary.main" }}
                >
                  Thinking
                </Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails sx={{ pt: 0, pb: 1 }}>
              <Divider sx={{ mb: 1 }} />
              <Stack spacing={0.5}>
                {message.thinkingSteps!.map((step, i) => (
                  <Typography
                    key={i}
                    variant="caption"
                    sx={{
                      fontStyle: "italic",
                      color: "text.secondary",
                      lineHeight: 1.5,
                      pl: 1,
                      borderLeft: `2px solid ${alpha(theme.palette.secondary.main, 0.3)}`,
                    }}
                  >
                    {step.length > 300 ? step.slice(0, 300) + "..." : step}
                  </Typography>
                ))}
              </Stack>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Status / Message Text — shown ABOVE tool calls */}
        {message.text && (
          <Paper
            elevation={0}
            sx={{
              px: 2,
              py: 1.5,
              mb: 0,
              borderRadius: 2,
              bgcolor:
                theme.palette.mode === "dark"
                  ? alpha(theme.palette.grey[800], 0.4)
                  : alpha(theme.palette.grey[100], 0.6),
              border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
              "& p": { margin: 0, lineHeight: 1.6 },
              "& p + p": { mt: 1 },
              "& code": {
                fontFamily: '"Fira Code", monospace',
                fontSize: "0.8rem",
                bgcolor: alpha(theme.palette.grey[500], 0.1),
                px: 0.5,
                py: 0.25,
                borderRadius: 0.5,
              },
              "& pre": {
                bgcolor: alpha(theme.palette.grey[900], 0.8),
                    color: "text.secondary",
                p: 1.5,
                borderRadius: 1,
                overflow: "auto",
                fontSize: "0.8rem",
              },
            }}
          >
            <Typography variant="body2" component="div">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.text}
              </ReactMarkdown>
            </Typography>
          </Paper>
        )}


      </Box>
    </Stack>
  );
}
