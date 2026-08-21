import { useEffect, useState } from "react";
import type { Address } from "viem";
import { formatUnits } from "viem";
import { createFileRoute } from "@tanstack/react-router";
import { Wallet as WalletIcon, LogOut } from "lucide-react";
import { toast } from "sonner";

import { Panel, SectionHeading } from "@/components/panel";
import { shortAddress } from "@/lib/round";
import { useWallet as useBlockchainWallet } from "@/hooks/useWallet";
import { useBettingContract } from "@/hooks/useBettingContract";
import { BettingContractService } from "@/services/blockchain/bettingContractService";
// Claim-related UI and transaction helpers removed
import { walletStore } from "@/lib/store";

const ticker = import.meta.env["TICKER"] ?? 'ETH';

export const Route = createFileRoute("/wallet")({
  head: () => ({
    meta: [
      { title: "Wallet — TRAFFIC Credits and Positions" },
      {
        name: "description",
        content:
          "Connect a wallet, manage TRAFFIC credits and review your under/over positions across settled vehicle-count rounds.",
      },
      { property: "og:title", content: "Wallet — TRAFFIC Credits and Positions" },
      {
        property: "og:description",
        content: "Manage credits and track your under/over positions on live traffic rounds.",
      },
    ],
  }),
  component: WalletPage,
});

const PROVIDERS = ["MetaMask", "Coinbase Wallet", "Browser Wallet", "WalletConnect"] as const;

