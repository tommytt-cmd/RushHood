import type { ChainInfo } from "./types";
import { CHAIN_PARAMS, ROBINHOOD_CHAIN_INFO } from "./constants";

export class ChainService {
  static getCurrentChainInfo(chainId: number | string | null): ChainInfo {
    if (!chainId) return ROBINHOOD_CHAIN_INFO;
    const id = typeof chainId === "string" ? Number(chainId) : chainId;
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
