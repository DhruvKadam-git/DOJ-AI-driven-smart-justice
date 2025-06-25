import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to check if the question is DOJ specific
def is_doj_specific(question):
    doj_keywords = ["justice", "law", "court", "legal", "attorney", "prosecutor", "defendant", "plaintiff", "federal", "criminal", "civil rights"]
    return any(keyword in question.lower() for keyword in doj_keywords)

def get_chatgpt_response(question, chat_history=None):
    if chat_history is None:
        chat_history = []
    # Format history for OpenAI
    messages = [{"role": role.lower(), "content": text} for role, text in chat_history]
    messages.append({"role": "user", "content": question})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting response from ChatGPT: {e}")
        return ""

# Streamlit App UI
st.set_page_config(page_title="DOJ Specific ChatBot")
st.header("Welcome to the DOJ Specific ChatBot")

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Create input form
with st.form(key='input_form', clear_on_submit=True):
    user_input = st.text_input("Input:", key="input")
    submit = st.form_submit_button(label="Ask the question")

if submit and user_input:
    # Check if the input is DOJ specific
    if not is_doj_specific(user_input):
        st.error("Please ask a question related to the Department of Justice.")
    else:
        # Get response from ChatGPT
        response = get_chatgpt_response(user_input, st.session_state['chat_history'])

        # Store user query
        st.session_state['chat_history'].append(("You", user_input))

        # Display bot response
        st.subheader("The Response is")
        bot_response = response
        st.write(bot_response)
        st.session_state['chat_history'].append(("Bot", bot_response))

# Display chat history
st.subheader("The Chat History is")
for role, text in st.session_state['chat_history']:
    st.write(f"{role}: {text}")
