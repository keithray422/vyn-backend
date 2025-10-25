from app.db.database import engine
from app.db import models

def create_all():
    models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_all()
