import type { Abi, Address, PublicClient, WalletClient } from "viem";
import type { ClaimStatus } from "./types";
import { ContractFactory } from "./contractFactory";
import { ROBINHOOD_CHAIN_INFO } from "./constants";
import { formatTokenAmount } from "./utils";
// Keep the frontend ABI coupled to the Foundry artifact that is deployed.  The
// previous aliases pointed at files that were never checked into `src`, which
// made every production build fail before a wallet could connect.
import RushBettingArtifact from "./RushBetting.json";
import RushHolderVaultArtifact from "./RushHolderVault.json";

function getBettingContractConfig() {
  const address = import.meta.env["VITE_BETTING_CONTRACT_ADDRESS"] as string | undefined;
  const artifact = RushBettingArtifact as Record<string, any>;
  const abi: Abi | undefined = artifact["abi"] ?? artifact["default"]?.["abi"];

  if (!address) {
    throw new Error("Missing VITE_BETTING_CONTRACT_ADDRESS environment variable.");
  }
  if (!abi || !Array.isArray(abi)) {
    throw new Error(
      "Unable to resolve contract ABI from RushBetting.json. Ensure the imported file exports an object with an `abi` array."
    );
  }

  return { address, abi };
}

export class BettingContractService {
  static async getRushRewardHistory(provider: PublicClient, player: Address, limit = 25) {
    const { address, abi } = getBettingContractConfig();
    const latest = BigInt(await provider.readContract({ address: address as Address, abi, functionName: "latestRound" }) as bigint);
    const holderVaultAddress = await provider.readContract({
      address: address as Address,
      abi,
      functionName: "rushHolderVault",
    }) as Address;
    const holderAbi = (RushHolderVaultArtifact as Record<string, unknown>)["abi"] as Abi;
    const first = latest > BigInt(limit) ? latest - BigInt(limit) + 1n : 1n;
    const rounds = Array.from({ length: Number(latest >= first ? latest - first + 1n : 0n) }, (_, index) => latest - BigInt(index));
    
    const entries = await Promise.all(rounds.map(async (roundNumber) => {
      const [claimable, hasClaimed, isStaked, buyback, holderClaimed] = await Promise.all([
        provider.readContract({ address: address as Address, abi, functionName: "getClaimableRushReward", args: [roundNumber, player] }),
        provider.readContract({ address: address as Address, abi, functionName: "hasClaimedRush", args: [roundNumber, player] }),
        provider.readContract({ address: address as Address, abi, functionName: "isRushRewardStaked", args: [roundNumber, player] }),
        provider.readContract({ address: address as Address, abi, functionName: "getRoundRushBuyback", args: [roundNumber] }),
        holderVaultAddress && holderVaultAddress !== "0x0000000000000000000000000000000000000000"
          ? provider.readContract({ address: holderVaultAddress, abi: holderAbi, functionName: "hasClaimedRushRewardStake", args: [roundNumber, player] }).catch(() => false)
          : Promise.resolve(false),
      ]);

      const safeClaimable = BigInt(claimable?.toString() ?? "0");
      const safeBuyback = BigInt(buyback?.toString() ?? "0");

      // FIXED: If the automated keeper has finalized it, it is automatically staked and ready!
      return { 
        roundNumber, 
        gross: safeClaimable, 
        claimed: Boolean(hasClaimed), 
        staked: Boolean(isStaked) || Boolean(hasClaimed) || Boolean(holderClaimed),
        buyback: safeBuyback 
      };
    }));
    
    return entries.filter((entry) => entry.gross > 0n || entry.claimed || entry.staked);
  }

  static async getBetHistory(provider: PublicClient, player: Address, limit = 25) {
    const { address, abi } = getBettingContractConfig();
    const latest = BigInt(await provider.readContract({ address: address as Address, abi, functionName: "latestRound" }) as bigint);
    const first = latest > BigInt(limit) ? latest - BigInt(limit) + 1n : 1n;
    const rounds = Array.from({ length: Number(latest >= first ? latest - first + 1n : 0n) }, (_, index) => latest - BigInt(index));

    const entries = await Promise.all(rounds.map(async (roundNumber) => {
      try {
        const userBet = await BettingContractService.getUserBet(provider, Number(roundNumber), player);
        const amount = BigInt(userBet.amount ?? 0n);
        if (amount > 0n) {
          return { roundNumber, side: userBet.side, amount };
        }
        return null;
      } catch (error) {
        return null;
      }
    }));

    return entries.filter(Boolean) as Array<{ roundNumber: bigint; side: string; amount: bigint }>;
  }

