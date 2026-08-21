import type { WalletConnectorName } from "./types";

export interface WalletConnector {
  id: WalletConnectorName;
  label: string;
  installed: () => boolean;
}

export const MetaMaskConnector: WalletConnector = {
  id: "MetaMask",
  label: "MetaMask",
  installed: () => typeof window !== "undefined" && typeof window.ethereum !== "undefined",
};

export const WalletConnectConnector: WalletConnector = {
  id: "WalletConnect",
  label: "WalletConnect",
  installed: () => false,
};

export const CONNECTORS = [MetaMaskConnector, WalletConnectConnector];
