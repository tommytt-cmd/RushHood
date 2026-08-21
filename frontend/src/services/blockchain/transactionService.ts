import type { TransactionReceipt } from "ethers";
import type { JsonRpcSigner } from "ethers";

export class TransactionService {
  static async sendTransaction(
    signer: JsonRpcSigner,
    transaction: Parameters<JsonRpcSigner["sendTransaction"]>[0],
  ): Promise<TransactionReceipt> {
    try {
      const tx = await signer.sendTransaction(transaction);
      return await tx.wait();
    } catch (error) {
      const normalized = TransactionService.normalizeError(error);
      console.error("[TransactionService] sendTransaction() failed", {
        error,
        normalized,
      });
      throw new Error(normalized);
    }
  }

  static normalizeError(error: unknown): string {
    const raw = error as any;
    const message = raw?.message ?? raw?.details ?? raw?.shortMessage ?? String(error);
    const statusText = String(message).toLowerCase();

    console.error("[TransactionService] normalizeError() raw payload", {
      error,
      message,
      stack: raw?.stack,
      code: raw?.code,
      metaMessages: raw?.metaMessages,
    });

    if (statusText.includes("user rejected") || statusText.includes("rejected")) {
      return "Transaction rejected by the user.";
    }
    if (statusText.includes("insufficient funds")) {
      return "Insufficient funds for gas or transaction value.";
    }
    if (statusText.includes("replacement fee too low")) {
      return "Transaction replacement fee is too low.";
    }
    if (statusText.includes("execution reverted") || statusText.includes("reverted")) {
      return `Transaction reverted by the network: ${message}`;
    }
    if (statusText.includes("chain")) {
      return `Network error: ${message}`;
    }

    return `Unable to process the transaction. Please try again. ${message}`;
  }
}