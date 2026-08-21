import { ArrowRight, ShieldCheck } from "lucide-react";
import { ClaimStatusBadge } from "@/components/claim-status-badge";
import { RewardBreakdown } from "@/components/reward-breakdown";

import type { ClaimStatus } from "@/services/blockchain/types";

interface ClaimRewardCardProps {
  claimableEth: string;
  claimableRush: string;
  claimStatus: ClaimStatus;
  hasParticipated: boolean;
  isWalletConnected: boolean;
  wrongNetwork: boolean;
  submitting: boolean;
  disabled: boolean;
  statusMessage: string | null;
  errorMessage: string | null;
  estimatedGas: string | null;
  estimatedGasError: string | null;
  onClaim: () => Promise<void>;
}

export function ClaimRewardCard({
  claimableEth,
  claimableRush,
  claimStatus,
  hasParticipated,
  isWalletConnected,
  wrongNetwork,
  submitting,
  disabled,
  statusMessage,
  errorMessage,
  estimatedGas,
  estimatedGasError,
  onClaim,
}: ClaimRewardCardProps) {
  return (
    <div className="mt-6 rounded-3xl border border-border bg-surface-2/70 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="label-tech">Reward claim</p>
          <p className="mt-1 text-sm text-muted-foreground">Claim your settled ETH and minted RUSH rewards.</p>
        </div>
        <ClaimStatusBadge status={claimStatus} />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <RewardBreakdown label="Claimable ETH" amount={claimableEth} symbol="ETH" />
        <RewardBreakdown label="Claimable RUSH" amount={claimableRush} symbol="RUSH" />
      </div>

      <div className="mt-4 grid gap-3 rounded-3xl border border-border bg-background p-4">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Estimated gas</span>
          <span>{estimatedGas ? `${estimatedGas} gas` : "n/a"}</span>
        </div>
        {estimatedGasError ? (
          <div className="rounded-2xl bg-amber-100/80 px-3 py-2 text-xs text-amber-900">
            {estimatedGasError}
          </div>
        ) : null}
      </div>

      {statusMessage ? (
        <div className="mt-4 rounded-3xl bg-slate-100 px-4 py-3 text-sm text-slate-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="mt-4 rounded-3xl bg-rose-100 px-4 py-3 text-sm text-rose-900">{errorMessage}</div>
      ) : null}

      <button
        type="button"
        onClick={onClaim}
        disabled={disabled || submitting || !isWalletConnected || wrongNetwork}
        className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-3xl bg-primary px-4 py-3 text-sm font-bold uppercase tracking-[0.16em] text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? "Claiming..." : "Claim rewards"}
        <ArrowRight className="h-4 w-4" />
      </button>

      {!isWalletConnected ? (
        <p className="mt-3 text-center text-xs text-muted-foreground">Connect wallet to view claim eligibility.</p>
      ) : null}
      {wrongNetwork ? (
        <p className="mt-3 text-center text-xs text-amber-900">Switch to the Robinhood Chain to claim.</p>
      ) : null}
      {!hasParticipated ? (
        <p className="mt-3 text-center text-xs text-muted-foreground">You must have participated in the settled round to claim rewards.</p>
      ) : null}
    </div>
  );
}
