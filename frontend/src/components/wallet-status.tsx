import { useMemo, useState } from "react";
import { Copy, LogOut, Link as LinkIcon, RefreshCcw, Wallet as WalletIcon } from "lucide-react";
import { toast } from "sonner";

import { useWallet } from "@/hooks/useWallet";
import { shortenAddress } from "@/services/blockchain/utils";
import { ROBINHOOD_CHAIN_INFO } from "@/services/blockchain/constants";

const explorerUrl = ROBINHOOD_CHAIN_INFO.explorerUrl;

export function WalletStatus() {
  const wallet = useWallet();
  const [menuOpen, setMenuOpen] = useState(false);

  const addressLabel = useMemo(
    () => (wallet.address ? shortenAddress(wallet.address) : "No wallet"),
    [wallet.address],
  );

  const networkBadge = wallet.isCorrectNetwork ? (
    <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-semibold uppercase text-emerald-900">
      {ROBINHOOD_CHAIN_INFO.chainName}
    </span>
  ) : (
    <button
      onClick={wallet.switchNetwork}
      className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-semibold uppercase text-amber-900 hover:bg-amber-200"
    >
      Switch network
    </button>
  );

  const toggleMenu = async () => {
    if (!wallet.address) return;
    setMenuOpen((current) => !current);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={toggleMenu}
        className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition hover:bg-primary/15"
      >
        <WalletIcon className="h-4 w-4" />
        <span>{addressLabel}</span>
      </button>

      {menuOpen && wallet.address ? (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-2xl border border-border bg-background p-4 shadow-lg shadow-black/5">
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3 rounded-2xl bg-surface-2/80 px-3 py-2">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Connected</p>
                <p className="font-mono text-sm text-foreground">{addressLabel}</p>
              </div>
              {networkBadge}
            </div>

            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(wallet.address ?? "");
                toast.success("Address copied");
              }}
              className="flex w-full items-center justify-between rounded-2xl border border-border bg-background px-3 py-3 text-left text-sm text-foreground transition hover:border-primary"
            >
              <span>Copy address</span>
              <Copy className="h-4 w-4 text-primary" />
            </button>

            <a
              href={`${explorerUrl}/address/${wallet.address}`}
              target="_blank"
              rel="noreferrer"
              className="flex w-full items-center justify-between rounded-2xl border border-border bg-background px-3 py-3 text-left text-sm text-foreground transition hover:border-primary"
            >
              <span>View on explorer</span>
              <LinkIcon className="h-4 w-4 text-primary" />
            </a>

            <button
              type="button"
              onClick={async () => {
                await wallet.disconnect();
                toast.success("Wallet disconnected");
                setMenuOpen(false);
              }}
              className="flex w-full items-center justify-between rounded-2xl border border-destructive/40 bg-destructive/5 px-3 py-3 text-left text-sm text-destructive transition hover:bg-destructive/10"
            >
              <span>Disconnect</span>
              <LogOut className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={wallet.refreshBalances}
              className="flex w-full items-center justify-between rounded-2xl border border-border bg-background px-3 py-3 text-left text-sm text-foreground transition hover:border-primary"
            >
              <span>Refresh balance</span>
              <RefreshCcw className="h-4 w-4 text-primary" />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
