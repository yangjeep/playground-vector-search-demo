
from lib2to3.pgen2.pgen import DFAState
import pandas as pd

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

import openai

import openai_embedding
from scipy.spatial import distance


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


def plot_data(df, s, labels=None):
    embeddings_list = df["embedding_gpt"].tolist()
    titles_list = df["title"].tolist()  # assuming "title" is the name of the column with titles

    # Append the search term embedding to the list
    embeddings = np.array(embeddings_list)
    embeddings = np.append(embeddings, [s], axis=0)

    # Initialize t-SNE algorithm
    tsne = TSNE(n_components=2, random_state=42)

    # Fit and transform the embeddings to a 2D space
    embeddings_2d = tsne.fit_transform(embeddings)

    # Create a scatter plot
    scatter = plt.scatter(embeddings_2d[:-1, 0], embeddings_2d[:-1, 1], c=labels)

    # Add the search term to the plot
    plt.scatter(embeddings_2d[-1, 0], embeddings_2d[-1, 1], c='red')

    # If labels provided, add a colorbar
    if labels is not None:
        plt.colorbar(scatter)

    plt.xlabel("t-SNE Component 1")
    plt.ylabel("t-SNE Component 2")
    plt.title("t-SNE Visualization of GPT Text Embeddings")

    # Compute the distances from the search term to all other points
    dists = distance.cdist([embeddings_2d[-1]], embeddings_2d[:-1], 'euclidean')[0]
    
    # Get the indices of the five closest points
    closest_idxs = dists.argsort()[:5]
    
    # Print the titles of the five closest points on the plot
    for idx in closest_idxs:
        plt.text(embeddings_2d[idx, 0], embeddings_2d[idx, 1], titles_list[idx], fontsize=8)
        print(titles_list[idx])


    plt.show()
    # plt.savefig("demo-vsearch.png", dpi=300)




def main():
    openai.api_key = openai_embedding.read_env_file()

    prod_file_path = "artifact/output_file.jsonl"
    df = read_jsonl_to_df(prod_file_path)


    while True:
        # Prompt the user for a search term
        search_term = input("Enter a search term (or 'q' to quit): ")
        if search_term.lower() == 'q':
            break

        # Get the embedding for the search term
        s = openai_embedding.embedding_encode(search_term)

        # Plot the data
        plot_data(df, s)

if __name__ == "__main__":
    main()
