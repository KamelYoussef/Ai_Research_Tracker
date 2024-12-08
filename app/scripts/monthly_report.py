from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.response import Response
from app.database import SessionLocal


def aggregate_total_by_product(db: Session, month: str):
    """
    Aggregate total_count by product for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by product.
    """
    results = (
        db.query(Response.product, func.sum(Response.total_count).label("total_count"))
        .filter(Response.date == month)
        .group_by(Response.product)
        .all()
    )
    return [{"product": r[0], "total_count": r[1]} for r in results]


def aggregate_total_by_location(db: Session, month: str):
    """
    Aggregate total_count by location for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by location.
    """
    results = (
        db.query(Response.location, func.sum(Response.total_count).label("total_count"))
        .filter(Response.date == month)
        .group_by(Response.location)
        .all()
    )
    return [{"location": r[0], "total_count": r[1]} for r in results]


def aggregate_total_by_product_and_location(db: Session, month: str):
    """
    Aggregate total_count by product and location for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by product and location.
    """
    results = (
        db.query(
            Response.product,
            Response.location,
            func.sum(Response.total_count).label("total_count"),
        )
        .filter(Response.date == month)
        .group_by(Response.product, Response.location)
        .all()
    )
    return [
        {"product": r[0], "location": r[1], "total_count": r[2]} for r in results
    ]


from app.database import get_db

if __name__ == "__main__":

    month = "202412"
    db: Session = SessionLocal()
    product = aggregate_total_by_product(db, month)
    location = aggregate_total_by_location(db, month)
    result = aggregate_total_by_product_and_location(db, month)
    print(product)
    print(location)
    print(result)