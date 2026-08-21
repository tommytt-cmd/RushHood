import { useContext } from "react";
import { WalletContext } from "@/providers";

export function useWallet() {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error("useWallet must be used within a WalletProvider");
  }
  return context;
}

export function useProvider() {
  const { provider } = useWallet();
  return provider;
}

export function useSigner() {
  const { signer } = useWallet();
  return signer;
}

export function useChain() {
  const { chainId, chainName, isCorrectNetwork } = useWallet();
  return { chainId, chainName, isCorrectNetwork };
}

export function useBalances() {
  const { balance, nativeBalance, tokenBalances } = useWallet();
  return { balance, nativeBalance, tokenBalances };
}
