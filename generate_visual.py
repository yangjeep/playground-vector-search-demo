
from lib2to3.pgen2.pgen import DFAState
import pandas as pd

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import openai_embedding


def read_jsonl_to_df(jsonl_path):
    """
    open json file and read it into a list of dictionaries
    """
    # Define the chunk size
    chunk_size = 1000

    # Create an empty DataFrame to store the combined data
    combined_data = pd.DataFrame()

    # Read JSON file in chunks
    for chunk in pd.read_json(jsonl_path, lines=True, chunksize=chunk_size):
        # Combine the chunks into a single DataFrame
        combined_data = pd.concat([combined_data, chunk])

    # Display the first few rows of the DataFrame
    print(combined_data.head())

    return combined_data


def plot_data(df):
    embeddings_list = df["embedding_gpt"].tolist()

    embeddings = np.array(embeddings_list)

    # Initialize t-SNE algorithm
    tsne = TSNE(n_components=2, random_state=42)

    # Fit and transform the embeddings to a 2D space
    embeddings_2d = tsne.fit_transform(embeddings)

    # Plot the t-SNE results
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
    plt.xlabel("t-SNE Component 1")
    plt.ylabel("t-SNE Component 2")
    plt.title("t-SNE Visualization of GPT Text Embeddings")

    plt.savefig("demo-vsearch.png", dpi=300)


def main():
    prod_file_path = "artifact/output_file.jsonl"
    df = read_jsonl_to_df(prod_file_path)


    while True:
        # Prompt the user for a search term
        search_term = input("Enter a search term (or 'q' to quit): ")
        if search_term.lower() == 'q':
            break

        # Get the embedding for the search term
        s = openai_embedding.get_embedding(search_term)

        # Plot the data
        plot_data(df, s)

if __name__ == "__main__":
    main()
