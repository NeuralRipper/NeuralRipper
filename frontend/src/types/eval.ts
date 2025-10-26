// WebSocket Message Types
export interface WSMessageSend {
  model: string;
  prompt: string;
}

export interface WSMessageToken {
  token: string;
}

export interface WSMessageDone {
  done: boolean;
}

export interface WSMessageError {
  error: string;
}

export type WSMessageReceive = WSMessageToken | WSMessageDone | WSMessageError;

// Connection Status
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'error';

// Metrics Types
export interface MetricsState {
  tokensPerSec: number;      // Tokens generated per second
  ttft: number;              // Time to first token (ms)
  gpuUtil: number;           // GPU utilization percentage
  cost: number;              // Running cost in dollars
  accuracy: number;          // Model accuracy percentage
  temp: number;              // GPU temperature (Celsius)
  runtime: number;           // Total runtime (minutes)
}

// Benchmark Types
export type BenchmarkStatus = 'queued' | 'running' | 'done' | 'error';

export interface Benchmark {
  name: string;              // Benchmark name (e.g., "MMLU", "HellaSwag")
  progress: number;          // Progress percentage (0-100)
  current: number;           // Current completed items
  total: number;             // Total items in benchmark
  status: BenchmarkStatus;   // Current status
  score?: number;            // Final score (if completed)
}

// Terminal Line Types
export type TerminalLineType = 'system' | 'prompt' | 'response' | 'divider' | 'empty' | 'error';

export interface TerminalLine {
  type: TerminalLineType;
  text: string;
  timestamp?: number;
}

// Inference Request
export interface InferenceRequest {
  model: string;
  prompt: string;
  temperature?: number;
  maxTokens?: number;
}

// Token Tracking (for metrics calculation)
export interface TokenTracking {
  startTime: number | null;
  firstTokenTime: number | null;
  tokenCount: number;
  lastTokenTime: number | null;
}
