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
  const [betHistory, setBetHistory] = useState<Array<{ roundNumber: bigint; side: string; amount: string; active: boolean }>>([]);
  const [claimableWins, setClaimableWins] = useState<Array<{ roundNumber: bigint; gross: string; claimed: boolean }>>([]);
  
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

        // Enrich each bet with `active` flag by querying round info
        const enriched = await Promise.all(raw.map(async (r) => {
          try {
            const roundInfo: any = await wallet.provider!.readContract({
              address: import.meta.env["VITE_BETTING_CONTRACT_ADDRESS"] as Address,
              abi: (await import("@/services/blockchain/RushBetting.json")).abi,
              functionName: "getRoundInfo",
              args: [r.roundNumber],
            });
            const settled = Boolean(roundInfo?.settled);
            return { roundNumber: r.roundNumber, side: r.side, amount: formatUnits(r.amount, 18), active: !settled };
          } catch (err) {
            return { roundNumber: r.roundNumber, side: r.side, amount: formatUnits(r.amount, 18), active: false };
          }
        }));

        if (cancelled) return;
        setBetHistory(enriched);

        // Also fetch claimable wins to render claim buttons for settled rounds
        const claims = await BettingContractService.getRushRewardHistory(wallet.provider, wallet.address as Address, 50);
        if (cancelled) return;
        setClaimableWins(claims.map((c) => ({ roundNumber: c.roundNumber, gross: formatUnits(c.gross, 18), claimed: c.claimed })));
      } catch (error) {
        console.debug("[WalletPage] getBetHistory failed", error);
        if (!cancelled) {
          setBetHistory([]);
          setClaimableWins([]);
        }
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

      {/* Scorecards */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="clip-tag p-4 border border-border bg-surface/60">
          <p className="label-tech text-xs">Active Positions</p>
          <p className="mt-2 text-2xl font-mono">{betHistory.filter((b) => b.active).length}</p>
        </div>
        <div className="clip-tag p-4 border border-border bg-surface/60">
          <p className="label-tech text-xs">Claimable Wins</p>
          <p className="mt-2 text-2xl font-mono">{claimableWins.filter((c) => !c.claimed).length}</p>
        </div>
        <div className="clip-tag p-4 border border-border bg-surface/60">
          <p className="label-tech text-xs">Total Bets</p>
          <p className="mt-2 text-2xl font-mono">{betHistory.length}</p>
        </div>
      </div>

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

          {/* Claimable wins for settled rounds */}
          <div className="mt-6">
            <SectionHeading eyebrow="Claim" title="Claimable wins" />
            <div className="mt-3 space-y-3">
              {claimableWins.length === 0 ? (
                <div className="clip-tag border border-border bg-surface/60 p-4 text-sm text-muted-foreground">No claimable wins</div>
              ) : (
                claimableWins.map((c) => (
                  <div key={c.roundNumber.toString()} className="clip-tag flex items-center justify-between border border-border bg-surface/60 p-3">
                    <div className="min-w-0">
                      <p className="font-display text-sm">Round #{c.roundNumber.toString()}</p>
                      <p className="label-tech mt-1 text-xs text-muted-foreground">Winnings: {c.gross} {ticker}</p>
                    </div>
                    <div>
                      <button
                        disabled={c.claimed || !wallet.signer}
                        onClick={async () => {
                          if (!wallet.signer) return;
                          try {
                            // If this round had a buyback, claim tokens via `claimStock` per-token.
                            const tokens = await BettingContractService.getRoundBoughtTokens(wallet.provider!, Number(c.roundNumber));
                            if (tokens && tokens.length > 0) {
                              for (const t of tokens) {
                                const txHash = await BettingContractService.claimStock(wallet.signer, Number(c.roundNumber), t as Address);
                                await wallet.provider?.waitForTransactionReceipt({ hash: txHash as string });
                              }
                              toast.success("Token claims submitted");
                            } else {
                              const txHash = await BettingContractService.claimEth(wallet.signer, Number(c.roundNumber));
                              await wallet.provider?.waitForTransactionReceipt({ hash: txHash as string });
                              toast.success("Claim submitted");
                            }
                          } catch (err) {
                            toast.error((err as Error).message || "Claim failed");
                          }
                        }}
                        className="clip-tag border border-primary/60 px-3 py-2 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {c.claimed ? "Claimed" : "Claim"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        <div>
          <SectionHeading eyebrow="Activity" title="Your positions" />
          <div className="mt-6 grid gap-3">
            {betHistory.filter(b => b.active).length === 0 && (
              <div className="clip-tag border border-border bg-surface/60 p-6 text-sm text-muted-foreground">
                No positions yet. Take a side on the live round.
              </div>
            )}
            {betHistory.filter(b => b.active).map((s) => (
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
                    {(() => {
                      const claimableMap = new Map(claimableWins.map((c) => [c.roundNumber.toString(), c.claimed]));
                      return betHistory.map((h) => {
                        const key = h.roundNumber.toString();
                        const isClaimable = claimableMap.has(key);
                        const isClaimed = Boolean(claimableMap.get(key));
                        return (
                          <div key={`${h.roundNumber.toString()}-${h.side}`} className="clip-tag flex items-center justify-between border border-border bg-surface/60 p-3">
                            <div className="min-w-0">
                              <p className="font-display text-sm uppercase">{h.side}</p>
                              <p className="label-tech mt-1 text-xs text-muted-foreground">Round #{h.roundNumber.toString().slice(-6)}</p>
                              {isClaimable && !isClaimed && (
                                <span className="label-tech mt-1 text-xs text-amber-500">Claimable</span>
                              )}
                              {isClaimable && isClaimed && (
                                <span className="label-tech mt-1 text-xs text-emerald-500">Claimed</span>
                              )}
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="text-right font-mono text-sm text-primary">{Number(h.amount).toFixed(3)} {ticker}</div>
                              {isClaimable && (
                                <button
                                  disabled={isClaimed || !wallet.signer}
                                  onClick={async () => {
                                    if (!wallet.signer) return;
                                    try {
                                      try {
                                        const tokens = await BettingContractService.getRoundBoughtTokens(wallet.provider!, Number(h.roundNumber));
                                        if (tokens && tokens.length > 0) {
                                          for (const t of tokens) {
                                            const txHash = await BettingContractService.claimStock(wallet.signer, Number(h.roundNumber), t as Address);
                                            await wallet.provider?.waitForTransactionReceipt({ hash: txHash as string });
                                          }
                                          toast.success("Token claims submitted");
                                        } else {
                                          const txHash = await BettingContractService.claimEth(wallet.signer, Number(h.roundNumber));
                                          await wallet.provider?.waitForTransactionReceipt({ hash: txHash as string });
                                          toast.success("Claim submitted");
                                        }
                                      } catch (err) {
                                        toast.error((err as Error).message || "Claim failed");
                                      }
                                    } catch (err) {
                                      toast.error((err as Error).message || "Claim failed");
                                    }
                                  }}
                                  className="clip-tag border border-primary/60 px-3 py-2 font-display text-xs font-bold uppercase tracking-[0.14em] text-primary disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                  {isClaimed ? "Claimed" : "Claim"}
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>
                )}
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
