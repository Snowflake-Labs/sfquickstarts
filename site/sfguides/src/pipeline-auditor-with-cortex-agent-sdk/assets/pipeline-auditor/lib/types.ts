// ---------------------------------------------------------------------------
// Stream event types (NDJSON from backend)
// ---------------------------------------------------------------------------

export interface StatusEvent {
  type: "status";
  message: string;
  database?: string;
}

export interface ToolProgressEvent {
  type: "tool_progress";
  toolName: string;
  count: number;
  elapsed: number;
  sqlPreview?: string;
  description?: string;
}

export interface ToolUseEvent {
  type: "tool_use";
  toolName: string;
  toolId: string;
  input: Record<string, unknown>;
}

export interface TextEvent {
  type: "text";
  text: string;
}

export interface ThinkingEvent {
  type: "thinking";
  text: string;
}

export interface ReportEvent {
  type: "report";
  report: AuditReport;
}

export interface ResultEvent {
  type: "result";
  isError: boolean;
  numTurns: number;
  durationMs: number;
  toolCalls?: number;
  report?: AuditReport;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens: number;
    cache_read_input_tokens: number;
  };
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type StreamEvent =
  | StatusEvent
  | ToolProgressEvent
  | ToolUseEvent
  | TextEvent
  | ThinkingEvent
  | ReportEvent
  | ResultEvent
  | ErrorEvent;

// ---------------------------------------------------------------------------
// Audit report types (matches JSON schema)
// ---------------------------------------------------------------------------

export interface TableInfo {
  schema: string;
  name: string;
  type: string;
  row_count?: number;
}

export interface DynamicTableInfo {
  schema: string;
  name: string;
  target_lag?: string;
  refresh_mode?: string;
  scheduling_state?: string;
}

export interface TaskInfo {
  schema: string;
  name: string;
  schedule?: string;
  state?: string;
}

export interface ViewInfo {
  schema: string;
  name: string;
}

export interface PipelineInventory {
  schemas: string[];
  tables: TableInfo[];
  dynamic_tables: DynamicTableInfo[];
  tasks: TaskInfo[];
  views: ViewInfo[];
}

export type FindingCategory =
  | "freshness"
  | "volume"
  | "schema"
  | "dt_health"
  | "task_status"
  | "data_quality"
  | "pipeline_design"
  | "stream_health"
  | "pipe_status"
  | "procedure_review";

export type Severity = "critical" | "warning" | "info";

export interface Finding {
  category: FindingCategory;
  severity: Severity;
  object: string;
  message: string;
  details?: Record<string, unknown>;
}

export type OverallHealth = "healthy" | "needs_attention" | "unhealthy";

export interface AuditSummary {
  total_objects: number;
  critical: number;
  warning: number;
  info: number;
  overall_health: OverallHealth;
}

export interface AuditReport {
  database: string;
  schema?: string;
  audit_timestamp: string;
  pipeline_inventory: PipelineInventory;
  findings: Finding[];
  summary: AuditSummary;
}

// ---------------------------------------------------------------------------
// Chat message type
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
  isStreaming?: boolean;
  thinkingSteps?: string[];
  toolCalls?: Array<{
    toolName: string;
    elapsed?: number;
    sqlPreview?: string;
    description?: string;
  }>;
}
