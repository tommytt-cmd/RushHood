import { useCallback } from "react";
import { TransactionService } from "@/services/blockchain/transactionService";
import type { JsonRpcSigner } from "ethers";
import type { TransactionReceipt } from "ethers";

export function useTransaction(signer: JsonRpcSigner | null) {
  return useCallback(
    async (transaction: Parameters<JsonRpcSigner["sendTransaction"]>[0]): Promise<TransactionReceipt> => {
      if (!signer) {
        throw new Error("A signer is required to send transactions.");
      }
      return TransactionService.sendTransaction(signer, transaction);
    },
    [signer],
  );
}
