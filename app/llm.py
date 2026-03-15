'''Use the retrieved chunks to generate a response using the specified LLM.
The implementation will depend on the LLM provider and model you choose.
'''
from .config import settings
from openai import OpenAI
import anthropic
import time

client = OpenAI(api_key=settings.openai_api_key)
client_anthropic = anthropic.Anthropic(api_key=settings.anthropic_api_key)

def generate_answer(query: str, retrieved_chunks: list[dict]) -> dict:
    """Generate an answer to the user's query based on the retrieved chunks."""

    context = "\n\n".join([chunk for chunk in retrieved_chunks["documents"][0]])

    system_prompt = f"""You are a helpful assistant that answers questions based on the following context:\n\n{context}. If you don't know the answer, say you don't know. Be concise and to the point."""
    user_prompt = f"""Answer the following question based on the provided context:\n\n{query}"""

    start = time.time()

    if settings.llm_provider == "openai":
        response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
            ]
        )
        answer = response.choices[0].message.content
        token_used = response.usage.total_tokens

    elif settings.llm_provider == "anthropic":
        response = client_anthropic.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
        )
        answer = response.content[0].text 
        token_used = response.usage.input_tokens + response.usage.output_tokens
    
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    end = time.time()
    response_time_ms = (end - start) * 1000

    return {"answer": answer, 
    "sources": retrieved_chunks["ids"][0],
    "token_used": token_used,
    "response_time_ms": response_time_ms}   


