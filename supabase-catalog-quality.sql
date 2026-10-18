alter table public.books
  add column if not exists publisher text,
  add column if not exists publication_year integer,
  add column if not exists isbn text,
  add column if not exists source_url text,
  add column if not exists rights_type text,
  add column if not exists rights_confirmed_at timestamptz,
  add column if not exists rights_confirmed_by uuid references auth.users(id) on delete set null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'books_rights_type_check'
      and conrelid = 'public.books'::regclass
  ) then
    alter table public.books
      add constraint books_rights_type_check
      check (rights_type is null or rights_type in ('original', 'permission', 'public_domain', 'open_license'));
  end if;
end;
$$;