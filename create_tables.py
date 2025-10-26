# create_tables.py
from app.db.database import Base, engine
from app.models import user_model, message_model

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
