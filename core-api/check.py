import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(db_url)
inspector = inspect(engine)

for t in ('users', 'subscriptions', 'payments', 'affiliates', 'commissions'):
    if t in inspector.get_table_names():
        print(f'\nTable: {t}')
        for c in inspector.get_columns(t):
            print(f"  {c['name']}: {c['type']}")
