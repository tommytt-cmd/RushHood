import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAccount, useConnect, type Connector } from "wagmi";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";
import {
  WalletCoinbase,
  WalletMetamask,
  WalletRainbow,
  WalletWalletConnect,
} from "@web3icons/react";

import { walletStore } from "@/lib/store";

interface WalletModalContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const WalletModalContext = createContext<WalletModalContextValue>({
  open: false,
  setOpen: () => {},
});

export function useWalletModal() {
  return useContext(WalletModalContext);
}

interface WalletMeta {
  label: string;
  blurb: string;
  accent: string;
  glyph: string;
  icon?: ReactNode;
}

const META: Record<string, WalletMeta> = {
  "io.rainbow": {
    label: "Rainbow",
    blurb: "Open in Rainbow app",
    accent: "#1b2c5a",
    glyph: "R",
    icon: <WalletRainbow size={40} variant="branded" />,
  },
  rainbow: {
    label: "Rainbow",
    blurb: "Open in Rainbow app",
    accent: "#1b2c5a",
    glyph: "R",
    icon: <WalletRainbow size={40} variant="branded" />,
  },
  walletConnect: {
    label: "WalletConnect",
    blurb: "Rainbow, Trust, and 300+ wallets",
    accent: "#1d7cf2",
    glyph: "◉",
    icon: <WalletWalletConnect size={40} variant="background" />,
  },
  coinbaseWalletSDK: {
    label: "Coinbase Wallet",
    blurb: "Open in Coinbase Wallet app",
    accent: "#0052ff",
    glyph: "◍",
    icon: <WalletCoinbase size={40} variant="branded" />,
  },
  "io.metamask": {
    label: "MetaMask",
    blurb: "Open in MetaMask app",
    accent: "#3a1e0d",
    glyph: "M",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="web3icons">
    <path fill="#FF5C16" d="m19.821 19.918-3.877-1.131-2.924 1.712h-2.04l-2.926-1.712-3.875 1.13L3 16.02l1.179-4.327L3 8.034 4.179 3.5l6.056 3.544h3.53L19.821 3.5 21 8.034l-1.179 3.658L21 16.02z"/>
    <path fill="#FF5C16" d="m4.18 3.5 6.055 3.547-.24 2.434zm3.875 12.52 2.665 1.99-2.665.777zm2.452-3.286-.512-3.251-3.278 2.21h-.002v.001l.01 2.275 1.33-1.235zM19.82 3.5l-6.056 3.547.24 2.434zm-3.875 12.52-2.665 1.99 2.665.777zm1.339-4.326v-.002zl-3.279-2.21-.512 3.25h2.451l1.33 1.236z"/>
    <path fill="#E34807" d="m8.054 18.787-3.875 1.13L3 16.022h5.054zm2.452-6.054.74 4.7-1.026-2.614-3.497-.85 1.33-1.236zm5.44 6.054 3.875 1.13L21 16.022h-5.055zm-2.452-6.054-.74 4.7 1.026-2.614 3.497-.85-1.331-1.236z"/>
    <path fill="#FF8D5D" d="m3 16.02 1.179-4.328h2.535l.01 2.276 3.496.85 1.026 2.613-.527.576-2.665-1.989H3zm18 0-1.179-4.328h-2.535l-.01 2.276-3.496.85-1.026 2.613.527.576 2.665-1.989H21zm-7.235-8.976h-3.53l-.24 2.435 1.251 7.95h1.508l1.252-7.95z"/>
    <path fill="#661800" d="M4.179 3.5 3 8.034l1.179 3.658h2.535l3.28-2.211zm5.594 10.177H8.625l-.626.6 2.222.54zM19.821 3.5 21 8.034l-1.179 3.658h-2.535l-3.28-2.211zm-5.593 10.177h1.15l.626.6-2.224.541zm-1.209 5.271.262-.94-.527-.575h-1.509l-.527.575.262.94"/>
    <path fill="#C0C4CD" d="M13.02 18.948V20.5h-2.04v-1.552z"/>
    <path fill="#E7EBF6" d="m8.055 18.785 2.927 1.714v-1.552l-.262-.94zm7.89 0L13.02 20.5v-1.552l.262-.94z"/>
</svg>
,
  },
  metaMask: {
    label: "MetaMask",
    blurb: "Open in MetaMask app",
    accent: "#3a1e0d",
    glyph: "M",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="web3icons">
    <path fill="#FF5C16" d="m19.821 19.918-3.877-1.131-2.924 1.712h-2.04l-2.926-1.712-3.875 1.13L3 16.02l1.179-4.327L3 8.034 4.179 3.5l6.056 3.544h3.53L19.821 3.5 21 8.034l-1.179 3.658L21 16.02z"/>
    <path fill="#FF5C16" d="m4.18 3.5 6.055 3.547-.24 2.434zm3.875 12.52 2.665 1.99-2.665.777zm2.452-3.286-.512-3.251-3.278 2.21h-.002v.001l.01 2.275 1.33-1.235zM19.82 3.5l-6.056 3.547.24 2.434zm-3.875 12.52-2.665 1.99 2.665.777zm1.339-4.326v-.002zl-3.279-2.21-.512 3.25h2.451l1.33 1.236z"/>
    <path fill="#E34807" d="m8.054 18.787-3.875 1.13L3 16.022h5.054zm2.452-6.054.74 4.7-1.026-2.614-3.497-.85 1.33-1.236zm5.44 6.054 3.875 1.13L21 16.022h-5.055zm-2.452-6.054-.74 4.7 1.026-2.614 3.497-.85-1.331-1.236z"/>
    <path fill="#FF8D5D" d="m3 16.02 1.179-4.328h2.535l.01 2.276 3.496.85 1.026 2.613-.527.576-2.665-1.989H3zm18 0-1.179-4.328h-2.535l-.01 2.276-3.496.85-1.026 2.613.527.576 2.665-1.989H21zm-7.235-8.976h-3.53l-.24 2.435 1.251 7.95h1.508l1.252-7.95z"/>
    <path fill="#661800" d="M4.179 3.5 3 8.034l1.179 3.658h2.535l3.28-2.211zm5.594 10.177H8.625l-.626.6 2.222.54zM19.821 3.5 21 8.034l-1.179 3.658h-2.535l-3.28-2.211zm-5.593 10.177h1.15l.626.6-2.224.541zm-1.209 5.271.262-.94-.527-.575h-1.509l-.527.575.262.94"/>
    <path fill="#C0C4CD" d="M13.02 18.948V20.5h-2.04v-1.552z"/>
    <path fill="#E7EBF6" d="m8.055 18.785 2.927 1.714v-1.552l-.262-.94zm7.89 0L13.02 20.5v-1.552l.262-.94z"/>
</svg>
,
  },
};

