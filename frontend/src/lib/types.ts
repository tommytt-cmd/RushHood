export type GamePhase = 'betting' | 'locked' | 'live' | 'settle';

export type Side = 'OVER' | 'UNDER';

export interface RoundResult {
  id: number;
  finalCount: number;
  line: number;
  winningSide: Side;
}

export interface RecentLine {
  id: number;
  value: string;
  side: Side;
}

export interface BetSelection {
  side: Side;
  amount: number;
}

export interface PayoutQuote {
  over: number;
  under: number;
}

export type BetStatus = 'won' | 'lost' | 'pending';

export interface BetRecord {
  id: string | number;
  bettor: string;
  avatar: string;
  side: Side;
  amount: number;
  payout: number;
  status: BetStatus;
  roundId: number;
  timeAgo: string;
}

export type NavView = 'play' | 'bets' | 'how' | 'history';
