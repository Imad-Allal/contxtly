-- ============================================================
-- Migration 003: soft-delete for saved_words (trash)
-- ============================================================

-- Add deleted_at column (null = active, timestamp = trashed)
alter table public.saved_words
  add column if not exists deleted_at timestamptz default null;

-- Index for fast trash queries
create index if not exists saved_words_deleted_at_idx
  on public.saved_words (user_id, deleted_at)
  where deleted_at is not null;

-- ── Trigger: enforce max 10 trashed words per user (FIFO) ──────────────────────
create or replace function public.enforce_trash_limit()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
  overflow_count int;
begin
  -- Count trashed words for this user after the soft-delete
  select count(*) - 10
  into overflow_count
  from public.saved_words
  where user_id = NEW.user_id
    and deleted_at is not null;

  -- Hard-delete the oldest trashed rows beyond the limit
  if overflow_count > 0 then
    delete from public.saved_words
    where id in (
      select id from public.saved_words
      where user_id = NEW.user_id
        and deleted_at is not null
      order by deleted_at asc
      limit overflow_count
    );
  end if;

  return NEW;
end;
$$;

create or replace trigger trg_enforce_trash_limit
  after update of deleted_at on public.saved_words
  for each row
  when (NEW.deleted_at is not null and OLD.deleted_at is null)
  execute procedure public.enforce_trash_limit();

-- Allow users to update own words (needed for soft-delete)
create policy "Users can update own words"
  on public.saved_words for update
  using (auth.uid() = user_id);
