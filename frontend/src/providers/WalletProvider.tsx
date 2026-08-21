import { useEffect, useMemo } from "react";
import type { Connector } from "wagmi";
import { useAccount, useBalance, useConnect, useDisconnect, usePublicClient, useSwitchChain, useWalletClient } from "wagmi";
import { WalletContext } from "./WalletContext";
import type { WalletConnectorName, WalletContextValue, WalletState } from "@/services/blockchain/types";
import { ROBINHOOD_CHAIN_INFO } from "@/services/blockchain/constants";
import { robinhoodChain, wagmiConnectors } from "@/services/blockchain/wagmi";

const initialState: WalletState = {
  connected: false,
  address: null,
  providerName: null,
  chainId: null,
  chainName: null,
  status: "idle",
  balance: 0,
  nativeBalance: "0",
  tokenBalances: {},
  isCorrectNetwork: false,
  lastConnectedWallet: null,
  error: null,
};

const connectorMap: Record<WalletConnectorName, Connector> = {
  MetaMask: wagmiConnectors.MetaMask,
  "Coinbase Wallet": wagmiConnectors.Coinbase,
  "Browser Wallet": wagmiConnectors.Browser,
  WalletConnect: wagmiConnectors.WalletConnect,
};

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const { connectAsync, status: connectStatus, error: connectError } = useConnect();
  const { disconnectAsync } = useDisconnect();
  const { switchChainAsync } = useSwitchChain();
  const { address, connector, isConnected, chainId: accountChainId } = useAccount();
  const publicClient = usePublicClient({ chainId: robinhoodChain.id });
  const { data: walletClient } = useWalletClient({ chainId: robinhoodChain.id });
  // disable continuous balance polling to avoid excessive RPC calls; refetch on demand
  const { data: balanceData, refetch: refetchBalance } = useBalance({
    address,
    chainId: robinhoodChain.id,
    watch: false,
    enabled: Boolean(address),
    // periodic background refresh kept low to reduce RPC usage
    refetchInterval: 60_000,
  });

  const provider = publicClient ?? null;
  const signer = walletClient ?? null;

  const connect = async (connectorName: WalletConnectorName) => {
    const selectedConnector = connectorMap[connectorName];
    if (!selectedConnector) {
      throw new Error(`Unsupported wallet connector: ${connectorName}`);
    }
    await connectAsync({ connector: selectedConnector });
  };

  const disconnect = async () => {
    await disconnectAsync();
  };

  const switchNetwork = async () => {
    if (accountChainId === robinhoodChain.id) return;
    await switchChainAsync({ chainId: robinhoodChain.id });
  };

  const refreshBalances = async () => {
    if (refetchBalance) {
      await refetchBalance();
    }
  };

  const contextValue = useMemo<WalletContextValue>(() => {
    const chainId = accountChainId ? Number(accountChainId) : null;
    const providerName = connector?.name ? String(connector.name) : null;
    const normalizedProviderName =
      providerName === "MetaMask" || providerName === "Coinbase Wallet" || providerName === "Browser Wallet" || providerName === "WalletConnect"
        ? (providerName as WalletConnectorName)
        : null;

    return {
      ...initialState,
      connected: isConnected,
      address: address ?? null,
      providerName: normalizedProviderName,
      chainId,
      chainName: robinhoodChain.name,
      status: isConnected ? "connected" : connectStatus === "connecting" ? "connecting" : "idle",
      balance: Number(balanceData?.formatted ?? "0"),
      nativeBalance: balanceData?.formatted ?? "0",
      tokenBalances: {},
      isCorrectNetwork: chainId === ROBINHOOD_CHAIN_INFO.chainId,
      lastConnectedWallet: normalizedProviderName,
      error: connectError?.message ?? null,
      provider,
      signer,
      connect,
      disconnect,
      switchNetwork,
      refreshBalances,
    };
  }, [isConnected, address, connector, accountChainId, connectStatus, connectError, balanceData, provider, signer, connect, disconnect, switchNetwork, refreshBalances]);

  return <WalletContext.Provider value={contextValue}>{children}</WalletContext.Provider>;
}
