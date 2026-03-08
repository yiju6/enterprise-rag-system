import sys
from app.retriever import retrieve
from app.llm import generate_answer

question = sys.argv[1] # Get the question from command line arguments
results = retrieve(question)
answer = generate_answer(question, results)

print(f"\nQuestion: {question}")
print(f"\nAnswer: {answer['answer']}")
print(f"\nSources:")
for source in answer['sources']:
    print(f"  - {source}")