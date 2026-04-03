''' Metrics to evaluate the quality of generated answers in RAG systems.
Faithfulness - ensures that the generated answer is supported by the retrieved evidence.
Answer Relevance - ensures that the generated answer is relevant to the question and the retrieved evidence.
Answer Correctness - ensures that the generated answer is semantically correct compared to the ground truth.
Context Recall - measures whether retrieved context contains all information needed to answer the question. Conceptually a retrieval metric; reported under B1 in eval reports.

'''
import os
import asyncio
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import ContextRecall, Faithfulness, AnswerRelevancy, AnswerCorrectness
from ragas.embeddings import OpenAIEmbeddings
from ..config import settings
from dotenv import load_dotenv
load_dotenv()

if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

client = AsyncOpenAI()
llm = llm_factory(settings.evaluation_model, client=client, max_tokens=8192)
embeddings = OpenAIEmbeddings(client=client)

async def compute_generation_metrics(
    question: str,
    answer: str,
    retrieved_contexts: list[str],
    ground_truth: str
) -> dict[str, float]:

    # Create metric instances
    context_recall_scorer = ContextRecall(llm=llm)
    faithfulness_scorer = Faithfulness(llm=llm)
    answer_relevancy_scorer = AnswerRelevancy(llm=llm, embeddings=embeddings)
    answer_correctness_scorer = AnswerCorrectness(llm=llm, embeddings=embeddings)

    context_recall, faithfulness, answer_relevancy, answer_correctness = await asyncio.gather(
        context_recall_scorer.ascore(
            user_input=question,
            retrieved_contexts=retrieved_contexts,
            reference=ground_truth,
        ),
        faithfulness_scorer.ascore(
            user_input=question,
            response=answer,
            retrieved_contexts=retrieved_contexts,
        ),
        answer_relevancy_scorer.ascore(
            user_input=question,
            response=answer,
        ),
        answer_correctness_scorer.ascore(
            user_input=question,
            response=answer,
            reference=ground_truth,
        )
    )

    return {
        'context_recall': context_recall.value,
        'faithfulness': faithfulness.value,
        'answer_relevance': answer_relevancy.value,
        'answer_correctness': answer_correctness.value
    }