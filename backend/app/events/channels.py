from __future__ import annotations

GAME_EVENTS = "game_events"
TIMER_EVENTS = "timer_events"
VEHICLE_EVENTS = "vehicle_events"
PROCESSING_EVENTS = "processing_events"
ADMIN_EVENTS = "admin_events"
SERVER_EVENTS = "server_events"
HEARTBEAT_EVENTS = "heartbeat_events"

EVENT_CHANNEL_MAP: dict[str, str] = {
    "phase_change": GAME_EVENTS,
    "round_created": GAME_EVENTS,
    "round_started": GAME_EVENTS,
    "round_locked": GAME_EVENTS,
    "round_finished": GAME_EVENTS,
    "timer": TIMER_EVENTS,
    "vehicle_detected": VEHICLE_EVENTS,
    "vehicle_count": VEHICLE_EVENTS,
    "vehicle_count_updated": VEHICLE_EVENTS,
    "replay_started": VEHICLE_EVENTS,
    "replay_finished": VEHICLE_EVENTS,
    "processing_progress": PROCESSING_EVENTS,
    "server_status": SERVER_EVENTS,
    "heartbeat": HEARTBEAT_EVENTS,
    "bet_placed": GAME_EVENTS,
    "settlement_completed": ADMIN_EVENTS,
    "player_settlement_updated": GAME_EVENTS,
}

ALL_CHANNELS = list(set(EVENT_CHANNEL_MAP.values()))
