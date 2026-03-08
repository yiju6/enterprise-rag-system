''' Set up configurations'''

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    embedding_model: str = ""
    chroma_db_path: str = ""
    chunk_size: int = 800 
    chunk_overlap: int = 150
    top_k_results: int = 5

    class Config:
        env_file = ".env"

settings = Settings()