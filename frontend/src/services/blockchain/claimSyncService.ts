export interface ClaimSyncPayload {
  txHash: string;
  walletAddress: string;
  roundId: string;
}

export class ClaimSyncService {
  static async syncClaim(payload: ClaimSyncPayload) {
    const response = await fetch(
      `${import.meta.env.VITE_GAME_API_URL ?? "http://localhost:8000"}/api/claims/sync`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Backend claim sync failed: ${response.status} ${body}`);
    }

    return response.json();
  }
}
