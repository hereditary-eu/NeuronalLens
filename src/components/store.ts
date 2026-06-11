import { atom } from "nanostores";
import * as d3 from "d3";

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

export const positions = atom<NeuronPosition[]>(
  (await d3.dsv(" ", "/rank_0_positions.txt")).map((d) => {
    return {
      local_id: +(d["local_id"] ?? 0),
      x: +(d["x"] ?? 0),
      y: +(d["y"] ?? 0),
      z: +(d["z"] ?? 0),
      area: d["area"] ?? "",
      type: d["type"] ?? "",
    };
  }),
);

export const selector = atom<Selection>({ local_id: 1, x: null, y: null, z: null, area: null, type: null });
