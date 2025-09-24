from app.database import SessionLocal
from app.utils.helpers import *
from app.routes.query_routes import aggregate_maps_by_product_and_location_route


if __name__ == "__main__":

    month = "202508"
    db: Session = SessionLocal()
    #product = aggregate_total_by_product(db, month)
    #location = aggregate_total_by_location(db, month)
    #result = aggregate_total_by_product_and_location(db, month)
    #score_ai = calculate_score_ai(db, month, "../config.yml")
    #print(product)
    #print(location)
    #print(result)
    #print(score_ai)

    #print(aggregate_maps_by_product_and_location(db, month, is_city=True))
    print(calculate_avg_rank_by_location_platform(db, month))
    print(len(calculate_avg_rank_by_location_platform(db, month)))