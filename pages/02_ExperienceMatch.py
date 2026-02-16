# imports
import pandas as pd
import numpy as np
import streamlit as st
import sqlite3
import sqlite_vec
from b2sdk.v2 import InMemoryAccountInfo, B2Api
import boto3
from sentence_transformers import SentenceTransformer

import sys
import os
# probably old, but will keep in case file systems change
#parent_dir = os.path.dirname(os.path.dirname(__file__))  # goes up one level from pages/
#if parent_dir not in sys.path:
#    sys.path.append(parent_dir)

# custom imports
from utils.support import process_query

# set database constants
B2_KEY_ID = st.secrets["B2_KEY_ID"]
B2_APP_KEY = st.secrets["B2_APP_KEY"]
B2_ENDPOINT = st.secrets["B2_ENDPOINT"]
BUCKET_NAME = "rag-resume-thomas-reedy"
DB_FILE_NAME = "resume.db"

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

# OLD APPROACH
# download db and cache it
@st.cache_data(show_spinner=True)
def get_db_file():
    local_path = os.path.join("temp_data", DB_FILE_NAME)
    os.makedirs("temp_data", exist_ok=True)

    downloaded_file = bucket.download_file_by_name(DB_FILE_NAME)
    downloaded_file.save_to(local_path)

    return local_path

# NEW APPROACH
@st.cache_resource
def download_db():
    session = boto3.session.Session()

    s3 = session.client(
        service_name='s3',
        endpoint_url=st.secrets["B2_ENDPOINT"],
        aws_access_key_id=st.secrets["B2_KEY_ID"],
        aws_secret_access_key=st.secrets["B2_APP_KEY"],
    )

    local_path = "temp_data/resume.db"

    # Download once per container lifecycle
    s3.download_file(
        BUCKET_NAME,
        DB_FILE_NAME,
        local_path
    )

    return local_path

# load db into memory

@st.cache_resource
def load_db_into_memory():
    local_path = download_db()

    disk_conn = sqlite3.connect(local_path)
    #memory_conn = sqlite3.connect(":memory:")
    memory_conn = sqlite3.connect(
        ":memory:",
        check_same_thread=False
    )

    # Copy entire DB into RAM
    disk_conn.backup(memory_conn)
    disk_conn.close()

    # Optional safety
    memory_conn.execute("PRAGMA query_only = ON;")

    return memory_conn


# get file from backblaze
#db_path = get_db_file()

# test locally
#db_path = st.secrets["LOCAL_DB_PATH"]

# connect to sqlite
#conn = sqlite3.connect(db_path)

# new way to connect
conn = load_db_into_memory()
cursor = conn.cursor()

# ExperienceMatch!
st.title("ExperienceMatch")

user_input = st.text_input("Match an Experience: ", key="input_box")

# give examples to ask:
if not user_input:
    st.markdown(f"""
        Example prompts to ask:
        - Built ETL pipeline for NLP
        - Trained a random forest model
        - Designed a database schema
        - Improved SQL queries
        \n
        For more inspiration, check out my
        [linkedin](https://www.linkedin.com/in/thomas-reedy-151363190/)
        or [sports analytics github](https://github.com/Tomcat13/SportsAnalytics)
    """)

else:

    # get all the data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    if "entities" not in tables: 
        st.error("Error getting database.  Please try again or come back tomorrow.")
    else:
        # get all the embedding stuff ready
        EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)


        # return most similar experiences
        results = process_query(user_input, cursor)

        if results:
            # I'll likely make formatting requirements based on whether its a class project
            # or a work experience etc.  This will be saved in another python file

            # get total results
            unique_projects = set(result[0] for result in results)
            st.write(f"Showing results for top {min( 3, len(unique_projects) )} experience matches.")
            
            st.divider()

            # limit outputs
            projects = []
            output_increment = 0

            # loop through all results
            for result in results:

                # for debugging
                #st.write(result)

                # ensure project isn't repeated
                if result[0] in projects:
                    continue
                else:
                    projects.append(result[0])
                    output_increment += 1

                # get max of three outputs
                if output_increment > 3:
                    break

                # make the mix of company and title when available
                if result[7] == 'course':
                    st.header(str(result[6]) + ' - ' + str(result[8]))
                else:
                    if result[9]:
                        if result[8]:
                            st.header( str(result[9]) + ', ' + str(result[8]) )
                        else:
                            st.header( str(result[9]) )
                    elif result[8]:
                        st.header( result[8] )

                # convert end date to present if not available
                if result[12]:
                    end_date = str(result[12])
                else:
                    end_date = 'present'
                # only display the job's start date if there's a start date
                if result[11]:
                    st.write(f"Date Range:  " + str(result[11]) +
                                " - " + str(end_date)
                            )
                # display project name
                # all i have is id... might want to change this in the future
                #st.write(f"Project ID: {results[i][0]}")
                st.subheader(result[-3])

                # show the similarity score
                st.write(f"Similarity Score: {result[-1]:.2f}")

                # later, can add specific dates for the project here

                # show url if present
                if result[13]:
                    st.write(f"URL: " + str(result[13]))

                # now, find the other descriptors that matched
                sub_query = f"SELECT chunk_type, content FROM chunks WHERE entity_id = '{result[3]}' "
                cursor.execute(sub_query)
                sub_results = cursor.fetchall()

                # write all other descriptions and results
                actions = [row for row in sub_results if row[0] == 'description']
                impacts = [row for row in sub_results if row[0] == 'outcomes']

                if actions:
                    st.write("Actions:")
                    for action in actions:
                        st.markdown(f"- {action[1]}")
                if impacts:
                    st.write("Impacts:")
                    for impact in impacts:
                        st.markdown(f"- {impact[1]}")

                # get skills associated to the project
                sub_query = f"""
                    SELECT 
                        e.title,
                        e.id,
                        r.*
                    FROM relations r
                    LEFT JOIN entities e ON r.to_id = e.id
                    WHERE
                        r.from_id = '{result[3]}'
                        AND r.relation = 'uses'
                        AND e.id = r.to_id
                """
                cursor.execute(sub_query)
                skills = cursor.fetchall()

                if skills:
                    st.write("Skills and Tools Used:")
                    list_skills = [skill[0] for skill in skills]
                    skill_string = ', '.join(list_skills)
                    st.markdown(f"- {skill_string}")

                # finish with experience section
                st.divider()

        else:
            st.write("No results found in the database for that experience.")
            st.write("Please try rephrasing your prompt or try to match a different experience.")
            st.write("\n")
            st.markdown(f"""
                    Example prompts to ask:
                    - Trained a random forest model
                    - Built ETL pipeline for NLP
                    - Designed a database schema
                    - Improved SQL queries
                """)

    #conn.close()