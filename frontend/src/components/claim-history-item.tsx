import { ExternalLink } from "lucide-react";

interface ClaimHistoryItemProps {
  txHash: string;
  status: string;
  explorerUrl: string;
}

export function ClaimHistoryItem({ txHash, status, explorerUrl }: ClaimHistoryItemProps) {
  return (
    <div className="mt-4 rounded-3xl border border-border bg-background/90 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Last claim</p>
          <p className="text-xs text-muted-foreground">{status}</p>
        </div>
        <a
          href={explorerUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          View
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>
      <p className="mt-3 font-mono text-sm text-muted-foreground break-all">{txHash}</p>
    </div>
  );
}
