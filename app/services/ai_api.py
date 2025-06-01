from openai import OpenAI
from app.config import OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from urllib.parse import urlparse


client_chatgpt = OpenAI(api_key=OPENAI_API_KEY)
client_perplexity = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
client_gemini = genai.Client(api_key=GEMINI_API_KEY)


def get_ai_response(prompt, ai_platform):
    platform_handlers = {
        "CHATGPT": chatgpt,
        "GEMINI": gemini,
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
            model="gpt-4o-mini-search-preview",
            web_search_options={
                "user_location": {
                    "type": "approximate",
                    "approximate": {
                        "country": "CA",
                        "city": "Calgary",
                    }
                },
            },
            messages=[
                {"role": "system", "content": "You are a helpful assistant for people in canada"},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        annotations = completion.choices[0].message.annotations
        sources = extract_base_domains([annotation.url_citation.url for annotation in annotations if annotation.type == 'url_citation'])
        return completion.choices[0].message.content, sources
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return None


def gemini(prompt):
    try:
        model = "gemini-2.0-flash"
        google_search_tool = Tool(
            google_search=GoogleSearch()
        )
        responses = client_gemini.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            )
        )
        response_text = ''.join(part.text for part in responses.candidates[0].content.parts)
        sources = [chunk.web.title for chunk in responses.candidates[0].grounding_metadata.grounding_chunks]
        return response_text, sources

    except Exception as e:
        print(f"Error getting response from Gemini: {e}")
        return None


def perplexity(prompt):
    try:
        completion = client_perplexity.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for people in Canada."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = completion.choices[0].message.content
        citations = completion.citations
        sources = extract_base_domains(citations)
        return answer, sources

    except Exception as e:
        return f"Error: {e}"


def extract_base_domains(urls):
    """
    Extracts base domains from a list of URLs by removing 'www.' and subdomains.

    Parameters:
    - urls (list): List of URL strings.

    Returns:
    - list: List of base domains.
    """
    base_domains = []
    for url in urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        base_domains.append(domain)
    return base_domains
