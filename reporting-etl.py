from getpass import getuser
from firexkit.argument_conversion import SingleArgDecorator
from firexkit.task import FireXTask

from firexapp.engine.celery import app
from firexapp.submit.arguments import InputConverter
from dotenv import load_dotenv
import os
import json


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        json_data_list = [json.loads(line) for line in file]
    return json_data_list


@app.task()
def readjson(data_file):
    raw = read_json_file(data_file)

    print("Number of lines in the file: ")
    print(len(raw))


@InputConverter.register
@SingleArgDecorator('data_file')
def process_datapath(data_file):
    # check if this is a Directory
    return os.path.abspath(data_file)
