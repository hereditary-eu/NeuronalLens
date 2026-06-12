import { atom } from "nanostores";
import * as d3 from "d3";

// ── Constants ─────────────────────────────────────────────────────────────────
export const MAX_STEP = 39900;   // 400 monitor samples × step-size 100
export const STEP_SIZE = 100;

// ── Interfaces ────────────────────────────────────────────────────────────────
export interface NeuronPosition {
  local_id: number;
  x: number;
  y: number;
  z: number;
  area: string;
  type: string;
}

export interface Selection {
  local_id: number;
  x: number | null;
  y: number | null;
  z: number | null;
  area: string | null;
  type: string | null;
}

export interface MonitorRow {
  step: number;
  fired: number;
  fired_fraction: number;
  activity: number;
  dampening: number;
  current_calcium: number;
  target_calcium: number;
  synaptic_input: number;
  background_input: number;
  grown_axons: number;
  connected_axons: number;
  grown_dendrites: number;
  connected_dendrites: number;
}

export interface ConnRow {
  source_id: number;
  target_id: number;
  weight: number;
}

export interface NetworkData {
  /** source_id → outgoing connections */
  out: Map<number, ConnRow[]>;
  /** target_id → incoming connections */
  inn: Map<number, ConnRow[]>;
}

// ── Stores ────────────────────────────────────────────────────────────────────
export const positions = atom<NeuronPosition[]>(
  (await d3.dsv(" ", "/rank_0_positions.txt")).map((d) => ({
    local_id: +(d["local_id"] ?? 0),
    x: +(d["x"] ?? 0),
    y: +(d["z"] ?? 0),
    z: +(d["y"] ?? 0),
    area: d["area"] ?? "",
    type: d["type"] ?? "",
  })),
);

export const currentTime = atom<number>(0);

export const selector = atom<Selection>({
  local_id: 1,
  x: null,
  y: null,
  z: null,
  area: null,
  type: null,
});

// ── Monitor data ──────────────────────────────────────────────────────────────
const monitorCache = new Map<number, MonitorRow[]>();

export async function fetchMonitor(local_id: number): Promise<MonitorRow[]> {
  if (monitorCache.has(local_id)) return monitorCache.get(local_id)!;
  try {
    const text = await fetch(`/monitors/0_${local_id}.csv`).then((r) => r.text());
    const rows = d3.dsvFormat(";").parseRows(text, (row): MonitorRow => ({
      step:               +(row[0]  ?? 0),
      fired:              +(row[1]  ?? 0),
      fired_fraction:     +(row[2]  ?? 0),
      activity:           +(row[3]  ?? 0),
      dampening:          +(row[4]  ?? 0),
      current_calcium:    +(row[5]  ?? 0),
      target_calcium:     +(row[6]  ?? 0),
      synaptic_input:     +(row[7]  ?? 0),
      background_input:   +(row[8]  ?? 0),
      grown_axons:        +(row[9]  ?? 0),
      connected_axons:    +(row[10] ?? 0),
      grown_dendrites:    +(row[11] ?? 0),
      connected_dendrites:+(row[12] ?? 0),
    }));
    // The full monitor file has 10 000 rows; only the first 400 are used for
    // visualisation (MAX_STEP / STEP_SIZE + 1), matching the activity .npy data.
    const sliced = rows.slice(0, MAX_STEP / STEP_SIZE + 1);
    monitorCache.set(local_id, sliced);
    return sliced;
  } catch {
    return [];
  }
}

/** Return the MonitorRow that corresponds to a currentTime value. */
export function monitorRowAt(rows: MonitorRow[], time: number): MonitorRow | undefined {
  return rows[Math.floor(time / STEP_SIZE)];
}

// ── Network data ──────────────────────────────────────────────────────────────

/** Available network snapshot steps (files copied to public/). */
const NETWORK_STEPS = [0, 10000, 20000, 30000, 40000];

/** Snap a currentTime value to the nearest available network step. */
export function networkStepFor(time: number): number {
  return NETWORK_STEPS.reduce((best, s) =>
    Math.abs(s - time) < Math.abs(best - time) ? s : best
  );
}

const networkCache = new Map<number, NetworkData>();

const parseNetworkFile = (text: string): ConnRow[] => {
  // header: "target_rank target_id source_rank source_id weight"
  return text
    .trim()
    .split("\n")
    .slice(1)
    .map((line) => {
      const p = line.trim().split(/\s+/);
      return {
        source_id: parseInt(p[3]!),
        target_id: parseInt(p[1]!),
        weight:    parseFloat(p[4]!),
      };
    });
};

export async function fetchNetwork(time = 0): Promise<NetworkData> {
  const step = networkStepFor(time);
  if (networkCache.has(step)) return networkCache.get(step)!;

  const [outText, inText] = await Promise.all([
    fetch(`/rank_0_step_${step}_out_network.txt`).then((r) => r.text()),
    fetch(`/rank_0_step_${step}_in_network.txt`).then((r) => r.text()),
  ]);

  const out = new Map<number, ConnRow[]>();
  const inn = new Map<number, ConnRow[]>();

  for (const row of parseNetworkFile(outText)) {
    if (!out.has(row.source_id)) out.set(row.source_id, []);
    out.get(row.source_id)!.push(row);
  }
  for (const row of parseNetworkFile(inText)) {
    if (!inn.has(row.target_id)) inn.set(row.target_id, []);
    inn.get(row.target_id)!.push(row);
  }

  const data: NetworkData = { out, inn };
  networkCache.set(step, data);
  return data;
}
