from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.storage import store_response
from app.utils.helpers import track_responses
from app.database import Base, engine
import time


def startup():
    """Create the database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def daily_track(ai_platfrom):
    """Function to be executed daily."""
    current_date = datetime.now().strftime("%Y%m")
    current_day = datetime.now().strftime("%d")
    db: Session = SessionLocal()

    try:
        ai_responses, results = track_responses(ai_platfrom, "app/config.yml")
        print(results)
        for result in results:
            product = result.get('product')
            location = result.get('location')
            total_count = result.get('total_count')
            competitors = result.get('competitors')
            competitor_1 = competitors.get('co-operators')
            competitor_2 = competitors.get('westland')
            competitor_3 = competitors.get('square one')

            store_response(
                db=db,
                product=product,
                location=location,
                total_count=total_count,
                ai_platform=ai_platfrom,
                date=current_date,
                day=current_day,
                competitor_1=competitor_1,
                competitor_2=competitor_2,
                competitor_3=competitor_3
            )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    startup()
    start_time = time.time()

    daily_track("CHATGPT")
    chat_time = time.time() - start_time
    print(f"Time taken to execute chatgpt: {chat_time:.2f} seconds")

    daily_track("PERPLEXITY")
    perplexity_time = time.time() + chat_time
    print(f"Time taken to execute perplexity: {perplexity_time:.2f} seconds")

    daily_track("GEMINI")
    gemini_time = time.time() - start_time
    print(f"Time taken to execute perplexity: {gemini_time:.2f} seconds")