
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


def read_tsv_to_dataframe(prod_file_path):
    """
    open tsv file and read it into a list of dictionaries
    """
    dataframe = pd.read_csv(prod_file_path, sep='\t', encoding='utf-8')

    print(dataframe.columns)

    return dataframe


@app.task(bind=True, returns=['prod_info_rawdf'])
def import_prod_data(self, prod_file_path):
    '''
    Import product data based on file name
    '''
    rawdf = read_tsv_to_dataframe(prod_file_path)

    return rawdf


@InputConverter.register
@SingleArgDecorator('prod_file_path')
def process_datapath(prod_file_path):
    # check if this is a Directory
    return prod_file_path


@app.task(bind=True)
def indexing(self):
    """
    Indexing the data by preping the data then use openai api to tokenize/encode the embeddings
    """
    encoding_chain = prep_data.s(feed="products.txt") | embedding_encode.s(
        prodlist='@prod_info_list')
    self.enqueue_child_and_get_results(encoding_chain)


@app.task(bind=True, returns=['results'])
def embedding_encode(self, prodlist):
    """ 
    Encode the embeddings using openai api: only tokenize the product name!
    """
    return "Encode embeddings"


@app.task(bind=True, returns=['prod_info_list'])
def prep_data(self, feed):
    """
    Prep the data for indexing by extracting the product name and SKU out
    """
    print("Prep data")
    results = self.enqueue_child_and_get_results(
        import_prod_data.s(feed))
    print(results['prod_info_rawdf'])
    return results['prod_info_rawdf']


@InputConverter.register
@SingleArgDecorator('search')
def preprocess_searchterm(search):
    """
    Just a stub
    """
    return search


@app.task(bind=True)
def vsearch(self, search):
    """
    Entry point for vector search
    """
    print("Search for:"+search)

    # Check if the data has been indexed!
    indexing_signature = indexing.s()
    self.enqueue_child_and_get_results(indexing_signature)

    # Search the data