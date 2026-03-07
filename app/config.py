''' Set up configurations'''

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    llm_provider: str = "openai"
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    embedding_model: str = ""
    openai_model: str = ""
    chroma_db_path: str = ""
    chunk_size: int = 800 
    chunk_overlap: int = 150
    top_k_results: int = 5

    class Config:
        env_file = ".env"

settings = Settings()