function WalletPage() {
  const wallet = useBlockchainWallet();
  const betting = useBettingContract();
  const [amount, setAmount] = useState(0.1);
  const [betHistory, setBetHistory] = useState<Array<{ roundNumber: bigint; side: string; amount: string }>>([]);
  
  const [holderShares, setHolderShares] = useState("0");
  const [pendingHolderRewards, setPendingHolderRewards] = useState("0");
  const [holderVaultAddress, setHolderVaultAddress] = useState<Address | null>(null);
  const [claimingHolderRewards, setClaimingHolderRewards] = useState(false);
  const [withdrawableRush, setWithdrawableRush] = useState("0");
  const [withdrawingRush, setWithdrawingRush] = useState(false);

  useEffect(() => {
    // claim state reads removed
  }, [wallet.connected, wallet.provider, wallet.address]);

  // claim gas estimation removed

  useEffect(() => {
    if (!wallet.provider || !wallet.address) return;
    void BettingContractService.getHolderPosition(wallet.provider, wallet.address as Address)
      .then((position) => {
        setHolderVaultAddress(position.holderVaultAddress ?? null);
        setHolderShares(formatUnits(position.shares, 18));
        setPendingHolderRewards(formatUnits(position.pendingRewards, 18));
        setWithdrawableRush(formatUnits(position.netAmount, 18));
      })
      .catch(() => {
        setHolderVaultAddress(null);
        setHolderShares("0");
        setPendingHolderRewards("0");
        setWithdrawableRush("0");
      });
  }, [wallet.provider, wallet.address]);

  useEffect(() => {
    if (!wallet.provider || !wallet.address) return;
    let cancelled = false;
    (async () => {
      try {
        const raw = await BettingContractService.getBetHistory(wallet.provider, wallet.address as Address, 50);
        if (cancelled) return;
        setBetHistory(raw.map((r) => ({ roundNumber: r.roundNumber, side: r.side, amount: formatUnits(r.amount, 18) })));
      } catch (error) {
        console.debug("[WalletPage] getBetHistory failed", error);
        if (!cancelled) setBetHistory([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [wallet.provider, wallet.address]);

  async function handleClaimHolderRewards() {
    if (!wallet.signer || !holderVaultAddress) return;
    setClaimingHolderRewards(true);
    try {
      const txHash = await BettingContractService.claimHolderRewards(wallet.signer, holderVaultAddress);
      await wallet.provider?.waitForTransactionReceipt({ hash: txHash });
      toast.success("Holder rewards claimed.");
      if (wallet.provider && wallet.address) {
        const position = await BettingContractService.getHolderPosition(wallet.provider, wallet.address as Address);
        setHolderShares(formatUnits(position.shares, 18));
        setPendingHolderRewards(formatUnits(position.pendingRewards, 18));
        setWithdrawableRush(formatUnits(position.netAmount, 18));
      }
    } catch (error) {
      toast.error((error as Error).message || "Unable to claim holder rewards.");
    } finally {
      setClaimingHolderRewards(false);
    }
  }

  async function handleWithdrawRush() {
    if (!wallet.signer || !holderVaultAddress) return;
    setWithdrawingRush(true);
    try {
      const txHash = await BettingContractService.withdrawAllRush(wallet.signer, holderVaultAddress);
      await wallet.provider?.waitForTransactionReceipt({ hash: txHash });
      toast.success("Staked RUSH withdrawn.");
      if (wallet.provider && wallet.address) {
        const position = await BettingContractService.getHolderPosition(wallet.provider, wallet.address as Address);
        setHolderShares(formatUnits(position.shares, 18));
        setPendingHolderRewards(formatUnits(position.pendingRewards, 18));
        setWithdrawableRush(formatUnits(position.netAmount, 18));
      }
    } catch (error) {
      toast.error((error as Error).message || "Unable to withdraw staked RUSH.");
    } finally {
      setWithdrawingRush(false);
    }
  }

  // reward claim handler removed

  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
      <p className="label-tech">Account</p>
      <h1 className="mt-3 text-4xl leading-[0.95] sm:text-5xl">Wallet</h1>

      <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <Panel>
          {wallet.address ? (
            <>
              <p className="label-tech text-emerald-500">Connected · {wallet.providerName ?? wallet.status}</p>
              <p className="mt-2 font-mono text-lg text-primary">
                {shortAddress(wallet.address)}
              </p>
              <p className="label-tech mt-6">Withdrawable ETH</p>
              <p className="font-display text-5xl text-primary">
                {Number(betting.claimableEth || "0").toFixed(3)}
                <span className="ml-2 text-base text-muted-foreground">{ticker}</span>
              </p>

              <div className="mt-6 clip-tag border border-border bg-surface/60 p-4">
                <p className="label-tech">RUSH staking position</p>
                <p className="mt-2 font-mono text-sm">{holderShares} shares</p>
                <p className="mt-1 font-mono text-sm">Withdrawable: {withdrawableRush} RUSH</p>
                <p className="mt-1 font-mono text-sm text-primary">{pendingHolderRewards} RUSH holder rewards</p>
                <button
                  onClick={handleClaimHolderRewards}
                  disabled={!holderVaultAddress || Number(pendingHolderRewards) <= 0 || claimingHolderRewards}
                  className="clip-tag mt-3 border border-primary/60 px-3 py-2 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {claimingHolderRewards ? "Claiming…" : "Claim holder rewards"}
                </button>
                <button
                  onClick={handleWithdrawRush}
                  disabled={!holderVaultAddress || Number(holderShares) <= 0 || withdrawingRush}
                  className="clip-tag ml-3 mt-3 border border-primary/60 px-3 py-2 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {withdrawingRush ? "Withdrawing…" : "Withdraw RUSH"}
                </button>
              </div>

              {/* Claim rewards UI removed */}

              <div className="mt-6">
                <input
                  type="number"
                  min={1}
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full border border-input bg-background px-3 py-2 font-mono text-sm outline-none focus:border-primary"
                />
                <div className="mt-3 grid grid-cols-1 gap-3">
                  <button
                    onClick={() => {
                      walletStore.withdraw(amount);
                      toast.success(`Withdrew ${amount} CR`);
                    }}
                    className="clip-tag bg-primary py-2.5 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary-foreground"
                  >
                    Withdraw
                  </button>
                </div>
              </div>

              <button
                onClick={async () => {
                  await wallet.disconnect();
                  toast.success("Wallet disconnected");
                }}
                className="mt-6 inline-flex items-center gap-2 font-mono text-xs text-destructive"
              >
                <LogOut className="h-3.5 w-3.5" /> Disconnect
              </button>
            </>
          ) : (
            <>
              <WalletIcon className="h-6 w-6 text-primary" />
              <h2 className="mt-4 text-2xl">Connect a wallet</h2>
              
              <div className="mt-6 grid gap-3">
                {PROVIDERS.map((p) => (
                  <button
                    key={p}
                    onClick={async () => {
                      try {
                        await wallet.connect(p);
                        toast.success(`${p} connected`);
                      } catch (error) {
                        toast.error((error as Error).message || "Unable to connect wallet");
                      }
                    }}
                    className="clip-tag flex items-center justify-between border border-border bg-surface-2/60 px-4 py-3 text-left transition-colors hover:border-primary"
                  >
                    <span className="font-display text-sm font-bold uppercase tracking-[0.12em]">
                      {p}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">connect</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </Panel>

        <div>
          <SectionHeading eyebrow="Activity" title="Your positions" />
          <div className="mt-6 grid gap-3">
            {betHistory.length === 0 && (
              <div className="clip-tag border border-border bg-surface/60 p-6 text-sm text-muted-foreground">
                No positions yet. Take a side on the live round.
              </div>
            )}
            {betHistory.map((s) => (
              <div
                key={`${s.roundNumber.toString()}-${s.side}`}
                className="clip-tag grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border border-border bg-surface/60 p-4"
              >
                <div className="min-w-0">
                  <p className="font-display text-lg uppercase">
                    {s.side} {Number(s.roundNumber).toString()}
                  </p>
                  <p className="label-tech mt-1">
                    Round #{s.roundNumber.toString().slice(-6)}
                  </p>
                </div>
                <p className="shrink-0 font-mono text-sm text-primary">
                  {Number(s.amount).toFixed(3)} {ticker}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-8 lg:mt-0">
          <SectionHeading eyebrow="History" title="Betting history" />
          <div className="mt-4">
            <Panel>
                {betHistory.length === 0 ? (
                  <div className="clip-tag border border-border bg-surface/60 p-6 text-sm text-muted-foreground">
                    No betting history yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {betHistory.map((h) => (
                      <div key={`${h.roundNumber.toString()}-${h.side}`} className="clip-tag flex items-center justify-between border border-border bg-surface/60 p-3">
                        <div className="min-w-0">
                          <p className="font-display text-sm uppercase">{h.side}</p>
                          <p className="label-tech mt-1 text-xs text-muted-foreground">Round #{h.roundNumber.toString().slice(-6)}</p>
                        </div>
                        <div className="text-right font-mono text-sm text-primary">{Number(h.amount).toFixed(3)} {ticker}</div>
                      </div>
                    ))}
                  </div>
                )}
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
