"use client";

import {
  Box,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { AuditHeader } from "@/components/AuditHeader";
import { AuditSidebar } from "@/components/AuditSidebar";
import { ChatThread } from "@/components/ChatThread";
import { EmptyState } from "@/components/EmptyState";
import { useAudit } from "@/hooks/useAudit";
import { useSuggestFix } from "@/hooks/useSuggestFix";
import { usePermissions } from "@/hooks/usePermissions";
import { useState, useCallback } from "react";

export function AuditDashboard() {
  const theme = useTheme();

  const {
    isAuditing,
    isLoading,
    report,
    messages,
    toolProgress,
    error,
    stats,
    startAudit,
    cancelAudit,
    resetView,
  } = useAudit();

  const { fixState, requestFix, sendFollowUp, dismissFix } = useSuggestFix();

  const permissions = usePermissions(report?.database || "", report?.schema || "");

  const handleSuggestFix = useCallback(
    (index: number, finding: import("@/lib/types").Finding) => {
      if (report?.database) {
        requestFix(index, finding, report.database);
      }
    },
    [report?.database, requestFix]
  );

  const downloadReport = useCallback(() => {
    if (!report) return;
    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const ts = report.audit_timestamp?.replace(/[:.]/g, "-") || Date.now();
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-${report.database}-${ts}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  // Email report — not wired in the quickstart (needs SYSTEM$SEND_EMAIL integration)
  // See the "Extending It" section in the guide for how to add this.

  const hasAuditData = isAuditing || report || toolProgress.length > 0;
  const showSidebar = hasAuditData;

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        bgcolor: theme.palette.background.default,
      }}
    >
      <AuditHeader
        onStartAudit={(db, scope, schema) => startAudit(db, scope, schema)}
        onCancel={cancelAudit}
        onReset={resetView}
        isLoading={isLoading}
        isAuditing={isAuditing}
      />

      {/* Main content area */}
      <Box sx={{ flex: 1, overflow: "hidden", display: "flex" }}>
        {!hasAuditData ? (
          <Box sx={{ flex: 1 }}>
                <EmptyState />
          </Box>
        ) : (
          <>
            {/* Chat column */}
            <Box
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                minWidth: 0,
              }}
            >
              {/* Chat thread with inline report accordion */}
              <Box sx={{ flex: 1, overflow: "auto" }}>
                <ChatThread messages={messages} report={report} toolProgress={toolProgress} isLoading={isLoading} onDownload={downloadReport} onSuggestFix={handleSuggestFix} onDismissFix={dismissFix} onSendFollowUp={sendFollowUp} fixState={fixState} canExecute={permissions.canExecute} />
              </Box>

              {/* Error display */}
              {error && (
                <Box sx={{ px: 2, py: 1 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      color: "error.main",
                      display: "block",
                      p: 1,
                      borderRadius: 1,
                      bgcolor: alpha(theme.palette.error.main, 0.08),
                    }}
                  >
                    {error}
                  </Typography>
                </Box>
              )}


            </Box>

            {/* Real-time stats sidebar */}
            {showSidebar && (
              <AuditSidebar
                toolProgress={toolProgress}
                report={report}
                stats={stats}
                isLoading={isLoading}
              />
            )}
          </>
        )}
      </Box>
    </Box>
  );
}
