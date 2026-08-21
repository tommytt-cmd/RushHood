import { createFileRoute, Link } from "@tanstack/react-router";

import { Panel, SectionHeading } from "@/components/panel";
import { PHASE_COPY, PHASE_DURATIONS, PHASE_ORDER } from "@/lib/round";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "How TRAFFIC Works — Phases, Thresholds, Settlement" },
      {
        name: "description",
        content:
          "Betting, locked, live and settling: how a TRAFFIC vehicle-count round runs, how thresholds are set and how payouts settle.",
      },
      { property: "og:title", content: "How TRAFFIC Works — Phases, Thresholds, Settlement" },
      {
        property: "og:description",
        content: "The four phases of a vehicle-count round and how under/over payouts are settled.",
      },
    ],
  }),
  component: HowItWorks,
});

const STEPS = [
  {
    title: "A window is published",
    body: "Each round names a junction, a counting window and a vehicle threshold derived from the last 24 hours of feed data.",
  },
  {
    title: "You pick a side",
    body: "Stake credits on UNDER or OVER the threshold. Both sides form one pool; odds move with the pool balance.",
  },
  {
    title: "Cameras count",
    body: "During the live phase, four junction cameras count passing vehicles and stream the running total.",
  },
  {
    title: "The round settles",
    body: "The verified final count is compared to the threshold and the winning pool is split pro-rata by stake size.",
  },
];

function HowItWorks() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
      <p className="label-tech">Protocol</p>
      <h1 className="mt-3 max-w-2xl text-4xl leading-[0.95] sm:text-5xl">How TRAFFIC works</h1>
      <p className="mt-4 max-w-xl text-sm text-muted-foreground">
        One question, repeated every three minutes: how many vehicles will the junction count? Every
        round moves through four phases.
      </p>

      <div className="mt-12 grid gap-4 md:grid-cols-4">
        {PHASE_ORDER.map((p, i) => (
          <Panel key={p}>
            <p className="font-mono text-xs text-primary">0{i + 1}</p>
            <h2 className="mt-3 text-xl">{PHASE_COPY[p].label}</h2>
            <p className="label-tech mt-1">{PHASE_DURATIONS[p]}s</p>
            <p className="mt-3 text-sm text-muted-foreground">{PHASE_COPY[p].blurb}</p>
          </Panel>
        ))}
      </div>

      <div className="mt-16">
        <SectionHeading eyebrow="Round lifecycle" title="From feed to payout">
          Thresholds are published before betting opens, so nobody can move the line once positions
          are being taken.
        </SectionHeading>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {STEPS.map((s, i) => (
            <div key={s.title} className="border-l-2 border-primary/50 pl-5">
              <p className="font-mono text-xs text-primary">STEP {i + 1}</p>
              <h3 className="mt-2 text-xl">{s.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{s.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-16">
        <SectionHeading eyebrow="Payouts" title="How odds are calculated" />
        <Panel className="mt-6">
          <p className="font-mono text-sm text-primary">
            payout = your_stake × (under_pool + over_pool) ÷ winning_pool
          </p>
          <p className="mt-4 text-sm text-muted-foreground">
            The unpopular side pays more. If everyone stakes OVER and the count lands under, the few
            UNDER positions split the entire round pool.
          </p>
        </Panel>
      </div>

      <div className="mt-16 flex flex-wrap gap-3">
        <Link
          to="/"
          className="clip-tag bg-primary px-5 py-3 font-display text-xs font-bold uppercase tracking-[0.16em] text-primary-foreground"
        >
          Go to live round
        </Link>
        <Link
          to="/wallet"
          className="clip-tag border border-primary/60 px-5 py-3 font-display text-xs font-bold uppercase tracking-[0.16em] text-primary"
        >
          Set up wallet
        </Link>
      </div>
    </div>
  );
}
