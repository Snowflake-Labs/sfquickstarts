"use client";

import { AppThemeProvider } from "@/components/ThemeContext";
import { AuditDashboard } from "@/components/AuditDashboard";

export default function Page() {
  return (
    <AppThemeProvider>
      <AuditDashboard />
    </AppThemeProvider>
  );
}
