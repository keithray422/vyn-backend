# create_tables.py
from app.db.database import Base, engine
from app.models.user import User
from app.models.message import Message

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
