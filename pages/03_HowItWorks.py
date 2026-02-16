import streamlit as st

st.title("How It Works")

st.markdown("""
    This application is based off of a RAG-like system which uses vectors and embeddings to find
    similar pieces of text based on semantic meaning.  This can be seen as an improvement over
    searching for text that contains key words in a classic example of "bank".  You can try to search
    for text including "bank" or "chase" but you may get results containing rivers or people running
    after busses, not your region Chase Bank you were hoping for.  Semantic reasoning does a better job
    "understanding" the different meanings of those words by looking at what words are around them.
    \n
    The data was chunked into individual tasks notable within projects I had done.  Each chunk
    of text was then embedded into a 768-dimension vector using the open source model `all-mpnet-base-v2`. 
    Although far from the state-of-art, it suits the needs of this simple project and is free.  The database
    uses SQLite-vec for storage of data and embedding vectors.
    \n
    I have migration and ingestion scripts available for easy creation of a db file given a yaml file
    is completed.  I uploaded that db file to a Backblaze bucket, of which I linked to a streamlit web app
    hosted on the Community Cloud.  Many changes will likely be needed for the database as there are some
    things I want to include and remove.
    \n
    When the user enters some text into the text box to search relevant experiences, that text is converted
    into a vector and compared to all other vectors using cosine similarity.  The top few vectors are
    returned, given their similarity is above a certain threshold.  These chunks are then linked to their
    respective projects and entities, along with other chunks done in the same project for a more complete
    final output.  The projects seen show the first few most similar project descriptions to what the 
    user entered in the prompt.
""")