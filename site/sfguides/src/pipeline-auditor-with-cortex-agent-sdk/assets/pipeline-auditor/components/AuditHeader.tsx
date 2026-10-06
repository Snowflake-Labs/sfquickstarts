"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Button,
  Typography,
  Paper,
  Stack,
  Chip,
  alpha,
  useTheme,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  AccountTree as PipelineIcon,
  Refresh as RefreshIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
} from "@mui/icons-material";
import { useThemeMode } from "@/components/ThemeContext";

export type AuditScope =
  | "tables_freshness"
  | "dynamic_tables"
  | "tasks"
  | "views"
  | "streams"
  | "pipes"
  | "procedures";

interface ScopeOption {
  key: AuditScope;
  label: string;
  defaultOn: boolean;
}

const SCOPE_OPTIONS: ScopeOption[] = [
  { key: "tables_freshness", label: "Tables & Freshness", defaultOn: true },
  { key: "dynamic_tables", label: "Dynamic Tables", defaultOn: true },
  { key: "tasks", label: "Tasks", defaultOn: true },
  { key: "views", label: "Views", defaultOn: true },
  { key: "streams", label: "Streams", defaultOn: false },
  { key: "pipes", label: "Pipes", defaultOn: false },
  { key: "procedures", label: "Stored Procedures", defaultOn: false },
];

const DEFAULT_SCOPE = SCOPE_OPTIONS.filter((o) => o.defaultOn).map((o) => o.key);

interface AuditHeaderProps {
  onStartAudit: (database: string, scope: AuditScope[], schema: string) => void;
  onCancel: () => void;
  onReset: () => void;
  isLoading: boolean;
  isAuditing: boolean;
}

