export interface BetSyncPayload {
  txHash: string;
  walletAddress: string;
  roundId: string;
  side: "OVER" | "UNDER";
  amountEth: string;
}

export class BetSyncService {
  static async syncTransaction(payload: BetSyncPayload) {
    const response = await fetch(`${import.meta.env.VITE_GAME_API_URL ?? "http://localhost:8000"}/api/bets/sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Backend sync failed: ${response.status} ${body}`);
    }

    return response.json();
  }
}
