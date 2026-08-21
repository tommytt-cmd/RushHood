import type { Abi, Address, PublicClient, WalletClient } from "viem";

export interface ContractReference {
  address: Address;
  abi: Abi;
}

const contractCache = new Map<string, ContractReference>();

export class ContractFactory {
  static createReadContract(address: string, abi: Abi, pubClient: PublicClient): ContractReference {
    const cacheKey = `${address.toLowerCase()}:${JSON.stringify(abi)}`;
    const existing = contractCache.get(cacheKey);
    if (existing) {
      return existing;
    }

    const contract = {
      address: address as Address,
      abi,
    } satisfies ContractReference;

    contractCache.set(cacheKey, contract);
    return contract;
  }

  static createWriteContract(address: string, abi: Abi, walletClient: WalletClient): ContractReference {
    const cacheKey = `${address.toLowerCase()}:${JSON.stringify(abi)}`;
    const existing = contractCache.get(cacheKey);
    if (existing) {
      return existing;
    }

    const contract = {
      address: address as Address,
      abi,
    } satisfies ContractReference;

    contractCache.set(cacheKey, contract);
    return contract;
  }

  static clearCache() {
    contractCache.clear();
  }
}
