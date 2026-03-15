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

def load_dataset(csv_path: str) -> list[dict]:
    new_column_names = ['question', 'source_docs', 'question_type','source_chunk_type', 'ground_truth']

    df = pd.read_csv(csv_path, names=new_column_names, header=0)  
    df['question_id'] = range(len(df))

    # For week 2, only keep the rows with 'Single-Doc Single-Chunk RAG' in 'Question Type' column
    strings_to_keep = ['Single-Doc Single-Chunk RAG']
    df = df[df['question_type'].isin(strings_to_keep)]

    return df[['question_id', 'question', 'source_docs', 'source_chunk_type', 'ground_truth']].to_dict(orient='records')

