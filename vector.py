
from getpass import getuser
from operator import truediv
from firexkit.argument_conversion import SingleArgDecorator
from firexkit.task import FireXTask

from firexapp.engine.celery import app
from firexapp.submit.arguments import InputConverter
from firexkit.chain import InjectArgs


from dotenv import load_dotenv
import os
import csv
import pandas as pd
import openai
import openai_embedding

from sklearn.manifold import TSNE
import numpy as np

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import ast


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


@app.task(bind=True, returns=['indexed_df'])
def indexing(self):
    """ 
    check if the data has been indexed, if not then index it
    """
    if os.path.exists('vsearch_index.jsonl'):
        print("Indexing already done!")
        df = self.enqueue_child_and_get_results(import_prod_data.s(
            prod_file_path='vsearch_index.jsonl'))
        return df['prod_info_rawdf']

    """
    Indexing the data by preping the data then use openai api to tokenize/encode the embeddings
    """
    encoding_chain = prep_data.s(feed="records.json") | embedding_encode.s(
        prodlist='@prod_info_list')
    indexed = self.enqueue_child_and_get_results(encoding_chain)

    with open('output_file.jsonl', 'w') as file:
        indexed['results'].to_json(file, orient='records', lines=True)

    return indexed['results']


@app.task(bind=True, returns=['results'])
def embedding_encode(self, prodlist):
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
    df['embedding'] = combined_fields.apply(openai_embedding.embedding_encode)

    print(df['embedding'].head())

    with open('vsearch_index.jsonl', 'w') as file:
        df.to_json(file, orient='records', lines=True)
    # get the embedding for the title

    # create a new field called 'embedding' and store embedding into it
    return df


def main():
    """
    Main entry point for the vector search
    """
    df = read_json_to_dataframe("records.json")
    print(df['title'].astype(str))


@ InputConverter.register
@ SingleArgDecorator('search')
def preprocess_searchterm(search):
    """
    Just a stub
    """
    return search


@ app.task(bind=True, returns=['results'])
def search_gpt(self, search):
    """
    Search the data
    """
    return "Search the data"


@ app.task(bind=True)
def loadDB(self, df):
    return True


@ app.task(bind=True)
def visualize_search(self, search, df):
    print(df.head())

    matrix = np.array(df.embedding.apply(ast.literal_eval).to_list())

    print(matrix)
    tsne = TSNE(n_components=2, perplexity=15, random_state=42,
                init='random', learning_rate=200)
    vis_dims = tsne.fit_transform(matrix)
    vis_dims.shape

    colors = ["turquoise"]
    x = [x for x, y in vis_dims]
    y = [y for x, y in vis_dims]

    color_indices = 0

    colormap = matplotlib.colors.ListedColormap(colors)
    plt.scatter(x, y, c=color_indices, cmap=colormap, alpha=0.3)

    plt.title("Try plot")

    return True


@ app.task(bind=True)
def vsearch(self, search):
    """
    Entry point for vector search
    """
    print("Search for:"+search)

    """
        if not self.enqueue_child_and_get_results(indexing.s()):
            return False
        if not self.enqueue_child_and_get_results(loadDB.s()):
            return False
        if not self.enqueue_child_and_get_results(search_gpt.s(search)):
            return False
        if not self.enqueue_child_and_get_results(visualize_search.s()):
            return False
    """
    # chain = indexing.s() | loadDB.s(df='@indexed_df') | search_gpt.s(search='@search') | visualize_search.s(search='@search', df='@indexed_df')
    chain = indexing.s() | visualize_search.s(search='@search', df='@indexed_df')
    self.enqueue_child_and_get_results(chain)
