from app.database import SessionLocal
from app.utils.helpers import *
import json
import pandas as pd
from app.routes.query_routes import aggregate_maps_by_product_and_location_route


if __name__ == "__main__":

    month = "202510"
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
    #print(calculate_rank(db, month, is_city=True, locations=['Leduc','Alix']))
    locations = [
    "Bolton", "Brandon", "Victoria", "Brooks", "Camrose",
    "Campbell River", "Richmond", "Cochrane", "Coquitlam", "Cranbrook",
    "Dawson Creek", "Duncan", "Drumheller", "Edmonton", "Fernie",
    "Fort St. John", "Vancouver", "Grande Prairie", "High River", "Kelowna",
    "Winnipeg", "Lethbridge", "Langley", "Lloydminster", "Medicine Hat",
    "Nanaimo", "Okotoks", "One Hundred Mile House", "Prince Albert", "Prince George",
    "Red Deer", "Schomberg", "Surrey", "Smithers", "Sooke",
    "Spruce Grove", "Taber", "Terrace", "Vernon", "West Kelowna"
    ]
    products = [""]
    prompt = "What is the best insurance broker in {location}{keyword}"
    ai_platforms = ["CHATGPT", "PERPLEXITY", "GEMINI", "CLAUDE"]

    for ai_platform in ai_platforms:
        ai_responses, results = track_responses(ai_platform, "../config.yml", locations=locations, products=products,
                                            prompt=prompt)

        with open(f"results_{ai_platform}.json", "w") as f:
            json.dump(results, f, indent=4)


    all_data = []

    for platform in ai_platforms:
        filename = f"results_{platform}.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)

                # Add the platform name to each entry before flattening
                for entry in data:
                    entry["ai_platform"] = platform
                    all_data.append(entry)
        except FileNotFoundError:
            print(f"Warning: {filename} not found. Skipping.")

    # Convert the full list to a DataFrame
    df = pd.json_normalize(all_data)

    # Select and rename columns to match your requested format
    # json_normalize turns {'competitors': {'acera': 0}} into 'competitors.acera'
    column_mapping = {
        "ai_platform": "ai_platform",
        "location": "location",
        "total_count": "total_count",
        "rank": "rank",
        "sentiment": "sentiment",
        "competitors.co-operators": "co-operators",
        "competitors.westland": "westland",
        "competitors.brokerlink": "brokerlink",
        "competitors.acera": "acera"
    }

    # Filter for only the columns you want
    final_df = df[list(column_mapping.keys())].rename(columns=column_mapping)

    # Save to CSV with semicolon delimiter
    final_df.to_csv("merged_results.csv", sep=";", index=False)

    print("Transformation complete! Created merged_results.csv")

    db.close()