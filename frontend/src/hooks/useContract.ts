import { useMemo } from "react";
import { ContractFactory } from "@/services/blockchain/contractFactory";
import type { BrowserProvider } from "ethers";

export function useContract<T = unknown>(
  address: string,
  abi: any,
  provider: BrowserProvider | null,
) {
  return useMemo(() => {
    if (!provider) return null;
    return ContractFactory.createContract<T>(address, abi, provider);
  }, [address, abi, provider]);
}