  static async getHolderPosition(provider: PublicClient, player: Address) {
    const { address: bettingAddress, abi: bettingAbi } = getBettingContractConfig();
    const holderVaultAddress = await provider.readContract({
      address: bettingAddress as Address,
      abi: bettingAbi,
      functionName: "rushHolderVault",
    }) as Address;
    if (!holderVaultAddress || holderVaultAddress === "0x0000000000000000000000000000000000000000") {
      return {
        holderVaultAddress: undefined, shares: 0n, pendingRewards: 0n, grossAmount: 0n, feeAmount: 0n, netAmount: 0n,
        custody: 0n, stakingAssets: 0n, liabilities: 0n, solvent: false,
      };
    }
    const artifact = RushHolderVaultArtifact as Record<string, any>;
    const abi = artifact["abi"] as Abi;
    const [shares, pendingRewards, preview, custody, stakingAssets, liabilities, solvent] = await Promise.all([
      provider.readContract({ address: holderVaultAddress, abi, functionName: "playerShares", args: [player] }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "pendingHolderReward", args: [player] }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "previewWithdrawAll", args: [player] }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "actualRushBalance" }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "stakingAssets" }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "totalRushLiabilities" }),
      provider.readContract({ address: holderVaultAddress, abi, functionName: "isSolvent" }),
    ]);
    const [grossAmount, feeAmount, netAmount] = preview as [bigint, bigint, bigint];
    return {
      holderVaultAddress,
      shares: BigInt(shares.toString()),
      pendingRewards: BigInt(pendingRewards.toString()),
      grossAmount: BigInt(grossAmount.toString()),
      feeAmount: BigInt(feeAmount.toString()),
      netAmount: BigInt(netAmount.toString()),
      custody: BigInt(custody.toString()),
      stakingAssets: BigInt(stakingAssets.toString()),
      liabilities: BigInt(liabilities.toString()),
      solvent: Boolean(solvent),
    };
  }

  static async claimHolderRewards(signer: WalletClient, holderVaultAddress: Address) {
    const artifact = RushHolderVaultArtifact as Record<string, any>;
    return signer.writeContract({
      address: holderVaultAddress,
      abi: artifact["abi"] as Abi,
      functionName: "claimHolderRewards",
      account: signer.account!,
    });
  }

  static async withdrawAllRush(signer: WalletClient, holderVaultAddress: Address) {
    const artifact = RushHolderVaultArtifact as Record<string, any>;
    return signer.writeContract({
      address: holderVaultAddress,
      abi: artifact["abi"] as Abi,
      functionName: "withdrawAll",
      account: signer.account!,
    });
  }

  static async previewRushWithdraw(provider: PublicClient, holderVaultAddress: Address, shares: bigint) {
    const artifact = RushHolderVaultArtifact as Record<string, any>;
    return provider.readContract({ address: holderVaultAddress, abi: artifact["abi"] as Abi, functionName: "previewWithdraw", args: [shares] }) as Promise<[bigint, bigint, bigint]>;
  }

  static async withdrawRush(signer: WalletClient, holderVaultAddress: Address, shares: bigint) {
    const artifact = RushHolderVaultArtifact as Record<string, any>;
    return signer.writeContract({ address: holderVaultAddress, abi: artifact["abi"] as Abi, functionName: "withdraw", args: [shares], account: signer.account! });
  }

  static async getRushWalletBalance(provider: PublicClient, player: Address) {
    const { address: bettingAddress, abi } = getBettingContractConfig();
    const rushToken = await provider.readContract({ address: bettingAddress as Address, abi, functionName: "rushToken" }) as Address;
    if (!rushToken || rushToken === "0x0000000000000000000000000000000000000000") return 0n;
    return provider.readContract({ address: rushToken, abi: [{ type: "function", name: "balanceOf", stateMutability: "view", inputs: [{ name: "account", type: "address" }], outputs: [{ type: "uint256" }] }] as Abi, functionName: "balanceOf", args: [player] }) as Promise<bigint>;
  }

  static getContract(provider: PublicClient) {
    const { address, abi } = getBettingContractConfig();
    return ContractFactory.createReadContract(address, abi, provider);
  }

  static getSignerContract(signer: WalletClient) {
    const { address, abi } = getBettingContractConfig();
    return ContractFactory.createWriteContract(address, abi, signer);
  }

  static async getUserBet(provider: PublicClient, roundNumber: number, player: string) {
    const { address, abi } = getBettingContractConfig();

    console.debug("[BettingContractService] getUserBet readContract send", {
      address,
      functionName: "getUserBet",
      roundNumber,
      player,
    });

    const result = await provider.readContract({
      address: address as Address,
      abi,
      functionName: "getUserBet",
      args: [BigInt(roundNumber), player as Address],
    });

    console.debug("[BettingContractService] getUserBet readContract result", result);

    const fallback: [bigint, bigint] = [0n, 0n];
    const rawTuple = Array.isArray(result) ? result : fallback;
    const [overAmount, underAmount] = rawTuple as [bigint | undefined, bigint | undefined];

    const normalizedOverAmount = overAmount === undefined || overAmount === null ? 0n : BigInt(overAmount.toString());
    const normalizedUnderAmount = underAmount === undefined || underAmount === null ? 0n : BigInt(underAmount.toString());

    console.debug("[BettingContractService] getUserBet normalized result", {
      normalizedOverAmount,
      normalizedUnderAmount,
    });

    if (normalizedOverAmount > 0n && normalizedOverAmount >= normalizedUnderAmount) {
      return {
        side: "OVER",
        amount: normalizedOverAmount,
      };
    }
    if (normalizedUnderAmount > 0n) {
      return {
        side: "UNDER",
        amount: normalizedUnderAmount,
      };
    }
    return {
      side: "OVER",
      amount: 0n,
    };
  }

  static async getClaimableReward(provider: PublicClient, address: string) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    console.debug("[BettingContractService] getClaimableReward send", {
      address: contractAddress,
      functionName: "getClaimableReward",
      args: [address],
    });

    const result = await provider.readContract({
      address: contractAddress as Address,
      abi,
      functionName: "getClaimableReward",
      args: [address as Address],
    });

    console.debug("[BettingContractService] getClaimableReward result", result);
    return result === undefined || result === null ? 0n : BigInt(result.toString());
  }

  static async getClaimableEth(provider: PublicClient, address: string) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    console.debug("[BettingContractService] getClaimableEth send", {
      address: contractAddress,
      functionName: "getClaimableEth",
      args: [address],
    });

    const result = await provider.readContract({
      address: contractAddress as Address,
      abi,
      functionName: "getClaimableEth",
      args: [address as Address],
    });

    console.debug("[BettingContractService] getClaimableEth result", result);
    return result === undefined || result === null ? 0n : BigInt(result.toString());
  }

  /*static async getClaimStatus(provider: PublicClient, address: string): Promise<ClaimStatus> {
    const { address: contractAddress, abi } = getBettingContractConfig();
    console.debug("[BettingContractService] getClaimStatus send", {
      address: contractAddress,
      functionName: "getClaimStatus",
      args: [address],
    });

    const result = await provider.readContract({
      address: contractAddress as Address,
      abi,
      functionName: "getClaimStatus",
      args: [address as Address],
    });

    console.debug("[BettingContractService] getClaimStatus result", result);

    if (result === undefined || result === null) return "unknown";

    const status = String(result);
    if (status === "already_claimed") return "already_claimed";
    if (status === "available") return "available";
    if (status === "none") return "none";
    return "unknown";
  }*/

  static async estimateClaimEth(provider: PublicClient, account: Address, roundNumber: number) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    return provider.estimateContractGas({
      address: contractAddress as Address,
      abi,
      functionName: "claimETH",
      account,
      args: [BigInt(roundNumber)],
    });
  }

  static async claimEth(signer: WalletClient, roundNumber: number) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    const account = signer.account;

    if (typeof signer.writeContract !== "function") {
      throw new Error("Wallet signer is not a viem WalletClient: missing writeContract().");
    }

    if (!account) {
      throw new Error("Wallet client has no connected account.");
    }

    return signer.writeContract({
      chain: signer.chain,
      address: contractAddress as Address,
      abi,
      functionName: "claimETH",
      account,
      args: [BigInt(roundNumber)],
    });
  }

  /**
   * RUSH rewards are claimed through the holder vault, where they are minted
   * as staking shares. RushBetting deliberately has no `claimReward` or
   * `claimMultiple` entry point, so never send a transaction to either of
   * those non-existent methods.
   */
  static async claimRushRewardStake(provider: PublicClient, signer: WalletClient, roundNumber: number) {
    const { address: bettingAddress, abi: bettingAbi } = getBettingContractConfig();
    const account = signer.account;
    if (!account) throw new Error("Wallet client has no connected account.");

    const holderVaultAddress = await provider.readContract({
      address: bettingAddress as Address,
      abi: bettingAbi,
      functionName: "rushHolderVault",
    }) as Address;
    if (!holderVaultAddress || holderVaultAddress === "0x0000000000000000000000000000000000000000") {
      throw new Error("The RUSH holder vault is not configured for this betting contract.");
    }

    const holderAbi = (RushHolderVaultArtifact as Record<string, unknown>)["abi"] as Abi;
    return signer.writeContract({
      chain: signer.chain,
      address: holderVaultAddress,
      abi: holderAbi,
      functionName: "claimRushRewardStake",
      args: [BigInt(roundNumber)],
      account,
    });
  }

  static async getProtocolFee(provider: PublicClient) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    console.debug("[BettingContractService] getProtocolFee send", {
      address: contractAddress,
      functionName: "protocolFeeBps",
    });

    const result = await provider.readContract({
      address: contractAddress as Address,
      abi,
      functionName: "protocolFeeBps",
      args: [],
    });

    console.debug("[BettingContractService] getProtocolFee result", result);
    return result === undefined || result === null ? 0n : BigInt(result.toString());
  }

  static async getRoundPool(provider: PublicClient, roundNumber: number) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    const result = await provider.readContract({
      address: contractAddress as Address,
      abi,
      functionName: "getRoundPool",
      args: [BigInt(roundNumber)],
    });
    const [overPool, underPool] = (Array.isArray(result) ? result : [0n, 0n]) as [bigint, bigint];
    return {
      over: Number(formatTokenAmount(BigInt(overPool.toString()))),
      under: Number(formatTokenAmount(BigInt(underPool.toString()))),
    };
  }

  static async estimatePlaceBet(provider: PublicClient, account: Address, roundNumber: number, side: string, amountWei: bigint) {
    const { address: contractAddress, abi } = getBettingContractConfig();

    // IRushBetting.Side is declared as UNDER = 0, OVER = 1.
    const normalizedSide = side.toUpperCase() === "OVER" ? 1n : 0n;
    return provider.estimateContractGas({
      address: contractAddress as Address,
      abi,
      functionName: "placeBet",
      account,
      args: [BigInt(roundNumber), normalizedSide],
      value: amountWei,
    });
  }

  static async placeBet(signer: WalletClient, roundNumber: number, side: string, amountWei: bigint) {
    const { address: contractAddress, abi } = getBettingContractConfig();
    const account = signer.account;

    if (typeof signer.writeContract !== "function") {
      console.error("[BettingContractService] placeBet() signer lacks writeContract", {
        signer,
        signerType: typeof signer,
        hasAccount: Boolean(account),
      });
      throw new Error("Wallet signer is not a viem WalletClient: missing writeContract().");
    }

    console.debug("[BettingContractService] placeBet() signer account + contract payload", {
      account,
      address: contractAddress,
      roundNumber,
      side,
      normalizedSide: side.toUpperCase() === "OVER" ? 1n : 0n,
      amountWei,
      abiLength: abi.length,
      chain: signer.chain,
    });

    if (!account) {
      throw new Error("Wallet client has no connected account.");
    }

    const normalizedSide = side.toUpperCase() === "OVER" ? 1n : 0n;

    try {
      const txHash = await signer.writeContract({
        chain: signer.chain,
        address: contractAddress as Address,
        abi,
        functionName: "placeBet",
        account,
        args: [BigInt(roundNumber), normalizedSide],
        value: amountWei,
      });

      console.debug("[BettingContractService] placeBet() writeContract resolved", {
        txHash,
      });

      return txHash;
    } catch (error) {
      console.error("[BettingContractService] placeBet() writeContract failure", {
        error,
        message: (error as Error)?.message,
        contractAddress,
        functionName: "placeBet",
        roundNumber,
        side,
        normalizedSide,
        amountWei,
      });
      throw error;
    }
  }

  static getExplorerTxUrl(txHash: string) {
    return `${ROBINHOOD_CHAIN_INFO.explorerUrl}/tx/${txHash}`;
  }
}
