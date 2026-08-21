import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";

import { PhaseStatus } from "@/components/phase-status";
import { LiveStream } from "@/components/live-stream";
import { SectionHeading } from "@/components/panel";
import { StakePanel } from "@/components/stake-panel";
import { JUNCTION } from "@/lib/round";
import { useGameLoop } from "@/hooks/useGameLoop";


export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TRAFFIC — Live Vehicle Count Under/Over Markets" },
      {
        name: "description",
        content:
          "Stake under or over the vehicle threshold on live junction camera counts. Betting, locked, live and settling phases every three minutes.",
      },
      { property: "og:title", content: "TRAFFIC — Live Vehicle Count Under/Over Markets" },
      {
        property: "og:description",
        content:
          "Live traffic count markets: pick under or over the threshold and settle on verified camera data.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const loop = useGameLoop();
  const queryClient = useQueryClient();
  const historyQuery = useQuery({
    queryKey: ["round-history"],
    queryFn: async () => {
      const response = await fetch(`${import.meta.env["VITE_GAME_API_URL"] ?? "http://localhost:8000"}/api/game/history`, { cache: "no-store" });
      if (!response.ok) throw new Error("Unable to load round history");
      return response.json() as Promise<Array<{ id: string; round_number: number; threshold: number | null; final: number; result: "over" | "under" | null }>>;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  const settledRoundNumberRef = useRef<number | null>(null);
  const previousRoundNumberRef = useRef<number>(loop.roundNumber);

  useEffect(() => {
    if (loop.phase === "settle" && loop.lastWinner !== null) {
      void queryClient.invalidateQueries({ queryKey: ["round-history"] });
      settledRoundNumberRef.current = loop.roundNumber;
    }

    if (loop.roundNumber !== previousRoundNumberRef.current) {
      void queryClient.invalidateQueries({ queryKey: ["round-history"] });
      previousRoundNumberRef.current = loop.roundNumber;
    }
  }, [loop.phase, loop.roundNumber, loop.lastWinner, queryClient]);

  const history = historyQuery.data ?? [];
  const settleData = loop.phase === 'settle' && loop.lastWinner ? loop.lastWinner : null;

  //const viewportVehicleCount = loop.phase === 'live' ? liveVehicleCount : loop.vehicleCount;

  return (
    <div>
      {/* HERO */}
      <section className="relative border-b border-border">
        <div className="relative mx-auto max-w-7xl px-4 pt-8 pb-12 sm:px-6">
          <p className="label-tech">
            {JUNCTION.name} · {JUNCTION.cameras} cameras
          </p>
          <h1 className="mt-3 max-w-3xl text-4xl leading-[0.95] sm:text-6xl">
            TRAFFIC — Live vehicle-count prediction markets
          </h1>
          <p className="mt-4 max-w-md text-sm text-muted-foreground">
            Place under/over stakes on verified junction vehicle counts. Rounds are settled
            deterministically against camera-verified data and on-chain rules.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href="#market"
              className="clip-tag bg-primary px-5 py-3 font-display text-xs font-bold uppercase tracking-[0.16em] text-primary-foreground"
            >
              View live market
            </a>
            <Link
              to="/how-it-works"
              className="clip-tag border border-primary/60 px-5 py-3 font-display text-xs font-bold uppercase tracking-[0.16em] text-primary"
            >
              How it works
            </Link>
          </div>
        </div>
      </section>

      {/* LIVE MARKET */}
      <section id="market" className="mx-auto max-w-7xl px-4 py-14 sm:px-6">
        {loop.isLoading ? (
          <div className="panel flex min-h-[360px] items-center justify-center p-8 text-center">
            <div>
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary/25 border-t-primary" />
              <p className="label-tech mt-5 text-primary">Loading live round</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Waiting for the game backend to provide the current round data.
              </p>
            </div>
          </div>
        ) : (
          <>
            <PhaseStatus phase={loop.phase} remaining={loop.secondsLeft} totalForPhase={loop.totalForPhase} />

            <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="grid gap-4 content-start">
            <LiveStream
              phase={loop.phase}
              //vehicleCount={viewportVehicleCount}
              settleData={settleData}
              threshold={loop.threshold}
              videoUrl={loop.videoUrl}
              playbackTime={loop.playbackTime}
              locationName={loop.locationName}
              timelineEvents={loop.timelineEvents}
            />

            <div className="mt-3 flex items-start gap-2 max-w-xl text-sm text-muted-foreground">
              <AlertTriangle className="h-4 w-4 text-warning mt-0.5" />
              <span>AI counting can be inaccurate on low-light, occluded, or poor-weather footage</span>
            </div>

            <div className="grid gap-4 sm:grid-cols-3" />
          </div>

          <StakePanel
            key={loop.roundId || loop.roundNumber}
            roundId={loop.roundId}
            phase={loop.phase}
            roundNumber={loop.roundNumber}
            threshold={loop.threshold}
            pool={loop.pool}
          />
            </div>
          </>
        )}

        {/* HISTORY */}
        <div className="mt-14">
            <SectionHeading eyebrow="Settled rounds" title="Recent settled rounds">
            Each round settles to the verified junction vehicle count. Results and settlement
            data are public and reproducible.
          </SectionHeading>
          <div className="panel mt-6 overflow-x-auto">
            <table className="w-full min-w-[420px] border-collapse text-left">
              <thead>
                <tr className="border-b border-border">
                  <th className="label-tech px-4 py-3">Round</th>
                  <th className="label-tech px-4 py-3">Threshold</th>
                  <th className="label-tech px-4 py-3">Final</th>
                  <th className="label-tech px-4 py-3 text-right">Result</th>
                </tr>
              </thead>
              <tbody>
                {historyQuery.isLoading ? (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-sm text-muted-foreground">Loading history…</td></tr>
                ) : history.map((r) => (
                  <tr key={r.round_number} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      #{r.round_number.toString().slice(-6)}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">{r.threshold ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-sm tabular-nums">{r.final}</td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={
                          r.result === "over"
                            ? "clip-tag bg-emerald-500/15 border border-emerald-500 transition-colors px-2 py-0.5 font-mono text-[0.625rem] uppercase"
                            : "clip-tag bg-rose-400/15 border border-rose-400 transition-colors px-2 py-0.5 font-mono text-[0.625rem] uppercase"
                        }
                      >
                        {r.result ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>


        {/* Demo notice removed for production */}
      </section>
    </div>
  );
}
