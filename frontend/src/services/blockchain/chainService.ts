import type { ChainInfo } from "./types";
import { CHAIN_PARAMS, ROBINHOOD_CHAIN_INFO } from "./constants";

export class ChainService {
  static normalizeChainId(chainId: number | string | bigint | null | undefined): number | null {
    if (chainId === null || chainId === undefined || chainId === "") return null;

    if (typeof chainId === "bigint") return Number(chainId);
    if (typeof chainId === "number") return Number.isFinite(chainId) ? chainId : null;

    const trimmed = chainId.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith("0x") || trimmed.startsWith("0X")) {
      const parsed = Number.parseInt(trimmed, 16);
      return Number.isFinite(parsed) ? parsed : null;
    }

    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : null;
  }

  static getCurrentChainInfo(chainId: number | string | null): ChainInfo {
    if (!chainId) return ROBINHOOD_CHAIN_INFO;
    const id = this.normalizeChainId(chainId) ?? ROBINHOOD_CHAIN_INFO.chainId;
    return {
      ...ROBINHOOD_CHAIN_INFO,
      chainId: id,
    };
  }

  static async switchToRobinhood(provider: any): Promise<ChainInfo> {
    if (!provider?.request) {
      throw new Error("Provider does not support chain switching");
    }

    try {
      await provider.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: CHAIN_PARAMS.chainId }],
      });
    } catch (error) {
      const code = (error as any)?.code;
      if (code === 4902 || code === -32603) {
        await provider.request({
          method: "wallet_addEthereumChain",
          params: [CHAIN_PARAMS],
        });
      } else {
        throw error;
      }
    }

    return ROBINHOOD_CHAIN_INFO;
  }

  static getExplorerUrl(txHash: string): string {
    return `${ROBINHOOD_CHAIN_INFO.explorerUrl}/tx/${txHash}`;
  }

  static getRpcUrl(): string {
    return ROBINHOOD_CHAIN_INFO.rpcUrl;
  }

  static getNativeCurrency() {
    return ROBINHOOD_CHAIN_INFO.nativeCurrency;
  }
}
