import { useEffect, useState } from "react";

export interface Stake {
  id: string;
  roundId: string;
  side: "under" | "over";
  amount: number;
  threshold: number;
  placedAt: number;
}

export interface WalletState {
  address: string | null;
  provider: string | null;
  balance: number;
  stakes: Stake[];
}

const KEY = "traffic.wallet.v1";

const initial: WalletState = { address: null, provider: null, balance: 0, stakes: [] };

let state: WalletState = initial;
let hydrated = false;
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

function persist() {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
}

function hydrate() {
  if (hydrated || typeof window === "undefined") return;
  hydrated = true;
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) state = { ...initial, ...(JSON.parse(raw) as WalletState) };
  } catch {
    /* ignore */
  }
  emit();
}

function randomAddress() {
  const hex = "0123456789abcdef";
  let out = "0x";
  for (let i = 0; i < 40; i++) out += hex[Math.floor(Math.random() * 16)];
  return out;
}

export const walletStore = {
  get: () => state,
  subscribe(fn: () => void) {
    listeners.add(fn);
    return () => {
      listeners.delete(fn);
    };
  },
  connect(provider: string) {
    state = { ...state, address: state.address ?? randomAddress(), provider, balance: state.balance || 0.2 };
    persist();
    emit();
  },
  disconnect() {
    state = { ...state, address: null, provider: null };
    persist();
    emit();
  },
  deposit(amount: number) {
    state = { ...state, balance: state.balance + amount };
    persist();
    emit();
  },
  withdraw(amount: number) {
    state = { ...state, balance: Math.max(0, state.balance - amount) };
    persist();
    emit();
  },
  placeStake(stake: Omit<Stake, "id" | "placedAt">) {
    if (stake.amount > state.balance) return false;
    state = {
      ...state,
      balance: state.balance - stake.amount,
      stakes: [
        { ...stake, id: `${stake.roundId}-${Date.now()}`, placedAt: Date.now() },
        ...state.stakes,
      ].slice(0, 50),
    };
    persist();
    emit();
    return true;
  },
};

export function useWallet(): WalletState {
  const [snapshot, setSnapshot] = useState(state);
  useEffect(() => {
    hydrate();
    setSnapshot(walletStore.get());
    return walletStore.subscribe(() => setSnapshot(walletStore.get()));
  }, []);
  return snapshot;
}
