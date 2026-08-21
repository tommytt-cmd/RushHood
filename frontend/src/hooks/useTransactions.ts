import { useMemo } from "react";
import { useTransactions as useTransactionContext } from "@/contexts/TransactionContext";

export function useTransactions() {
  const context = useTransactionContext();
  return useMemo(
    () => ({
      transactions: context.transactions,
      pushTransaction: context.pushTransaction,
      updateTransaction: context.updateTransaction,
      dismissTransaction: context.dismissTransaction,
    }),
    [context],
  );
}
