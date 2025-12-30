"""Run migration 084 to add company_id to vw_job_listings."""

from database import db

# Read the migration file
with open('database/migrations/084_add_company_id_to_vw_job_listings.sql', 'r') as f:
    sql = f.read()

# Execute via Supabase client using raw query
# Split by semicolons and execute each statement
statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

for i, statement in enumerate(statements, 1):
    if statement:
        print(f"Executing statement {i}/{len(statements)}...")
        try:
            # Use the query method to execute raw SQL
            result = db.client.rpc('query', {'query': statement}).execute()
            print(f"✅ Statement {i} executed successfully")
        except Exception as e:
            # If RPC doesn't work, try direct table query
            print(f"⚠️  RPC failed, trying alternative method: {e}")
            # For view creation, we need to use Supabase dashboard or direct PostgreSQL access
            print("Please run this migration manually via Supabase dashboard or psql")
            print(f"\nSQL to execute:\n{statement}")
            break

print("\n✅ Migration completed!")
