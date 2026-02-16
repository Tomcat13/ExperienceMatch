import streamlit as st

st.title("ExperienceMatch")

st.markdown("""
    \n
    Welcome to my ExperienceMatch site!  Interact with my professional, personal, and academic
    experiences through a retrieval-augmented lense.  No LLMs are used in this webpage.
    \n
""")

if st.button("Use ExperienceMatch"):
    st.switch_page("pages/02_ExperienceMatch.py")

if st.button("Project Background"):
    st.switch_page("pages/01_Background.py")

if st.button("How it Works"):
    st.switch_page("pages/03_HowItWorks.py")
    
st.markdown("""
    \n
    More to come!  If you have any recommendations,
    questions, or want to chat, please email me at reedyt22@gmail.com or message me 
    on [linkedin](https://www.linkedin.com/in/thomas-reedy-151363190/).  You can search
    for more projects on my [github](https://github.com/Tomcat13/SportsAnalytics).
    \n
       \- Thomas Reedy
""")