export function AuditHeader({
  onStartAudit,
  onCancel,
  onReset,
  isLoading,
  isAuditing,
}: AuditHeaderProps) {
  const theme = useTheme();
  const { mode, toggleTheme } = useThemeMode();

  // Database state
  const [databases, setDatabases] = useState<string[]>([]);
  const [database, setDatabase] = useState("");
  const [databasesLoading, setDatabasesLoading] = useState(true);

  // Schema state
  const [schemas, setSchemas] = useState<string[]>([]);
  const [schema, setSchema] = useState("");
  const [schemasLoading, setSchemasLoading] = useState(false);

  // Audit scope state
  const [scope, setScope] = useState<AuditScope[]>(DEFAULT_SCOPE);

  const toggleScope = (key: AuditScope) => {
    setScope((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  // Fetch schemas for a given database
  const fetchSchemas = useCallback((db: string) => {
    if (!db) return;
    setSchemasLoading(true);
    setSchemas([]);
    setSchema("");
    fetch(`/api/schemas?database=${encodeURIComponent(db)}`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => {
        const s = (data.schemas || []) as string[];
        setSchemas(s);
      })
      .catch(() => setSchemas([]))
      .finally(() => setSchemasLoading(false));
  }, []);

  // Fetch databases
  const fetchDatabases = useCallback(() => {
    setDatabasesLoading(true);
    setDatabases([]);
    setDatabase("");
    setSchemas([]);
    setSchema("");
    fetch("/api/databases", { credentials: "include" })
      .then((r) => r.json())
      .then((data) => {
        const dbs = data.databases || [];
        setDatabases(dbs);
        let selectedDb = "";
        if (dbs.includes("PIPELINE_AUDITOR_DB")) {
          selectedDb = "PIPELINE_AUDITOR_DB";
        } else if (dbs.length > 0) {
          selectedDb = dbs[0];
        }
        if (selectedDb) {
          setDatabase(selectedDb);
          fetchSchemas(selectedDb);
        }
      })
      .catch(() => setDatabases([]))
      .finally(() => setDatabasesLoading(false));
  }, [fetchSchemas]);

  // Fetch databases on mount
  useEffect(() => {
    fetchDatabases();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDatabaseChange = useCallback(
    (db: string) => {
      setDatabase(db);
      fetchSchemas(db);
    },
    [fetchSchemas]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (database && schema && scope.length > 0) {
      onStartAudit(database, scope, schema);
    }
  };

  const selectorsDisabled = isLoading;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
        bgcolor:
          theme.palette.mode === "dark"
            ? alpha(theme.palette.background.paper, 0.8)
            : theme.palette.background.paper,
        zIndex: 1300,
        position: "relative",
      }}
    >
      <Stack
        direction={{ xs: "column", md: "row" }}
        alignItems={{ md: "flex-start" }}
        spacing={2}
        sx={{ maxWidth: 1200, mx: "auto", width: "100%" }}
      >
        {/* Logo */}
        <Stack
          direction="row"
          alignItems="center"
          spacing={1.5}
          onClick={isLoading ? undefined : onReset}
          sx={{ minWidth: 0, pt: 0.75, cursor: isLoading ? "default" : "pointer", "&:hover": { opacity: isLoading ? 1 : 0.8 } }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 40,
              height: 40,
              borderRadius: "50%",
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
            }}
          >
            <PipelineIcon color="primary" fontSize="small" />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Pipeline Auditor
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: "0.7rem" }}
            >
              Powered by Cortex Agent SDK
            </Typography>
          </Box>
        </Stack>

        {/* Selectors + scope — two rows */}
        <Box component="form" onSubmit={handleSubmit} sx={{ flex: 1 }}>
          <Stack spacing={1}>
            {/* Row 1: selectors + button */}
            <Stack direction="row" spacing={1} alignItems="center">
              <FormControl size="small" sx={{ width: 280, flexShrink: 0 }}>
                <InputLabel sx={{ fontSize: "0.75rem" }}>Database</InputLabel>
                <Select
                  value={database}
                  label="Database"
                  onChange={(e) => handleDatabaseChange(e.target.value)}
                  disabled={selectorsDisabled || databasesLoading || databases.length === 0}
                  sx={{ borderRadius: 1.5, fontSize: "0.75rem" }}
                  MenuProps={{ PaperProps: { sx: { maxHeight: 320, "&::-webkit-scrollbar": { width: 6 }, "&::-webkit-scrollbar-thumb": { bgcolor: (t) => alpha(t.palette.text.primary, 0.2), borderRadius: 3 }, "&::-webkit-scrollbar-track": { bgcolor: "transparent" } } } }}
                >
                  {databases.map((db) => (
                    <MenuItem key={db} value={db} sx={{ fontSize: "0.75rem" }}>
                      {db}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Tooltip title="Refresh databases">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => fetchDatabases()}
                    disabled={selectorsDisabled || databasesLoading}
                    sx={{ color: "text.secondary", "&:hover": { color: "primary.main" } }}
                  >
                    {databasesLoading ? <CircularProgress size={16} /> : <RefreshIcon sx={{ fontSize: 18 }} />}
                  </IconButton>
                </span>
              </Tooltip>

              <FormControl size="small" sx={{ width: 200, flexShrink: 0 }}>
                <InputLabel sx={{ fontSize: "0.75rem" }}>Schema</InputLabel>
                <Select
                  value={schema}
                  label="Schema"
                  onChange={(e) => setSchema(e.target.value)}
                  disabled={selectorsDisabled || schemasLoading || !database}
                  sx={{ borderRadius: 1.5, fontSize: "0.75rem" }}
                  MenuProps={{ PaperProps: { sx: { maxHeight: 320, "&::-webkit-scrollbar": { width: 6 }, "&::-webkit-scrollbar-thumb": { bgcolor: (t) => alpha(t.palette.text.primary, 0.2), borderRadius: 3 }, "&::-webkit-scrollbar-track": { bgcolor: "transparent" } } } }}
                >
                  {schemas.map((s) => (
                    <MenuItem key={s} value={s} sx={{ fontSize: "0.75rem" }}>
                      {s}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Tooltip title="Refresh schemas">
                <span>
                  <IconButton
                    size="small"
                    onClick={() => { if (database) fetchSchemas(database); }}
                    disabled={selectorsDisabled || schemasLoading || !database}
                    sx={{ color: "text.secondary", "&:hover": { color: "primary.main" } }}
                  >
                    {schemasLoading ? <CircularProgress size={16} /> : <RefreshIcon sx={{ fontSize: 18 }} />}
                  </IconButton>
                </span>
              </Tooltip>

              <Box sx={{ flexShrink: 0 }}>
                {isLoading ? (
                  <Button
                    type="button"
                    variant={theme.palette.mode === "light" ? "outlined" : "contained"}
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onCancel();
                    }}
                    sx={{
                      borderRadius: 1.5,
                      textTransform: "none",
                      minWidth: 140,
                      whiteSpace: "nowrap",
                      ...(theme.palette.mode === "light" && {
                        borderColor: theme.palette.error.main,
                        borderWidth: 1.5,
                        "&:hover": {
                          bgcolor: alpha(theme.palette.error.main, 0.08),
                          borderColor: theme.palette.error.dark,
                        },
                      }),
                    }}
                  >
                    Cancel Audit
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    variant={theme.palette.mode === "light" ? "outlined" : "contained"}
                    startIcon={<PlayIcon />}
                    disabled={!database || !schema || scope.length === 0}
                    sx={{
                      borderRadius: 1.5,
                      textTransform: "none",
                      fontWeight: 600,
                      px: 3,
                      minWidth: 140,
                      whiteSpace: "nowrap",
                      ...(theme.palette.mode === "light" && {
                        borderColor: theme.palette.primary.main,
                        borderWidth: 1.5,
                        "&:hover": {
                          bgcolor: alpha(theme.palette.primary.main, 0.08),
                          borderColor: theme.palette.primary.dark,
                        },
                      }),
                    }}
                  >
                    Run Audit
                  </Button>
                )}
              </Box>

              <Tooltip title={mode === "dark" ? "Light mode" : "Dark mode"}>
                <IconButton
                  size="small"
                  onClick={toggleTheme}
                  sx={{ flexShrink: 0, color: "text.secondary", "&:hover": { color: "primary.main" } }}
                >
                  {mode === "dark" ? <LightModeIcon sx={{ fontSize: 20 }} /> : <DarkModeIcon sx={{ fontSize: 20 }} />}
                </IconButton>
              </Tooltip>
            </Stack>

            {/* Row 2: scope chips */}
            <Stack direction="row" spacing={0.75} alignItems="center">
              <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5, fontSize: "0.7rem", whiteSpace: "nowrap" }}>
                Scope:
              </Typography>
              {SCOPE_OPTIONS.map((opt) => {
                const selected = scope.includes(opt.key);
                return (
                  <Chip
                    key={opt.key}
                    label={opt.label}
                    size="small"
                    clickable
                    disabled={selectorsDisabled}
                    onClick={() => toggleScope(opt.key)}
                    variant={selected ? "filled" : "outlined"}
                    sx={{
                      fontSize: "0.7rem",
                      height: 24,
                      borderRadius: 1,
                      fontWeight: selected ? 600 : 400,
                      bgcolor: selected
                        ? alpha(theme.palette.primary.main, 0.15)
                        : "transparent",
                      borderColor: selected
                        ? theme.palette.primary.main
                        : alpha(theme.palette.divider, 0.5),
                      color: selected
                        ? theme.palette.primary.main
                        : theme.palette.text.secondary,
                      "&:hover": {
                        bgcolor: selected
                          ? alpha(theme.palette.primary.main, 0.25)
                          : alpha(theme.palette.action.hover, 0.08),
                      },
                    }}
                  />
                );
              })}
            </Stack>
          </Stack>
        </Box>
      </Stack>
    </Paper>
  );
}
