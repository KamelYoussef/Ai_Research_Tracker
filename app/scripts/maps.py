from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.storage import store_maps
from app.utils.helpers import get_insurance_brokers_by_city, find_target_rank_by_city_and_keyword
from app.database import Base, engine



def startup():
    """Create the database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def maps_track():
    """Function to be executed daily."""
    current_date = datetime.now().strftime("%Y%m")
    current_day = datetime.now().strftime("%d")
    db: Session = SessionLocal()
    try :
        results = find_target_rank_by_city_and_keyword(get_insurance_brokers_by_city("app/config.yml"), "app/config.yml")
        print(results)
        for result in results:
            product = result.get('product')
            location = result.get('location')
            rank = result.get('rank')
            rating = result.get('rating')
            reviews = result.get('reviews')

            store_maps(
                db=db,
                product=product,
                location=location,
                date=current_date,
                day=current_day,
                rank=rank,
                rating=rating,
                reviews=reviews
            )

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    startup()
    maps_track()
