from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


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
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message
    except Exception as e:
        print(f"Error getting response from OpenAI: {e}")
        return None


def gemini(prompt):
    return prompt #to be created


def perplexity(prompt):
    return prompt # to be created