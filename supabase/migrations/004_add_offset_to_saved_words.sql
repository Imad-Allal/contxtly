-- Migration 004: add offset column to saved_words
-- offset stores the character position of the word within its block's textContent
-- Nullable so existing rows are unaffected (legacy rows fall back to context-only restore)
alter table public.saved_words add column if not exists "offset" integer;
