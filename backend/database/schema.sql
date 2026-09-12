-- RushHour PostgreSQL schema for Supabase or other PostgreSQL hosts.
-- This schema is intended for infrastructure-level deployment and can be applied
-- from the Supabase SQL editor or via psql.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.audit_logs (
  id character varying NOT NULL,
  actor character varying NOT NULL,
  action character varying NOT NULL,
  resource character varying NOT NULL,
  details json NOT NULL,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT audit_logs_pkey PRIMARY KEY (id)
);

CREATE TABLE public.round_commitments (
  id character varying NOT NULL,
  round_id character varying NOT NULL UNIQUE,
  commitment_hash character varying NOT NULL,
  algorithm_version character varying NOT NULL,
  generated_at timestamp without time zone NOT NULL,
  CONSTRAINT round_commitments_pkey PRIMARY KEY (id)
);

CREATE TABLE public.server_seeds (
  id character varying NOT NULL,
  seed_value character varying NOT NULL,
  active boolean NOT NULL,
  created_at timestamp without time zone NOT NULL,
  rotated_at timestamp without time zone,
  CONSTRAINT server_seeds_pkey PRIMARY KEY (id)
);

CREATE TABLE public.wallets (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  wallet_address character varying NOT NULL UNIQUE,
  chain_id integer NOT NULL,
  first_seen_at timestamp with time zone NOT NULL DEFAULT now(),
  last_login_at timestamp with time zone,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT wallets_pkey PRIMARY KEY (id)
);

CREATE TABLE public.wallet_sessions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  wallet_id uuid NOT NULL,
  nonce character varying NOT NULL UNIQUE,
  session_token character varying NOT NULL UNIQUE,
  expires_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT wallet_sessions_pkey PRIMARY KEY (id),
  CONSTRAINT wallet_sessions_wallet_id_fkey FOREIGN KEY (wallet_id) REFERENCES public.wallets(id)
);

CREATE TABLE public.players (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  wallet_address character varying NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT players_pkey PRIMARY KEY (id)
);

CREATE TABLE public.videos (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  video_id character varying NOT NULL UNIQUE,
  original_filename character varying NOT NULL,
  filename character varying NOT NULL,
  storage_path text NOT NULL,
  video_url text NOT NULL,
  thumbnail_url text,
  location_name character varying NOT NULL,
  country character varying,
  duration_seconds integer NOT NULL CHECK (duration_seconds > 0),
  filesize bigint NOT NULL CHECK (filesize >= 0),
  width integer NOT NULL CHECK (width > 0),
  height integer NOT NULL CHECK (height > 0),
  fps numeric NOT NULL CHECK (fps > 0::numeric),
  vehicle_total integer NOT NULL CHECK (vehicle_total >= 0),
  checksum character varying NOT NULL,
  status character varying NOT NULL DEFAULT 'READY'::character varying CHECK (status::text = ANY (ARRAY['UPLOADING'::character varying, 'READY'::character varying, 'IN_USE'::character varying, 'USED'::character varying, 'FAILED'::character varying]::text[])),
  processed_at timestamp with time zone,
  uploaded_at timestamp with time zone NOT NULL DEFAULT now(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT videos_pkey PRIMARY KEY (id)
);

CREATE TABLE public.rounds (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  video_id uuid,
  status character varying NOT NULL DEFAULT 'WAITING'::character varying,
  starts_at timestamp with time zone,
  betting_closes_at timestamp with time zone,
  ends_at timestamp with time zone,
  result integer,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  round_number bigint NOT NULL DEFAULT nextval('rounds_round_number_seq'::regclass) UNIQUE,
  locked_ends_at timestamp with time zone,
  live_ends_at timestamp with time zone,
  CONSTRAINT rounds_pkey PRIMARY KEY (id),
  CONSTRAINT rounds_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id)
);

ALTER TABLE public.rounds
  ADD COLUMN settlement_status character varying NOT NULL DEFAULT 'NOT_STARTED'::character varying;

ALTER TABLE public.rounds
  ADD COLUMN settlement_tx_hash character varying(66);

ALTER TABLE public.rounds
  ADD COLUMN settlement_submitted_at timestamp with time zone;

ALTER TABLE public.rounds
  ADD COLUMN settlement_confirmed_at timestamp with time zone;

ALTER TABLE public.rounds
  ADD COLUMN reconciliation_status character varying NOT NULL DEFAULT 'NOT_STARTED'::character varying;

ALTER TABLE public.rounds
  ADD COLUMN reconciliation_started_at timestamp with time zone;

ALTER TABLE public.rounds
  ADD COLUMN reconciliation_completed_at timestamp with time zone;

ALTER TABLE public.rounds
  ADD COLUMN reconciliation_error_message character varying(1024);

ALTER TABLE public.rounds
  ADD COLUMN onchain_total_pool bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_over_pool bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_under_pool bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_winner_pool bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_loser_pool bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_treasury_fee bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_protocol_fee_bps bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_winning_side bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_final_vehicle_count bigint;

ALTER TABLE public.rounds
  ADD COLUMN onchain_settled_at timestamp with time zone;

ALTER TABLE public.rounds
  ADD COLUMN onchain_status bigint;

CREATE TABLE public.bets (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL,
  player_id uuid NOT NULL,
  prediction integer NOT NULL DEFAULT 0,
  stake integer NOT NULL DEFAULT 0,
  transaction_hash character varying(66) UNIQUE,
  onchain_round_number bigint,
  status character varying NOT NULL DEFAULT 'PENDING'::character varying,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT bets_pkey PRIMARY KEY (id),
  CONSTRAINT bets_round_id_fkey FOREIGN KEY (round_id) REFERENCES public.rounds(id),
  CONSTRAINT bets_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id)
);

CREATE TABLE public.timeline_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  video_id uuid NOT NULL,
  timestamp_ms integer NOT NULL CHECK (timestamp_ms >= 0),
  cumulative_count integer NOT NULL CHECK (cumulative_count > 0),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT timeline_events_pkey PRIMARY KEY (id),
  CONSTRAINT timeline_events_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id)
);

CREATE TABLE public.replay_events (
  id uuid NOT NULL,
  video_id character varying NOT NULL,
  timestamp_ms integer NOT NULL,
  vehicle_id character varying NOT NULL,
  vehicle_type character varying NOT NULL,
  direction character varying,
  line_id character varying,
  cumulative_count integer NOT NULL,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT replay_events_pkey PRIMARY KEY (id)
);
