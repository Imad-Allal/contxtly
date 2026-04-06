-- ============================================================
-- Migration 001: profiles, usage, saved_words
-- Run once in the Supabase SQL editor
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1. profiles
--    One row per user, auto-created on signup via trigger below
-- ────────────────────────────────────────────────────────────
create table if not exists public.profiles (
  id          uuid        primary key references auth.users(id) on delete cascade,
  email       text        not null,
  plan        text        not null default 'free' check (plan in ('free', 'pro')),
  daily_limit int         not null default 50,
  created_at  timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- ────────────────────────────────────────────────────────────
-- 2. usage
--    One row per (user, date); upserted on each translation
-- ────────────────────────────────────────────────────────────
create table if not exists public.usage (
  id      uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  date    date not null default current_date,
  count   int  not null default 0,
  unique (user_id, date)
);

alter table public.usage enable row level security;

create policy "Users can read own usage"
  on public.usage for select
  using (auth.uid() = user_id);

-- Only the backend (service role) writes to usage — no client insert/update policy needed

-- ────────────────────────────────────────────────────────────
-- 3. saved_words
-- ────────────────────────────────────────────────────────────
create table if not exists public.saved_words (
  id          uuid        primary key default gen_random_uuid(),
  user_id     uuid        not null references public.profiles(id) on delete cascade,
  text        text        not null,
  translation text        not null,
  context     text,
  source_url  text,
  data        jsonb,      -- full translation result (breakdown, meaning, etc.)
  created_at  timestamptz not null default now()
);

alter table public.saved_words enable row level security;

create policy "Users can read own words"
  on public.saved_words for select
  using (auth.uid() = user_id);

create policy "Users can insert own words"
  on public.saved_words for insert
  with check (auth.uid() = user_id);

create policy "Users can delete own words"
  on public.saved_words for delete
  using (auth.uid() = user_id);

-- ────────────────────────────────────────────────────────────
-- 4. Trigger: auto-create profile on signup
-- ────────────────────────────────────────────────────────────
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ────────────────────────────────────────────────────────────
-- 5. Atomic usage increment (avoids race conditions)
-- ────────────────────────────────────────────────────────────
create or replace function public.increment_usage(p_user_id uuid, p_date date)
returns void
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.usage (user_id, date, count)
  values (p_user_id, p_date, 1)
  on conflict (user_id, date)
  do update set count = public.usage.count + 1;
end;
$$;
