import { createFileRoute } from "@tanstack/react-router";
import React from "react";

// hero image removed for production copy
import { Panel, SectionHeading } from "@/components/panel";
import { AlertTriangle } from "lucide-react";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About TRAFFIC — Vehicle Count Prediction Markets" },
      {
        name: "description",
        content:
          "TRAFFIC turns public junction camera feeds into transparent under/over prediction markets on live vehicle counts.",
      },
      { property: "og:title", content: "About TRAFFIC — Vehicle Count Prediction Markets" },
      {
        property: "og:description",
        content: "Why we built open markets on top of live traffic-count telemetry.",
      },
    ],
  }),
  component: About,
});

function About() {
  // track active section for the left nav
  const sections = [
    'overview',
    'how-it-works',
    'utility',
    'participate',
    'data-and-settlement',
    'security',
    'roadmap',
    'contribute',
  ];

  const titles: Record<string, string> = {
    overview: 'Overview',
    'how-it-works': 'How it works',
    utility: 'Token & utility',
    participate: 'How to participate',
    'data-and-settlement': 'Data & settlement',
    security: 'Security & audits',
    roadmap: 'Roadmap',
    contribute: 'Contribute & contact',
  };

  const [active, setActive] = React.useState('overview');

  React.useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { root: null, rootMargin: '-40% 0px -40% 0px', threshold: 0 }
    );

    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) obs.observe(el);
    });

    return () => obs.disconnect();
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div className="mb-8">
        <p className="label-tech">About</p>
        <h1 className="mt-3 max-w-3xl text-4xl leading-[0.95] sm:text-5xl">RushHood — TRAFFIC</h1>
        <p className="mt-4 max-w-2xl text-sm text-muted-foreground">
          RushHood builds TRAFFIC: on-chain prediction markets that resolve to live vehicle counts
          produced by public junction camera feeds. Markets are short, verifiable, and settled
          transparently on-chain so anyone can audit outcomes and reward distribution.
        </p>
      </div>

      <div className="md:flex md:gap-8">
        <aside className="mb-6 md:w-1/4">
          <nav className="sticky top-20 space-y-2">
            {[
              ['overview', 'Overview'],
              ['how-it-works', 'How it works'],
              ['utility', 'Token & utility'],
              ['participate', 'Participate'],
              ['data-and-settlement', 'Data & settlement'],
              ['security', 'Security'],
              ['roadmap', 'Roadmap'],
              ['contribute', 'Contribute'],
            ].map(([id, label]) => (
              <a
                key={id}
                href={`#${id}`}
                className={`block label-tech transition-colors px-2 py-1 rounded ${
                  active === id ? 'text-primary font-medium bg-surface/40 border-l-2 border-primary' : 'text-muted-foreground'
                }`}
              >
                {label}
              </a>
            ))}
          </nav>
        </aside>

        <main className="prose max-w-none md:w-3/4">
          <div className="sticky top-16 z-10 mb-4">
            <div className="inline-block rounded-md bg-surface-2/80 px-3 py-1 text-sm font-medium text-foreground shadow-sm backdrop-blur-sm">
              {titles[active]}
            </div>
          </div>
          <section id="overview">
            <SectionHeading eyebrow="Docs" title="Overview" />
            <p>
              RushHood's TRAFFIC product turns public traffic camera telemetry into rapid under/over
              markets. Each market (round) proposes a public threshold and accepts stakes on two
              outcomes. After the round closes, an archived camera count is used to resolve the
              market and distribute rewards on-chain.
            </p>
          </section>

          <Panel className="mb-6">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
              <div>
                <p className="label-tech">Note</p>
                <p className="mt-1 text-sm text-muted-foreground">AI-generated counts may be inaccurate — verify archived footage for important outcomes.</p>
              </div>
            </div>
          </Panel>

          <section id="how-it-works">
            <SectionHeading eyebrow="Design" title="How it works" />
            <ol className="list-decimal pl-6">
              <li>
                Market open — a junction and threshold are published; users place under/over bets.
              </li>
              <li>Locking — bets are locked while the observation window passes.</li>
              <li>
                Observation — the camera feed produces a verified count; the count is archived and
                timestamped.
              </li>
              <li>Settlement — the archived count is used to settle the market and distribute rewards.</li>
            </ol>
          </section>

          <section id="utility">
            <SectionHeading eyebrow="Token" title="Token & utility" />
            <p>
              The platform token (RUSH) is used for holder governance, staking rewards, and aligning
              incentives across operators and participants. Token holders may be eligible for
              protocol fees, rewards for operating or sponsoring feeds, and future governance
              privileges.
            </p>
          </section>

          <section id="participate">
            <SectionHeading eyebrow="Participation" title="How to participate" />
            <ul>
              <li>Connect a web3 wallet to view live markets and your balances.</li>
              <li>Place bets on under/over outcomes during the open phase.</li>
              <li>After settlement, winners can withdraw their on-chain rewards via the wallet page.</li>
            </ul>
          </section>

          <section id="data-and-settlement">
            <SectionHeading eyebrow="Data" title="Data & settlement" />
            <p>
              We rely on public junction cameras and an auditable archival process. Each settled
              round includes the raw count and a timestamp so anyone can verify the recorded value
              and confirm correct on-chain settlement.
            </p>
          </section>

          <section id="security">
            <SectionHeading eyebrow="Safety" title="Security & audits" />
            <p>
              Smart contracts are the source of truth for market lifecycle and funds. Contracts are
              written to minimize trust assumptions; we recommend following our audit reports and
              verifying copy of contracts on the network explorer before interacting with large
              amounts.
            </p>
          </section>

          <section id="roadmap">
            <SectionHeading eyebrow="Plan" title="Roadmap" />
            <p>
              Upcoming items include additional junction onboarding, richer market types, deeper
              analytics, and improved incentive mechanisms for data providers and token holders.
            </p>
          </section>

          <section id="contribute">
            <SectionHeading eyebrow="Community" title="Contribute & contact" />
            <p>
              Contributions are welcome — open issues, audits, UI improvements, and integrations.
              For partnership or operator onboarding, contact the team via the project repository or
              the community channels linked in the footer.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
}
