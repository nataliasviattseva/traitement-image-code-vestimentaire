from sqlalchemy import create_engine
import os

from dotenv import load_dotenv
load_dotenv()


engine = create_engine(os.getenv("DIRECT_URL"))

try:
    with engine.connect() as conn:
        print("Connexion OK")
except Exception as e:
    print("Erreur :", e)
