import type { GamePhase } from "./types";

export const PHASE_DURATIONS: Record<GamePhase, number> = {
  betting: 60,
  locked: 15,
  live: 90,
  settle: 15,
};

export const PHASE_ORDER: GamePhase[] = ["betting", "locked", "live", "settle"];
export const CYCLE_SECONDS = PHASE_ORDER.reduce((s, p) => s + PHASE_DURATIONS[p], 0);

export const PHASE_COPY: Record<GamePhase, { label: string; blurb: string }> = {
  betting: {
    label: "Betting open",
    blurb: "Stake UNDER or OVER the vehicle threshold for this window.",
  },
  locked: { label: "Locked", blurb: "Positions are sealed. The counting window is about to open." },
  live: { label: "Live count", blurb: "Junction cameras are counting vehicles in real time." },
  settle: { label: "Settling", blurb: "Final count verified — payouts are being credited." },
};

export const JUNCTION = {
  id: "E-11",
  name: "Shutoko Expressway / Junction E-11",
  cameras: 4,
};

// Deterministic pseudo-random so every client sees the same round.
function hash(n: number) {
  let x = Math.sin(n * 12.9898) * 43758.5453;
  x = x - Math.floor(x);
  return x;
}

export interface RoundState {
  roundId: number;
  roundNumber: number;
  phase: GamePhase;
  phaseElapsed: number;
  phaseRemaining: number;
  threshold: number;
  liveCount: number;
  finalCount: number | null;
  pool: { under: number; over: number };
}

export function thresholdFor(roundId: number) {
  return 380 + Math.round(hash(roundId) * 160);
}

export function finalCountFor(roundId: number) {
  const t = thresholdFor(roundId);
  const drift = (hash(roundId + 7.77) - 0.5) * 140;
  return Math.max(80, Math.round(t + drift));
}

export function poolFor(roundId: number) {
  return {
    under: 8_000 + Math.round(hash(roundId + 3.3) * 22_000),
    over: 8_000 + Math.round(hash(roundId + 9.1) * 22_000),
  };
}

export function getRoundState(nowMs: number = Date.now()): RoundState {
  const totalSeconds = Math.floor(nowMs / 1000);
  const roundId = Math.floor(totalSeconds / CYCLE_SECONDS);
  let offset = totalSeconds % CYCLE_SECONDS;

  let phase: GamePhase = "betting";
  for (const p of PHASE_ORDER) {
    if (offset < PHASE_DURATIONS[p]) {
      phase = p;
      break;
    }
    offset -= PHASE_DURATIONS[p];
  }

  const final = finalCountFor(roundId);
  let liveCount = 0;
  if (phase === "live") {
    const progress = offset / PHASE_DURATIONS.live;
    const jitter = 1 + (hash(roundId + offset) - 0.5) * 0.02;
    liveCount = Math.round(final * progress * jitter);
  } else if (phase === "settle") {
    liveCount = final;
  }

  return {
    roundId,
    roundNumber: roundId,
    phase,
    phaseElapsed: offset,
    phaseRemaining: PHASE_DURATIONS[phase] - offset,
    threshold: thresholdFor(roundId),
    liveCount,
    finalCount: phase === "settle" ? final : null,
    pool: poolFor(roundId),
  };
}

export function historyRounds(currentRoundId: number, count = 8) {
  return Array.from({ length: count }, (_, i) => {
    const id = currentRoundId - (i + 1);
    const threshold = thresholdFor(id);
    const final = finalCountFor(id);
    return { id, threshold, final, result: final > threshold ? "over" : "under" } as const;
  });
}

export function formatCountdown(seconds: number) {
  const s = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export function shortAddress(address: string) {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}
