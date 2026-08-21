interface RewardSummaryProps {
  label: string;
  value: string;
  symbol: string;
}

export function RewardSummary({ label, value, symbol }: RewardSummaryProps) {
  return (
    <div className="grid gap-1 rounded-3xl border border-border bg-background/80 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold text-foreground">
        {value} <span className="text-sm text-muted-foreground">{symbol}</span>
      </p>
    </div>
  );
}
