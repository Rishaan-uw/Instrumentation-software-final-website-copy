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

export interface Biosignatures {
  chlorophyll: boolean;
  carotenoids: boolean;
  organics: boolean;
  /** Percentage of organic matter from the color test (0–100). Null until measured. */
  organic_pct: number | null;
  confidence: "none" | "low" | "medium" | "high";
  interpretation: string;
}

export interface SpectrumPayload {
  sample_id: string;
  timestamp: number;
  wavelengths: number[];
  intensities: number[];
  peak_wavelengths: number[];
  peak_intensities: number[];
  biosignatures: Biosignatures;
}

export interface ChemReading {
  timestamp: number;
  ph: number;
  conductivity_us_cm: number;
  temperature_c: number;
  moisture_pct: number;
  organic_index: number;
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
    biosignature_analysis: Biosignatures;
  }>;
}
