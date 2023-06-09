from getpass import getuser
from firexkit.argument_conversion import SingleArgDecorator
from firexkit.task import FireXTask

from firexapp.engine.celery import app
from firexapp.submit.arguments import InputConverter
from dotenv import load_dotenv
import os
import openai


def read_env_file():
    # Load the .env file
    load_dotenv()

    # Get the value of OPENAI_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key:
        print(f"OPENAI_API_KEY: {openai_api_key}")
    else:
        print("OPENAI_API_KEY not found in .env file")

    return openai_api_key


@app.task()
def embedding_encode():
    openai.api_key = read_env_file()
    
    openai.Engine.list()  # check we have authenticated

    embedding = openai.Embedding.create(
        input="product name", model="text-embedding-ada-002")["data"][0]["embedding"]
    print(embedding)