do $$
begin
  if not (select relrowsecurity from pg_class where oid = 'public.books'::regclass) then
    raise exception 'Enable RLS on public.books before applying the admin delete policy';
  end if;

  if not (select relrowsecurity from pg_class where oid = 'storage.objects'::regclass) then
    raise exception 'Enable RLS on storage.objects before applying the admin delete policy';
  end if;
end;
$$;

drop policy if exists "admin can delete any book" on public.books;
create policy "admin can delete any book"
on public.books
for delete
to authenticated
using (lower((select auth.jwt() ->> 'email')) = 'yanaroyana462@gmail.com');

drop policy if exists "admin can delete book storage files" on storage.objects;
create policy "admin can delete book storage files"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'books'
  and lower((select auth.jwt() ->> 'email')) = 'yanaroyana462@gmail.com'
);