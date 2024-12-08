from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.storage import store_response
from app.utils.helpers import track_responses

def daily_track():
    """Function to be executed daily."""
    current_date = datetime.now().strftime("%Y%m")
    db: Session = SessionLocal()

    try:
        ai_responses, results = track_responses()

        for result, ai_response in zip(results, ai_responses):
            product = result.get('product')
            location = result.get('location')
            total_count = result.get('total_count')

            store_response(
                db=db,
                product=product,
                location=location,
                total_count=total_count,
                ai_platform="ai_platform",
                date=current_date,
            )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    daily_track()
