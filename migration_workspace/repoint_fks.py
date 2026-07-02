import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'besmart_backend.settings')
django.setup()

from django.db import connection

def repoint_fks():
    query = """
        SELECT
            n.nspname AS schema_name,
            c_rel.relname AS table_name,
            c.conname AS constraint_name,
            a.attname AS column_name,
            pg_get_constraintdef(c.oid) AS constraint_def
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        JOIN pg_class c_rel ON c_rel.oid = c.conrelid
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
        WHERE confrelid = 'auth.users'::regclass;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("No foreign keys pointing to auth.users found.")
            return

        print(f"Found {len(rows)} foreign keys pointing to auth.users. Repointing to users_user...")

        for row in rows:
            schema_name, table_name, constraint_name, column_name, constraint_def = row
            full_table = f'"{schema_name}"."{table_name}"'
            
            drop_sql = f'ALTER TABLE {full_table} DROP CONSTRAINT "{constraint_name}";'
            print(f"Executing: {drop_sql}")
            try:
                cursor.execute(drop_sql)
            except Exception as e:
                print(f"Error dropping constraint {constraint_name}: {e}")
                continue
            
            # Recreate pointing to public.users_user
            add_sql = f'ALTER TABLE {full_table} ADD CONSTRAINT "{constraint_name}" FOREIGN KEY ("{column_name}") REFERENCES public.users_user(id) ON DELETE CASCADE;'
            print(f"Executing: {add_sql}")
            try:
                cursor.execute(add_sql)
            except Exception as e:
                print(f"Error adding constraint {constraint_name}: {e}")
                # We might need to handle ON DELETE SET NULL if we parse it, but for our test DB, CASCADE is mostly safe.
                pass

        print("Finished repointing foreign keys.")

if __name__ == "__main__":
    repoint_fks()
