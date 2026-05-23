export type RunStatus = "idle" | "running" | "error";

export interface CalibrationPoint {
  pixel: number;
  wavelength_nm: number;
}

export interface SystemStatus {
  status: RunStatus;
  error_message: string | null;
  session_id: string | null;
  sample_count: number;
  last_sample_id: string | null;
  last_sample_time: number | null;
  calibration: CalibrationPoint[];
}

export interface ColorReadReading {
  timestamp: number;
  pct_diff: number;
  organics_detected: boolean;
  interpretation: string;
}

export interface SpectrumPayload {
  sample_id: string;
  timestamp: number;
  wavelengths: number[];
  intensities: number[];
  peak_wavelengths: number[];
  peak_intensities: number[];
}

export interface CameraInfo {
  id: string;
  label: string;
  device: string;
  available: boolean;
}

export interface SessionSummary {
  session_id: string;
  start_time: string | null;
  end_time: string | null;
  measurement_count: number;
}

export interface RobotAction {
  id: string;
  label: string;
  description: string;
  running: boolean;
  started_at: number | null;
  finished_at: number | null;
  elapsed_s: number | null;
  exit_code: number | null;
  stdout: string;
  stderr: string;
  error: string | null;
}

export interface SessionDetail {
  session_id: string;
  start_time: string;
  end_time?: string;
  measurements: Array<{
    measurement_id: number;
    sample_id: string;
    timestamp: string;
    peaks_detected: number;
    biosignature_analysis: Record<string, unknown>;
  }>;
}
