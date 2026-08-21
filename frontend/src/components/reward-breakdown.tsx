interface RewardBreakdownProps {
  label: string;
  amount: string;
  symbol: string;
}

export function RewardBreakdown({ label, amount, symbol }: RewardBreakdownProps) {
  return (
    <div className="flex items-center justify-between rounded-3xl border border-border bg-surface-2/70 px-4 py-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-mono text-sm text-foreground">
        {amount} {symbol}
      </span>
    </div>
  );
}
