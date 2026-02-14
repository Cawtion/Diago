/**
 * API client for the Diago FastAPI backend.
 * All requests go through the Vite proxy (or direct in production).
 */

import type {
  BehavioralContext,
  DiagnosisResponse,
  AudioInfo,
  SpectrogramData,
  Session,
  SessionMatch,
  Signature,
  SignatureStats,
  TroubleCode,
  VinDecodeResult,
  RecallsResult,
  VehicleYearsResult,
  VehicleMakesResult,
  VehicleModelsResult,
  TSBItem,
  TSBSearchResult,
} from "@/types";
import { getApiBase } from "@/lib/env";

const BASE = `${getApiBase()}/api/v1`;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

/* ─── Health ─── */
export async function healthCheck() {
  return request<{ status: string; version: string }>(`${getApiBase()}/health`);
}

/* ─── Diagnosis ─── */
export async function diagnoseText(payload: {
  symptoms: string;
  codes: string[];
  context: BehavioralContext;
}): Promise<DiagnosisResponse> {
  return request<DiagnosisResponse>(`${BASE}/diagnosis/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function diagnoseAudio(
  file: File | Blob,
  symptoms = "",
  codes = ""
): Promise<DiagnosisResponse> {
  const form = new FormData();
  form.append("audio_file", file);
  form.append("symptoms", symptoms);
  form.append("codes", codes);
  return request<DiagnosisResponse>(`${BASE}/diagnosis/audio`, {
    method: "POST",
    body: form,
  });
}

/* ─── Audio ─── */
export async function getAudioInfo(file: File | Blob): Promise<AudioInfo> {
  const form = new FormData();
  form.append("audio_file", file);
  return request<AudioInfo>(`${BASE}/audio/info`, {
    method: "POST",
    body: form,
  });
}

export async function getSpectrogram(
  file: File | Blob,
  mode = "power"
): Promise<SpectrogramData> {
  const form = new FormData();
  form.append("audio_file", file);
  form.append("mode", mode);
  return request<SpectrogramData>(`${BASE}/audio/spectrogram`, {
    method: "POST",
    body: form,
  });
}

/* ─── Sessions ─── */
export async function listSessions(limit = 50): Promise<Session[]> {
  return request<Session[]>(`${BASE}/sessions/?limit=${limit}`);
}

export async function getSessionMatches(
  sessionId: number
): Promise<SessionMatch[]> {
  return request<SessionMatch[]>(`${BASE}/sessions/${sessionId}/matches`);
}

export async function deleteSession(
  sessionId: number
): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`${BASE}/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

/* ─── Signatures ─── */
export async function listSignatures(): Promise<Signature[]> {
  return request<Signature[]>(`${BASE}/signatures/`);
}

export async function getSignatureStats(): Promise<SignatureStats> {
  return request<SignatureStats>(`${BASE}/signatures/stats`);
}

export async function createSignature(payload: {
  name: string;
  description: string;
  category: string;
  associated_codes?: string;
}): Promise<{ signature_id: number }> {
  return request<{ signature_id: number }>(`${BASE}/signatures/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteSignature(
  id: number
): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`${BASE}/signatures/${id}`, {
    method: "DELETE",
  });
}

/* ─── Trouble Codes ─── */
export async function lookupCode(code: string): Promise<TroubleCode> {
  return request<TroubleCode>(`${BASE}/codes/lookup/${code}`);
}

export async function lookupCodes(codes: string[]): Promise<TroubleCode[]> {
  return request<TroubleCode[]>(
    `${BASE}/codes/lookup?codes=${codes.join(",")}`
  );
}

export async function searchCodes(
  query: string
): Promise<{ query: string; results: TroubleCode[]; count: number }> {
  return request<{ query: string; results: TroubleCode[]; count: number }>(
    `${BASE}/codes/search?q=${encodeURIComponent(query)}`
  );
}

export async function suggestBySymptoms(
  keywords: string[]
): Promise<TroubleCode[]> {
  return request<TroubleCode[]>(
    `${BASE}/codes/symptoms?keywords=${keywords.join(",")}`
  );
}

/* ─── Vehicle (NHTSA vPIC + Recalls) ─── */
export async function decodeVin(
  vin: string,
  modelYear?: number
): Promise<VinDecodeResult> {
  const params = new URLSearchParams();
  if (modelYear != null) params.set("model_year", String(modelYear));
  const q = params.toString();
  return request<VinDecodeResult>(
    `${BASE}/vehicle/vin/${encodeURIComponent(vin)}${q ? `?${q}` : ""}`
  );
}

export async function getRecalls(
  make: string,
  model: string,
  modelYear: number
): Promise<RecallsResult> {
  return request<RecallsResult>(
    `${BASE}/vehicle/recalls?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}&model_year=${modelYear}`
  );
}

export async function getVehicleYears(): Promise<VehicleYearsResult> {
  return request<VehicleYearsResult>(`${BASE}/vehicle/years`);
}

export async function getVehicleMakes(
  vehicleType = "car"
): Promise<VehicleMakesResult> {
  return request<VehicleMakesResult>(
    `${BASE}/vehicle/makes?vehicle_type=${encodeURIComponent(vehicleType)}`
  );
}

export async function getVehicleModels(
  makeId: number,
  modelYear: number
): Promise<VehicleModelsResult> {
  return request<VehicleModelsResult>(
    `${BASE}/vehicle/models?make_id=${makeId}&model_year=${modelYear}`
  );
}

/* ─── TSBs ─── */
export async function searchTsbs(params: {
  model_year?: number;
  make?: string;
  model?: string;
  component?: string;
  limit?: number;
}): Promise<TSBSearchResult> {
  const search = new URLSearchParams();
  if (params.model_year != null) search.set("model_year", String(params.model_year));
  if (params.make) search.set("make", params.make);
  if (params.model) search.set("model", params.model);
  if (params.component) search.set("component", params.component);
  if (params.limit != null) search.set("limit", String(params.limit));
  return request<TSBSearchResult>(`${BASE}/tsbs/search?${search.toString()}`);
}

export async function getTsbCount(): Promise<{ count: number }> {
  return request<{ count: number }>(`${BASE}/tsbs/count`);
}
