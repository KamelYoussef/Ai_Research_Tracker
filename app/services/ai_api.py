from openai import OpenAI
from app.config import OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY, GOOGLE_CX, GOOGLE_API_KEY
import google.generativeai as genai
import requests

client_chatgpt = OpenAI(api_key=OPENAI_API_KEY)
client_perplexity = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
client_gemini = genai.configure(api_key=GEMINI_API_KEY)
google_api_key = GOOGLE_API_KEY
google_cx = GOOGLE_CX

def get_ai_response(prompt, ai_platform):
    platform_handlers = {
        "CHATGPT": chatgpt,
        "GEMINI": gemini_with_search,
        "PERPLEXITY": perplexity,
    }

    handler = platform_handlers.get(ai_platform)
    if handler:
        return handler(prompt)
    else:
        raise ValueError(f"Unsupported AI platform: {ai_platform}")


def chatgpt(prompt):
    try:
        completion = client_chatgpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for people in canada"},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return None


def gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return None


def perplexity(prompt):
    try:
        completion = client_perplexity.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for people in canada."},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return None


def perform_search(query, api_key, cx):
    """
    Perform a search using the Google Custom Search API.

    Args:
    - query (str): The search query.
    - api_key (str): The Google API key.
    - cx (str): The Custom Search Engine ID.

    Returns:
    - str: Relevant snippets and links from the search results.
    """
    params = {
        "key": api_key,  # API key for authentication
        "cx": cx,  # Custom Search Engine ID
        "q": query  # Search query
    }
    try:
        # Make a GET request to the Google Custom Search API
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        search_results = response.json()

        # Extract snippets and links
        if 'items' in search_results:
            return "\n".join(
                f"Snippet: {item.get('snippet')}\nLink: {item.get('link')}"
                for item in search_results['items']
            )
        else:
            return "No results found."
    except Exception as e:
        print(f"Error performing search: {e}")
        return "Error fetching search results."


def gemini_with_search(prompt, google_api_key=GOOGLE_API_KEY, google_cx=GOOGLE_CX):
    """
    Generate a response using Gemini with real-time search results.

    Args:
    - prompt (str): The user's query.
    - google_api_key (str): The Google API key.
    - google_cx (str): The Custom Search Engine ID.

    Returns:
    - str: Gemini's response combined with real-time search data.
    """
    try:
        replacements = [
            "give me the best",
            "What are the top",
            "List the most affordable",
            "give me the well-known names of",
            "Find the highest-rated"
        ]
        for phrase in replacements:
            prompt = prompt.replace(phrase, "").replace("  ", " ").strip()

        # Perform a Google search
        search_results = perform_search(f"{prompt} Canada", google_api_key, google_cx)
        # Combine the prompt and search results
        combined_prompt = (
            f"User Query: I'm doing benchmark study from the search results list me the name of insurances\n\n"
            f"Real-Time Search Results:\n{search_results}\n\n"
            f"Based on the query and the search results, provide an answer for a client living in canada:"
        )

        # Call the Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(combined_prompt)
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

#test
#user_query = "give me the best car insurance in victoria"
#response = gemini_with_search(user_query, google_api_key, google_cx)
#print(response)