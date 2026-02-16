# imports
import sqlite3
import sqlite_vec
import numpy as np
from sentence_transformers import SentenceTransformer
import pathlib as Path

# embedding model
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# saves from a complex import
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# process the query
def process_query(user_input, cursor, thresh=0.25, top_k=6):
    # this is far from "efficient" but it saves an import and the datafile is small
    # if I need to update this in the future, I will

    # turn user query into a vector
    query_vector = model.encode(user_input, normalize_embeddings=True).astype("float32")

    # next, get the vectors that align well with what the user inputted
    query = """
            SELECT
                c.entity_id,
                c.chunk_type,
                c.content,
                r.*,
                e.*,
                p.id as project_id,
                p.role as project_name,
                c.id as chunk_id_,
                ce.embedding
                
            -- get main data from the chunks
            FROM chunks c
            
            -- first join to get the relations
            LEFT JOIN relations r ON r.from_id = c.entity_id
            
            -- get the entity that does the relating to the chunk
            LEFT JOIN entities e ON e.id = r.to_id
            
            -- get the project that relates to the chunk
            LEFT JOIN projects p on p.id = c.entity_id
            
            -- get the chunk embeddings for comparison
            LEFT JOIN chunk_embeddings ce ON c.id = ce.chunk_id
            
            -- make sure the realtion is part of (filters out skills)
            WHERE r.relation = 'part_of'
        """
    cursor.execute(query)
    results = cursor.fetchall()

    # reformat things
    new_results = []
    for result in results:
        result = list(result)
        result[-1] = np.frombuffer(result[-1], dtype=np.float32)
        new_results.append(result)

    # compute cosine similarity
    query_vector = np.array(query_vector, dtype=np.float32)
    for r in new_results:
        r[-1] = float(np.dot(query_vector, r[-1]) /
                      (np.linalg.norm(query_vector) * np.linalg.norm(r[-1]) + 1e-8))

    # return top-k above a given threshold
    new_results.sort(key=lambda x: x[-1], reverse=True)
    best_results = [r for r in new_results if r[-1] > thresh]
    return best_results[:top_k]
    
    
    