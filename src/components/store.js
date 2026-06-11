import { atom } from "nanostores";
import * as d3 from "d3";

export const positions = atom(
  (await d3.dsv(" ", "/rank_0_positions.txt")).map((d) => {
    return {
      local_id: +d.local_id,
      x: +d.x,
      y: +d.y,
      z: +d.z,
      area: d.area,
      type: d.type,
    };
  }),
);

export const selector = atom({ local_id: 1, x: null, y: null, z: null, area: null, type: null });
