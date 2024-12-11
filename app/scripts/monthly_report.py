from app.database import SessionLocal
from app.utils.helpers import *



if __name__ == "__main__":

    month = "202412"
    db: Session = SessionLocal()
    product = aggregate_total_by_product(db, month)
    location = aggregate_total_by_location(db, month)
    result = aggregate_total_by_product_and_location(db, month)
    score_ai = calculate_score_ai(db, month, "../config.yml")
    print(product)
    print(location)
    print(result)
    print(score_ai)
