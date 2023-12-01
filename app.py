import requests
import streamlit as st
from PIL import Image
import os
import sys
import openai
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from langchain.agents import create_csv_agent
from langchain.llms import OpenAI
from gtts import gTTS
import base64
from datetime import datetime
import streamlit.components.v1 as components
#import logging

# import API key from .env file
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(
    page_title="QuickpartsIT",
    layout="wide",
    initial_sidebar_state="collapsed")

# Add an empty line to reduce space at the top
st.markdown(
        """
        <style>
        div.stApp {
            margin-top: -50px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
#logging.basicConfig(level=logging.INFO)
# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

def get_answer_csv(query: str) -> str:
    try:
        file = "raw.csv"
        agent = create_csv_agent(OpenAI(temperature=0), file, verbose=False)
        answer = agent.run(query)
        return answer
    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")
        st.info('This is an experimental version, so feel free to ask simpler questions as we fine-tune our system.')
        answer=""
        return answer
    except Exception as e:
        # Handle other exceptions
        #logging.info(f"An error occurred(Please refresh and try): {e}")
        answer=""
        return answer

def transcribe(audio_file):
    try:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, language="en")
        return transcript
    except openai.error.InvalidRequestError as e:
        #logging.info(f"InvalidRequestError: {e}")
        st.info("I'm sorry, I couldn't catch that. Could you please repeat your question?")
        transcript="I'm sorry, I couldn't catch that. Could you please repeat your question?"
        return transcript

def save_audio_file(audio_bytes, file_extension):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.{file_extension}"

    with open(file_name, "wb") as f:
        f.write(audio_bytes)

    return file_name

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = transcribe(audio_file)

    return transcript["text"]

def text_to_speech(text):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Format with milliseconds
    filename = f"output_{timestamp}.mp3"
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)
    #st.info(filename)
    # Convert audio data to base64
    audio_base64 = base64.b64encode(open(filename, 'rb').read()).decode('utf-8')
    # Generate a data URI for the audio
    audio_uri = f"data:audio/mp3;base64,{audio_base64}"
    st.cache_data.clear()
    audio_code = f"""
    <audio id="audioPlayer" autoplay>
        <source src="{audio_uri}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    <script>
        document.getElementById("audioPlayer").setAttribute("src", "{audio_uri}");
        document.getElementById("audioPlayer").play();
    </script>
    """
    st.markdown(audio_code, unsafe_allow_html=True)

def reportsGPT():
    st.image("images/report_charts.jpg", use_column_width="always")
    st.write("Ask about it")
    tab1, tab2 = st.tabs(["Speak", "Chat"])
    # Record Audio tab
    with tab1:
        audio_bytes = audio_recorder()
        if audio_bytes:
            st.cache_data.clear()
            #option to replay audio
            #st.audio(audio_bytes, format="audio/wav")
            save_audio_file(audio_bytes, "mp3")
            audio_file_path = max(
                [f for f in os.listdir(".") if f.startswith("audio")],
                key=os.path.getctime,
            )
            # Transcribe the audio file
            transcript_text = transcribe_audio(audio_file_path)
            if transcript_text != "I'm sorry, I couldn't catch that. Could you please repeat your question?":
                # Display the transcript
                st.header("Transcript")
                st.write(transcript_text)
                query=transcript_text
                response=get_answer_csv(query)
                if response != "":
                    st.write(response)
                    js_code="""
                    var u = new SpeechSynthesisUtterance();
                    u.text = "{response}";
                    u.lang = 'en-US';
                    speechSynthesis.speak(u);
                    """.format(response=response)
                    my_html = f"<script>{js_code}</script>"
                    components.html(my_html, width=0, height=0)
    #Chat Tab
    with tab2:
        query = st.text_area("Ask any question related to the tickets",label_visibility="hidden")
        button = st.button("Submit")
        if button:
            response=get_answer_csv(query)
            if response != "":
                st.write(response)


# Set up the working directory
working_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(working_dir)
# Run the main function
try:
    reportsGPT()
except Exception as e:
    # Handle other exceptions
    #logging.info(e)
    print(f"An error occurred(Please refresh and try): {e}")
    st.info("We ran into a problem. We're still in beta. Please refresh and try!")

