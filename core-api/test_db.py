from app.database import engine
try:
    with engine.connect() as conn:
        print("Success! Connected to DB.")
except Exception as e:
    print("Error:", str(e))
