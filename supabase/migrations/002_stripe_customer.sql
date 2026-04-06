-- Migration 002: add stripe_customer_id to profiles
alter table public.profiles
  add column if not exists stripe_customer_id text unique;
