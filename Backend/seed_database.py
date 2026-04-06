from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./bookmygig.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBMusician(Base):
    __tablename__ = "musicians"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    musician_type = Column(String, default="Band")
    contact = Column(String)
    location = Column(String, default="London")
    genres = Column(String, default="Rock")
    years_experience = Column(Integer, default=5)
    base_price = Column(Float, default=500.0)
    social_links = Column(Boolean, default=True)
    average_sentiment = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()

    musicians_to_add = [
        DBMusician(id="M001", username="rockband", password="pass123", name="The FYP Rockers", musician_type="Band", contact="rock@test.com", location="London", genres="Rock, Indie", years_experience=5, base_price=500.0, average_sentiment=0.85),
        DBMusician(id="M002", username="jazzsolo", password="pass123", name="Smooth Jazz Jane", musician_type="Solo", contact="jane@test.com", location="Manchester", genres="Jazz", years_experience=12, base_price=350.0, average_sentiment=0.92),
        DBMusician(id="M003", username="djbeat", password="pass123", name="DJ Pulse", musician_type="DJ", contact="dj@test.com", location="Bristol", genres="Electronic, Pop", years_experience=3, base_price=250.0, average_sentiment=0.60),
        DBMusician(id="M004", username="classicalq", password="pass123", name="Royal Strings", musician_type="Quartet", contact="strings@test.com", location="Edinburgh", genres="Classical", years_experience=15, base_price=1200.0, average_sentiment=0.98),
        DBMusician(id="M005", username="popduo", password="pass123", name="Neon Lights", musician_type="Duo", contact="neon@test.com", location="London", genres="Pop", years_experience=2, base_price=300.0, average_sentiment=0.45)
    ]

    added_count = 0
    for mus in musicians_to_add:
        if not db.query(DBMusician).filter(DBMusician.username == mus.username).first():
            db.add(mus)
            added_count += 1

    db.commit()
    db.close()
    
    if added_count > 0:
        print(f"Successfully added {added_count} musicians to the database!")
    else:
        print("All musicians already exist in the database.")

if __name__ == "__main__":
    seed_data()