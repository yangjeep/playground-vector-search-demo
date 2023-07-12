
from firexkit.argument_conversion import SingleArgDecorator

from firexapp.engine.celery import app
from firexapp.submit.arguments import InputConverter


import os
import pandas as pd
import openai
import openai_embedding


import numpy as np


def read_json_to_dataframe(prod_file_path):
    """
    open json file and read it into a list of dictionaries
    """
    # Define the chunk size
    chunk_size = 1000

    # Create an empty DataFrame to store the combined data
    combined_data = pd.DataFrame()

    # Read JSON file in chunks
    for chunk in pd.read_json(prod_file_path, lines=True, chunksize=chunk_size):
        # Combine the chunks into a single DataFrame
        combined_data = pd.concat([combined_data, chunk])

    # Display the first few rows of the DataFrame
    print(combined_data.head())

    return combined_data


@app.task(bind=True, returns=['prod_info_rawdf'])
def import_prod_data(self, prod_file_path):
    '''
    Import product data based on file name
    '''
    rawdf = read_json_to_dataframe(prod_file_path)

    return rawdf


@InputConverter.register
@SingleArgDecorator('prod_file_path')
def process_datapath(prod_file_path):
    # check if this is a Directory
    return prod_file_path


@app.task(bind=True, returns=['prod_info_list'])
def prep_data(self, feed):
    """
    Prep the data for indexing by extracting the product name and SKU out
    """
    print("Prep data")
    results = self.enqueue_child_and_get_results(
        import_prod_data.s(feed))
    print(len(results['prod_info_rawdf']))
    return results['prod_info_rawdf']


@app.task(bind=True, returns=['results'])
def embedding_gpt(self, prodlist):
    """
    Encode the embeddings using openai api: only tokenize the product name!
    """
    openai.api_key = openai_embedding.read_env_file()

    df = prodlist
    # take the id and title and tokenize the title
    # encoded_titles = df['title'].apply(openai_embedding.embedding_encode)
    # df['embedding'] = encoded_titles
    combined_fields = df.apply(lambda row: str(
        row['title']) + str(row['body_html']), axis=1)
    df['embedding_gpt'] = combined_fields.apply(openai_embedding.embedding_encode)

    print(df['embedding_gpt'].head())

    return df


@app.task(bind=True, returns=['indexed_df'])
def indexing(self):
    """ 
    check if the data has been indexed, if not then index it
    """
    if os.path.exists('artifact/output_file.jsonl'):
        print("Indexing already done!")
        df = self.enqueue_child_and_get_results(import_prod_data.s(
            prod_file_path='vsearch_index.jsonl'))
        return df['prod_info_rawdf']

    """
    Indexing the data by preping the data then use openai api to tokenize/encode the embeddings
    """
    encoding_chain = prep_data.s(feed="records.json") | embedding_gpt.s(
        prodlist='@prod_info_list')
    indexed = self.enqueue_child_and_get_results(encoding_chain)

    with open('artifact/output_file.jsonl', 'w') as file:
        indexed['results'].to_json(file, orient='records', lines=True)

    return indexed['results']
