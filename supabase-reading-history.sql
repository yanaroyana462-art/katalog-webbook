-- Izinkan pembaca login melihat histori bacaan miliknya sendiri.
-- Jalankan setelah tabel public.reading_events tersedia.
alter table public.reading_events enable row level security;

drop policy if exists "users can view own reading history" on public.reading_events;
create policy "users can view own reading history"
  on public.reading_events
  for select
  to authenticated
  using (auth.uid() = user_id);
