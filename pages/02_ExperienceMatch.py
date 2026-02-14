import pandas as pd
import streamlit as st
import sqlite3
import os
from b2sdk.v2 import InMemoryAccountInfo, B2Api

B2_KEY_ID = st.secrets["B2_KEY_ID"]
B2_APP_KEY = st.secrets["B2_APP_KEY"]
BUCKET_NAME = "rag-resume-thomas-reedy"
DB_FILE_NAME = "resume.db"

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

# download db and cache it
@st.cache_data(show_spinner=True)
def get_db_file():
    local_path = os.path.join("temp_data", DB_FILE_NAME)
    os.makedirs("temp_data", exist_ok=True)

    downloaded_file = bucket.download_file_by_name(DB_FILE_NAME)
    downloaded_file.save_to(local_path)

    return local_path



# get file from backblaze
db_path = get_db_file()

# test locally
#db_path = st.secrets["LOCAL_DB_PATH"]

# connect to sqlite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()



st.title("ExperienceMatch")

# get all the data
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

if "entities" not in tables:
    st.error("Error getting database.  Please try again or come back tomorrow.")
else:
    # run main query
    query = """
        SELECT
            c.entity_id,
            c.chunk_type,
            c.content,
            r.*,
            e.*
        FROM chunks c
        LEFT JOIN relations r ON r.from_id = c.entity_id
        LEFT JOIN entities e ON e.id = r.to_id
        WHERE 
            c.id = 'athlete_crawler:description:0'
            AND r.relation = 'part_of'
    """

    cursor.execute(query)
    results = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    if results:
        # for later... this should then go and loop through the results
        # I'll likely make formatting requirements based on whether its a class project
        # or a work experience etc.  This will be saved in another python file

        st.write(f"Results for top {len(results)} experience matches.")
        st.divider()

        
        # make the mix of company and title when available
        if results[0][9]:
            if results[0][8]:
                st.subheader( str(results[0][9]) + ', ' + str(results[0][8]) )
            else:
                st.subheader( str(results[0][9]) )
        else:
            if results[0][8]:
                st.subheader( results[0][8] )

        # display project name
        # all i have is id... might want to change this in the future
        st.write(f"Project ID: {results[0][0]}")

        # convert end date to present if not available
        if str(results[0][12]):
            end_date = str(results[0][12])
        else:
            end_date = 'present'
        # only display the date if there's a start date
        if results[0][11]:
            st.write(f"Date Range:  " + str(results[0][11]) +
                        " - " + str(end_date)
                )

        # show url if present
        if results[0][13]:
            st.write(f"URL: " + str(results[0][13]))

        # write the part that matched
        #st.markdown(f"""
        #    Matched {results[0][1].capitalize()}:
        #    - {results[0][2]}
        #""")

        # now, find the other descriptors that matched
        sub_query = "SELECT chunk_type, content FROM chunks WHERE entity_id = 'athlete_crawler' ORDER BY chunk_type ASC"
        cursor.execute(sub_query)
        sub_results = cursor.fetchall()

        # write all other descriptions and results
        actions = [row for row in sub_results if row[0] == 'description'] #and row[1] != results[0][2]]
        impacts = [row for row in sub_results if row[0] == 'outcomes'] #and row[1] != results[0][2]]

        if actions:
            st.write("Actions:")
            for action in actions:
                st.markdown(f"- {action[1]}")
        if impacts:
            st.write("Impacts:")
            for impact in impacts:
                st.markdown(f"- {impact[1]}")


        st.divider()

        #df = pd.DataFrame(results, columns=columns)
        #st.dataframe(df)
    else:
        st.write("No results found in the database.")

conn.close()