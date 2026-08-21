import { type ClaimStatus } from "@/services/blockchain/types";

const STATUS_STYLES: Record<ClaimStatus, string> = {
  unknown: "bg-slate-100 text-slate-800",
  available: "bg-emerald-100 text-emerald-900",
  already_claimed: "bg-rose-100 text-rose-900",
  none: "bg-amber-100 text-amber-900",
};

const STATUS_LABELS: Record<ClaimStatus, string> = {
  unknown: "Unknown",
  available: "Claim available",
  already_claimed: "Already claimed",
  none: "No reward",
};

interface ClaimStatusBadgeProps {
  status: ClaimStatus;
}

export function ClaimStatusBadge({ status }: ClaimStatusBadgeProps) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}
