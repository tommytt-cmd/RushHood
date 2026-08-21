import { ArrowDown, ArrowUp, CircleDollarSign, Loader2 } from "lucide-react";

interface BetSlipProps {
  side: "under" | "over";
  amount: string;
  walletBalance: number;
  potentialRush: string;
  protocolFee?: string;
  onAmountChange: (amount: string) => void;
  onSubmit: () => Promise<void>;
  submitting?: boolean;
  disabled: boolean;
  closed: boolean;
  statusMessage: string | null;
  errorMessage: string | null;
}

export function BetSlip({
  side,
  amount,
  walletBalance,
  potentialRush,
  protocolFee,
  onAmountChange,
  onSubmit,
  submitting,
  disabled,
  closed,
  statusMessage,
  errorMessage,
}: BetSlipProps) {
  return (
    <div className="mt-6 rounded-3xl">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="label-tech">Bet slip</p>
          <p className="mt-1 text-sm text-muted-foreground">Review the transaction before confirming.</p>
        </div>
        <div className="rounded-full bg-primary/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-primary">
          {side}
        </div>
      </div>

      <div className="mt-5 space-y-4">
        <div className="grid gap-2">
          <label className="label-tech">Amount (ETH)</label>
          <input
            type="number"
            min={0}
            step="0.001"
            value={amount}
            onChange={(event) => onAmountChange(event.target.value)}
            className="clip-tag w-full border border-input bg-background px-4 py-3 font-mono text-sm outline-none focus:border-primary"
          />
        </div>

        {/*<div className="grid gap-2 rounded-3xl border border-border bg-background p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Wallet balance</span>
            <span>{walletBalance.toFixed(4)} ETH</span>
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Potential RUSH reward</span>
            <span>{potentialRush} RUSH</span>
          </div>
          {protocolFee ? (
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Protocol fee</span>
              <span>{protocolFee} ETH</span>
            </div>
          ) : null}
        </div>*/}

        {/*statusMessage ? (
          <p className="rounded-2xl bg-surface/70 px-4 py-3 text-sm text-muted-foreground">{statusMessage}</p>
        ) : null}
        {errorMessage ? (
          <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-900">{errorMessage}</p>
        ) : null*/}

        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || submitting}
          aria-busy={submitting ? "true" : "false"}
          //className="w-full rounded-3xl bg-primary px-4 py-3 text-sm font-bold uppercase tracking-[0.16em] text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center gap-2"
          className="w-full clip-tag bg-primary py-2.5 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing…
            </>
          ) : (closed ? "Round closed" : disabled ? "Cannot place bet" :
            "Place bet"
          )}
        </button>
      </div>
    </div>
  );
}
