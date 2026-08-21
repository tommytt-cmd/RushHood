import { useEffect, useState } from "react";

import { getRoundState, type RoundState } from "@/lib/round";

export function useRoundState(): RoundState {
  const [state, setState] = useState<RoundState>(() => getRoundState(0));

  useEffect(() => {
    setState(getRoundState());
    const id = window.setInterval(() => setState(getRoundState()), 1000);
    return () => window.clearInterval(id);
  }, []);

  return state;
}
