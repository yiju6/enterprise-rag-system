'''
Load test dataset for evaluation. 
The dataset should be a list of dict, each dict contains:
- question_id: int
- question: str
- source_docs: str
- source_chunk_type: str
- answer: str
'''

import pandas as pd

def load_dataset(csv_path: str, companies: list[str] = None, quarter: str = None) -> list[dict]:
    new_column_names = ['question', 'source_docs', 'question_type','source_chunk_type', 'ground_truth']

    df = pd.read_csv(csv_path, names=new_column_names, header=0)  
    df['question_id'] = range(len(df))

    # Filter by companies and quarter if provided
    if companies is not None:
        df = df[df['source_docs'].apply(lambda x: any(company in x for company in companies))]
    if quarter is not None:
        df = df[df['source_docs'].str.contains(quarter)]
    
    df = df[df['question_type'] == 'Single-Doc Single-Chunk RAG'] 
    # Only evaluate on single-doc single-chunk questions for now, as the retrieval and generation logic is different for multi-doc and multi-chunk questions. We will add support for those in the future.

    return df[['question_id', 'question', 'source_docs', 'source_chunk_type', 'ground_truth']].to_dict(orient='records')
