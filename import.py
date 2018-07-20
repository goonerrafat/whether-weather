import os,csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session , sessionmaker 

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind = engine)) #database session

if __name__ == '__main__':
    with open("zips.csv" , "r") as f:
        reader = csv.reader(f)
        next(reader)

        for Zipcode,City,State,Lat,Long,Population in reader:
            db.execute("INSERT INTO cities (Zipcode,City,State,Lat,Long,Population) \
                VALUES (:Zipcode,:City,:State,:Lat,:Long,:Population)",
                {"Zipcode":Zipcode,"City":City,"State":State,"Lat":Lat,"Long":Long,"Population":Population})

            print(f"Added {Zipcode},{City},{State},{Lat},{Long},{Population}")
            print("Finish Loading Cities into database")
            db.commit()





