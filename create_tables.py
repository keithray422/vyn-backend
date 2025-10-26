# create_tables.py
from app.db.database import Base, engine
from app.models import user_model, message_model

print("Creating database tables...")
user_model.Base.metadata.create_all(bind=engine)
message_model.Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
