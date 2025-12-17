from app.configs.database import Base, engine

# ---- Create Database and Tables if not exists ----
def migrate():
    Base.metadata.create_all(bind = engine)