import { Contract, formatUnits, parseUnits } from "ethers";
import type { BrowserProvider } from "ethers";
import type { TokenBalance } from "./types";

const ERC20_ABI = [
  "function balanceOf(address owner) view returns (uint256)",
  "function allowance(address owner, address spender) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function decimals() view returns (uint8)",
  "function symbol() view returns (string)",
  "function name() view returns (string)",
];

export class TokenService {
  static async getTokenBalance(
    tokenAddress: string,
    walletAddress: string,
    provider: BrowserProvider,
  ): Promise<TokenBalance> {
    const contract = new Contract(tokenAddress, ERC20_ABI, provider);
    const [balance, decimals, symbol] = await Promise.all([
      contract.balanceOf(walletAddress),
      contract.decimals(),
      contract.symbol(),
    ]);

    const formatted = formatUnits(balance, decimals);
    return {
      tokenAddress,
      balance: BigInt(balance.toString()),
      decimals,
      symbol,
      formatted,
    };
  }

  static async getAllowance(
    tokenAddress: string,
    walletAddress: string,
    spender: string,
    provider: BrowserProvider,
  ): Promise<bigint> {
    const contract = new Contract(tokenAddress, ERC20_ABI, provider);
    const raw = await contract.allowance(walletAddress, spender);
    return BigInt(raw.toString());
  }

  static async approve(
    tokenAddress: string,
    spender: string,
    amount: string,
    provider: BrowserProvider,
  ): Promise<string> {
    const contract = new Contract(tokenAddress, ERC20_ABI, provider.getSigner());
    const decimals = await contract.decimals();
    const parsed = parseUnits(amount, decimals);
    const tx = await contract.approve(spender, parsed);
    const receipt = await tx.wait();
    return receipt.transactionHash;
  }

  static formatTokenAmount(value: string | number | bigint, decimals = 18): string {
    return formatUnits(value.toString(), decimals);
  }

  static parseTokenAmount(value: string, decimals = 18): bigint {
    return BigInt(parseUnits(value, decimals).toString());
  }
}
