import re

def find_words_in_texts(text, search_phrases, product, location):
    results = {
        "product": product,
        "location": location,
        "total_count": 0  # Initialize total match count
    }

    for phrase in search_phrases:
        # Check if the phrase exists in the text
        if re.search(rf'\b{re.escape(phrase)}\b', text, re.IGNORECASE):
            results[phrase] = 1  # Match found
            results["total_count"] += 1  # Increment total count
        else:
            results[phrase] = 0  # Match not found

    return results