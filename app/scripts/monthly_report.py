from app.database import SessionLocal
from app.utils.helpers import *



if __name__ == "__main__":

    month = "202412"
    db: Session = SessionLocal()
    product = aggregate_total_by_product(db, month)
    location = aggregate_total_by_location(db, month)
    result = aggregate_total_by_product_and_location(db, month)
    score_ai = calculate_score_ai(db, month)
    print(product)
    print(location)
    print(result)
    n_locations, n_products = get_counts_from_config()
    n_days_in_month = 30
    print(score_ai/(n_locations*n_products)/n_days_in_month*100)
