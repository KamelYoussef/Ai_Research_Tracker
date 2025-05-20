from openai import OpenAI
from app.config import OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch


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
        return completion.choices[0].message.content
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
        return response_text

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
        sources = "\n\nSources:\n\n" + "\n\n".join(citations)
        return answer + sources

    except Exception as e:
        return f"Error: {e}"