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
        print(f"OPENAI_API_KEY is imported")
    else:
        print("OPENAI_API_KEY not found in .env file")

    openai.api_key = openai_api_key

    try:
        openai.Model.list()
        print("OpenAI API key is valid")
    except:
        print("OpenAI API key is invalid")

    return openai_api_key


def embedding_encode(encode_string):
    # always stringify the input
    encode_string = str(encode_string)

    print(f"encoding string: {encode_string}")

    embeddings = openai.Embedding.create(
        input=encode_string, model="text-embedding-ada-002")["data"][0]["embedding"]
    return embeddings