function metaFor(connector: Connector) {
  return (
    META[connector.id] ??
    META[connector.name] ?? {
      label: connector.name,
      blurb: "Connect with " + connector.name,
      accent: "#1f2a26",
      glyph: "◆",
    }
  );
}

function WalletLogo({ meta }: { meta: WalletMeta }) {
  return (
    <span
      className="relative flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-lg font-display text-lg font-bold text-white"
      style={{ backgroundColor: meta.accent }}
      aria-hidden
    >
      {meta.icon ?? meta.glyph}
    </span>
  );
}

function WalletModal() {
  const { open, setOpen } = useWalletModal();
  const { connectors, connectAsync, isPending, variables } = useConnect();

  const list = useMemo(() => {
    const seen = new Set<string>();
    return connectors.filter((c) => {
      const key = metaFor(c).label;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [connectors]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-background/80 p-4 backdrop-blur-sm sm:items-center">
      <button
        aria-label="Close wallet dialog"
        className="absolute inset-0 cursor-default"
        onClick={() => setOpen(false)}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Connect wallet"
        className="clip-tech relative w-full max-w-md border border-primary/40 bg-surface shadow-[0_0_60px_-12px_hsl(var(--primary)/0.4)]"
      >
        <div className="flex items-start justify-between gap-4 border-b border-border px-6 py-5">
          <div>
            <h2 className="font-display text-xl font-bold uppercase tracking-[0.16em]">
              Connect wallet
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Choose your wallet to get started
            </p>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-2 text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="grid gap-3 px-6 py-5">
          {list.map((connector) => {
            const meta = metaFor(connector);
            const busy = isPending && variables?.connector === connector;
            return (
              <button
                key={connector.uid}
                disabled={isPending}
                onClick={async () => {
                  try {
                    await connectAsync({ connector });
                    setOpen(false);
                  } catch (error) {
                    toast.error(
                      error instanceof Error
                        ? error.message
                        : "Wallet connection cancelled",
                    );
                  }
                }}
                className="clip-tag flex items-center gap-4 border border-border bg-surface-2/60 px-4 py-3 text-left transition-colors hover:border-primary disabled:opacity-60"
              >
                <WalletLogo meta={meta} />
                <span className="min-w-0 flex-1">
                  <span className="block font-display text-base font-bold tracking-[0.08em]">
                    {meta.label}
                  </span>
                  <span className="block truncate text-sm text-muted-foreground">
                    {meta.blurb}
                  </span>
                </span>
                {busy && (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" />
                )}
              </button>
            );
          })}
        </div>

        <div className="border-t border-border px-6 py-4 text-center text-sm text-muted-foreground">
          By connecting you agree to the{" "}
          <span className="text-foreground">terms of service</span>
        </div>
      </div>
    </div>
  );
}

function WalletSync() {
  const { address, connector, isConnected } = useAccount();

  useEffect(() => {
    if (isConnected && address) {
      walletStore.connect(connector?.name ?? "Wallet");
    } else {
      walletStore.disconnect();
    }
  }, [address, connector, isConnected]);

  return null;
}

export function WalletModalProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const value = useMemo(() => ({ open, setOpen }), [open]);

  return (
    <WalletModalContext.Provider value={value}>
      <WalletSync />
      {children}
      <WalletModal />
    </WalletModalContext.Provider>
  );
}

// Backwards-compatible alias for callers that used the old name.
export const WalletProviders = WalletModalProvider;
