import type { BigNumberish } from "ethers";
import { formatUnits, parseUnits } from "ethers";

export function shortenAddress(address: string): string {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function normalizeBigNumberish(value: BigNumberish | null | undefined, decimals = 18): bigint {
  if (value === null || value === undefined) return 0n;
  return BigInt(value.toString());
}

export function formatTokenAmount(value: BigNumberish | null | undefined, decimals = 18): string {
  if (value === null || value === undefined) {
    console.debug("[formatTokenAmount] received undefined/null and normalizing to 0", { value, decimals });
    return "0";
  }

  console.debug("[formatTokenAmount] formatting value", { value, decimals });
  return Number(formatUnits(value, decimals)).toFixed(6).replace(/\.?0+$/, "");
}

export function parseTokenAmount(value: string, decimals = 18): bigint {
  return BigInt(parseUnits(value || "0", decimals).toString());
}
