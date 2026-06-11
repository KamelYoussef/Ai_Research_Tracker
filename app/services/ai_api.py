from openai import OpenAI
from app.config import OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY, CLAUDE_API_KEY, SERP_API_KEY
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from urllib.parse import urlparse
from anthropic import Anthropic
import serpapi
import requests
import html2text


client_chatgpt = OpenAI(api_key=OPENAI_API_KEY)
client_perplexity = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
client_gemini = genai.Client(api_key=GEMINI_API_KEY)
client_claude = Anthropic(api_key=CLAUDE_API_KEY)
client_google = serpapi.Client(api_key=SERP_API_KEY)


def get_ai_response(prompt, ai_platform):
    platform_handlers = {
        "CHATGPT": chatgpt,
        "GEMINI": gemini,
        "PERPLEXITY": perplexity,
        "CLAUDE": claude,
        "GOOGLE": google,
        "AI MODE": google_ai_mode
    }

    handler = platform_handlers.get(ai_platform)
    if handler:
        return handler(prompt)
    else:
        raise ValueError(f"Unsupported AI platform: {ai_platform}")


def chatgpt(prompt):
    try:
        response = client_chatgpt.responses.create(
            model="gpt-5-nano",
            tools=[{
                "type": "web_search",
                "user_location": {
                    "type": "approximate",
                    "country": "CA",
                    "city": "Calgary",
                    "region": "Alberta",
                }
            }],
            include=["web_search_call.action.sources"],
            input=prompt
        )
        full_sources_list = []

        for item in response.output:
            if item.type == 'web_search_call' and item.action:
                if item.action.type == 'search' and hasattr(item.action, 'sources'):
                    full_sources_list.extend(item.action.sources)

        sources = extract_base_domains([source.url for source in full_sources_list])
        return response.output_text, sources

    except Exception as e:
        print(f"Error getting response from OpenAI Responses API: {e}")
        return "", []


def gemini(prompt):
    try:
        model = "gemini-2.5-flash"
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
        return "", []


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
        print(f"Error getting response from perplexity: {e}")
        return "", []


def google(prompt):
    try:
        result = client_google.search({
            "q": prompt
        })
        page_token = result["ai_overview"]["page_token"]
        ai_overview = client_google.search({
            "engine": "google_ai_overview",
            "page_token": result["ai_overview"]["page_token"]
        })

        url = ai_overview["search_metadata"]["raw_html_file"]
        response = requests.get(url)

        html_string = response.text
        text = html2text.html2text(html_string)
        return text, None

    except Exception as e:
        print(f"Error getting response from google: {e}")
        return "", ["www.google.com"]


def google_ai_mode(prompt):
    try:
        ai_mode = client_google.search({
            "engine": "google_ai_mode",
            "q": prompt
        })
        print(ai_mode)
        text = ai_mode["reconstructed_markdown"]

        citations = []
        for ref in ai_mode["references"]:
            citations.append(ref["link"])
        sources = extract_base_domains(citations)
        return text, sources

    except Exception as e:
        print(f"Error getting response from google: {e}")
        return "", []


def claude(prompt):
    try:
        response = client_claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            system="You are a helpful assistant for people in Canada.",
            messages=[
                {"role": "user", "content": prompt}
            ],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 1,
                "user_location": {
                    "type": "approximate",
                    "country": "CA",
                    "city": "Calgary"
                }
            }]
        )
        # Extract text response
        answer_parts = []
        citations = []

        for block in response.content:
            if block.__class__.__name__ == "TextBlock":
                # Collect the text
                answer_parts.append(block.text)

                # Collect citations if any
                if block.citations:
                    for cite in block.citations:
                        citations.append(getattr(cite, "url", None))

        answer = "\n".join(answer_parts)
        sources = extract_base_domains(citations)

        return answer, sources
    except Exception as e:
        print(f"Error getting response from Claude: {e}")
        return "", []


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