import streamlit as st
from streamlit_chat import message as st_message
from streamlit_option_menu import option_menu
import os
import plotly.express as px
from io import StringIO
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
import warnings
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, Table, MetaData
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt
from langchain_groq import ChatGroq
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import re

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-70b-versatile")


# Streamlit page configuration
st.set_page_config(
    page_title="TraffiTrack", 
    page_icon="", 
    layout="wide", 
    initial_sidebar_state="expanded", 
)

# Initialize session state for messages and banned users
if 'messages' not in st.session_state:
    st.session_state.messages = [{"message": "Hi! How can I assist you today?", "is_user": False}]
if 'banned_users' not in st.session_state:
    st.session_state.banned_users = []
if 'flowmessages' not in st.session_state:
    st.session_state.flowmessages = []


# Function to handle registration
def registration():
    st.title("User Registration")

    # Ensure session state is initialized
    if "user_data" not in st.session_state:
        st.session_state.user_data = []

    name = st.text_input("Enter your name")
    phone_number = st.text_input("Enter your phone number")

    if st.button("Register"):
        if name and phone_number:
            # Append user data to session state as a dictionary
            st.session_state.user_data.append({"name": name, "phone_number": phone_number})
            st.success("Registration successful!")
        else:
            st.warning("Please fill in all fields.")


# Function to simulate drug tracking data
def generate_sample_data():
    data = {
        "Drug Name": ["MDMA", "LSD", "Mephedrone", "Cocaine", "Heroin"],
        "Detected Instances": [10, 15, 7, 12, 5],
        "Flagged Users": [5, 10, 4, 7, 3],
        "IP Addresses": [3, 8, 2, 6, 2]
    }
    return pd.DataFrame(data)

# Function to check for drug-related content and extract info
def check_for_drug_content(input_text):
    drug_keywords = ["MDMA", "LSD", "Mephedrone", "Cocaine", "Heroin"]
    pattern = r'(\+?\d{1,3}[-. ]?)?\(?\d{1,4}?\)?[-. ]?\d{1,4}[-. ]?\d{1,4}[-. ]?\d{1,9}'  # Regex for phone numbers
    ip_pattern = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'  # Regex for IP addresses

    found_drugs = [keyword for keyword in drug_keywords if keyword.lower() in input_text.lower()]
    phone_numbers = re.findall(pattern, input_text)
    ip_addresses = re.findall(ip_pattern, input_text)

    return found_drugs, phone_numbers, ip_addresses

# Sidebar with options
selected = option_menu(
    "Main Menu", 
    ["Home", "Registration","Chat", "Statistics"], 
    icons=['house', 'person','chat-dots', 'bar-chart'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#DEF9C4"},
        "icon": {"color": "#468585", "font-size": "25px"},
        "nav-link": {
            "font-size": "16px", 
            "text-align": "left", 
            "margin": "0px", 
            "--hover-color": "#9CDBA6"
        },
        "nav-link-selected": {"background-color": "#50B498"},
    }
)


# Function to get a response from the chat model
def get_chatmodel_response(user_message):
    # Ensure user_message is a string
    if "user_data" in st.session_state and st.session_state.user_data:
        user_info = st.session_state.user_data[-1]  # Get the most recent registered user
        name = user_info.get("name", "Unknown")
        phone_number = user_info.get("phone_number", "Unknown")
    else:
        name = "Unknown"
        phone_number = "Unknown"

#better the prompt more formatting
#chat types -> human message
#response -> no drug message detected
#from registration
#remove debugging

    PROMPT_TEMPLATE = """You are an expert assistant specializing in detecting drug-related messages for monitoring illegal drug activities. Your role is to analyze user messages carefully to identify mentions of illegal substances or any activity related to drug trafficking, sales, or use.

Key substances to focus on:
- MDMA
- LSD
- Mephedrone
- Cocaine
- Heroin
- Marijuana
- Ecstasy
- Crack

Instructions:
1. If you detect any mention of the above substances or any activities related to drug sales, trafficking, or use, respond with a simple confirmation of detection, including the drug name.
2. **Do not** include the original user message in your response.
3. Ensure the format includes the following fields: sender's name, phone number, and the detected drug word.
4. If there is **no drug-related content**, respond with "drug word detected: none."

Below is the required format for your response:

         {name}
        {phone_number}
        drug word detected: {{drug_word_detected}}

        Below is the user message

        User message: {user_message}

        Response:
        """


    memory = ConversationBufferWindowMemory(k=5, return_messages=True)
    user_message = str(user_message)

    # Use the parameter user_message to format the prompt
    formatted_prompt = PROMPT_TEMPLATE.format(
        user_message=user_message,
        name=name,
        phone_number=phone_number
    )
    # Add the formatted prompt to the conversation history
    st.session_state.flowmessages.append(HumanMessage(content=user_message))

    # Generate a response from the model
    response = llm([SystemMessage(content=formatted_prompt)])

    # Ensure the response.content is a string
    response_content = str(response.content)

    # Add the AI response to the conversation history
    st.session_state.flowmessages.append(AIMessage(content=response_content))


    # Save the conversation context
    memory.save_context({"input": user_message}, {"output": response_content})

    return response_content


    
    # User input for query
    
    # Button to send the message
    # if st.button("Send"):
    #     if user_input:
    #         response = get_chatmodel_response(user_input)
    #         st.session_state.messages.append({"message": response, "is_user": False})
    #         st.experimental_rerun()
    #     else:
    #         st.warning("Please enter a message.")
    
    # Display the conversation history
    if "flowmessages" in st.session_state:
        st.subheader("Chat")
        for message in st.session_state.flowmessages:
            if isinstance(message, HumanMessage):
                st_message(message.content, is_user=True)
            elif isinstance(message, AIMessage):
                st_message(message.content, is_user=False)

def display_home_info():
    # Set background color
    st.markdown(
        """
        <style>
        .reportview-container {
            background: #DEF9C4;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Title with emoji
    st.title("🏠 Welcome to the Drug-Related Content Detector")

    # Section for description
    st.markdown(
        """
        <div style='background-color: #50B498; padding: 10px; border-radius: 5px;'>
            <h3 style='color: white;'>Our software solution helps identify drug-related content across multiple platforms.</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Features list
    st.write("### Features include:")
    st.markdown(
        """
        <ul style='list-style-type: none;'>
            <li>🌐 Real-time monitoring of messages.</li>
            <li>🖼️ Detection of images and text related to drug trafficking.</li>
            <li>📊 Comprehensive statistics and insights.</li>
        </ul>
        """,
        unsafe_allow_html=True
    )

if selected == "Registration":
    registration()

elif selected == "Home":
    display_home_info()

elif selected == "Chat":
    
    def traffitrack_chatbot():
        st.title('TraffiTrack 💬')

        # Dropdown to select platform
        platform = st.selectbox(
            "Choose a platform", 
            ["Live 💁‍♀️", "WhatsApp 📱", "Instagram 📸", "Telegram ✉️"], 
            index=0
        )

        if platform == "Telegram ✉️":
            # Hardcoded CSV content
            csv_content = """sender_name,sender_id,phone_number,message_text
    Shruti,1580593004,917304814120,But I would prefer blowing a bag of Charlie
    Shruti,1580593004,917304814120,I want to eat ice cream i am bored
    Shruti,1580593004,917304814120,He’s heavily into smack
    Shruti,1580593004,917304814120,There was a bag of snow in the car
    Shruti,1580593004,917304814120,Did you bring the Mary Jane for the party tonight?
    Shruti,1580593004,917304814120,Mary Jane
    Ritika,1065437474,918828000465,I WANT A BAG OF CHARLIE
    Ritika,1065437474,918828000465,Okayy
    Preeyaj,6649015430,,Haa bhej cocain thoda
    Ritika,1065437474,918828000465,Maal chahiye?
    Preeyaj,6649015430,,Llm
    Ritika,1065437474,918828000465,Kya kar rahe ho?
    Ritika,1065437474,918828000465,Hey"""

            # Read the CSV content into a DataFrame
            messages_df = pd.read_csv(StringIO(csv_content))
            # Reverse the DataFrame to display messages from first to last
            for idx, row in messages_df[::-1].iterrows():  # Reverse the DataFrame here
                sender_name = row['sender_name']
                message_text = row['message_text']
                # Display each message with its corresponding sender name
                st_message(f"{sender_name}: {message_text}", is_user=False, key=f"telegram_message_{idx}")

            if st.button("Analyze 🚨"):
                # Initialize count and list for drug-related messages
                drug_count = 0  # Initialize drug_count here
                drug_messages = []
                user_data = {}  # Initialize user data dictionary

                # Analyze each message for drug-related content
                for idx, row in messages_df.iterrows():
                    message_text = row['message_text']
                    sender_name = row['sender_name']
                    sender_id = row['sender_id']
                    phone_number = row['phone_number']

                    # Get response from the chat model
                    response_content = get_chatmodel_response(message_text)

                    # Check for drug word detected in the response
                    if "drug word detected" in response_content and "none" not in response_content:
                        drug_word = response_content.split("drug word detected: ")[1].strip()
                        drug_count += 1
                        drug_messages.append({
                            "sender_name": sender_name,
                            "sender_id": sender_id,
                            "phone_number": phone_number,
                            "message_text": message_text,
                            "drug_word": drug_word
                        })
                        # Aggregate data by user
                        if sender_name not in user_data:
                            user_data[sender_name] = {
                                "phone_number": phone_number,
                                "message_count": 0,
                                "drug_words": []
                            }
                        user_data[sender_name]["message_count"] += 1
                        user_data[sender_name]["drug_words"].append(drug_word)

                # Display statistics
                st.subheader("Analysis Results 📊")
                st.write(f"Total drug-related messages detected: {drug_count}")

                if drug_count > 0:
                    # st.write("Details of detected messages:")
                    # for message in drug_messages:
                    #     st.markdown(f"**Phone Number**: {message['phone_number']}  \
                    #                 **Sender ID**: {message['sender_id']}  \
                    #                 **Message**: {message['message_text']}  \
                    #                 **Drug Detected**: {message['drug_word']}")
                    
                    # Prepare data for visualization
                    user_names = list(user_data.keys())
                    message_counts = [data["message_count"] for data in user_data.values()]
                    phone_numbers = [data["phone_number"] for data in user_data.values()]

                    # 1. Bar chart: Messages per user
                    st.markdown("### Number of Messages per User 📊")
                    fig = px.bar(
                        x=user_names, 
                        y=message_counts, 
                        labels={'x': 'User Name', 'y': 'Message Count'}, 
                        title="Messages Detected per User"
                    )
                    st.plotly_chart(fig)

                    # 2. Pie chart: Distribution of drug-related messages
                    st.markdown("### Drug Distribution Among Users 🍰")
                    drugs_detected = [drug for user in user_data.values() for drug in user["drug_words"]]
                    fig = px.pie(
                        names=drugs_detected, 
                        title="Distribution of Detected Drugs"
                    )
                    st.plotly_chart(fig)

                    # 3. Horizontal bar chart: Number of drug-related messages per user
                    st.markdown("### Drug-related Messages per User 📊")
                    fig = px.bar(
                        y=user_names, 
                        x=message_counts, 
                        orientation='h', 
                        labels={'y': 'User Name', 'x': 'Drug-related Messages Count'}, 
                        title="Drug-related Messages per User"
                    )
                    st.plotly_chart(fig)

                    # 4. Display user details in a table
                    st.markdown("### User Details Table 📋")
                    user_df = pd.DataFrame({
                        "User Name": user_names,
                        "Phone Number": phone_numbers,
                        "Message_id" : sender_id,
                        "Messages Detected": message_counts
                    })
                    st.dataframe(user_df)

                    # Optionally: Link to the statistics page
                    st.markdown("[View Statistics Page](#)")
                else:
                    st.write("No drug-related messages detected.")

        else:
            # Display chat messages for other platforms with unique keys
            for idx, msg in enumerate(st.session_state.messages):
                st_message(msg["message"], is_user=msg["is_user"], key=f"message_{idx}")

            # Input for user query
            input_text = st.text_input("Enter your text", key="user_input")

            if st.button("Send"):
                if input_text:
                    # Append the user's message to session state
                    st.session_state.messages.append({"message": input_text, "is_user": True})

                    # Get the response from the model
                    response = get_chatmodel_response(input_text)

                    # Append the response from the model
                    st.session_state.messages.append({"message": response, "is_user": False})

                    # Rerun to refresh the UI with new messages
                    st.experimental_rerun()
                else:
                    st.warning("Please enter a message.")

    # Call the chatbot function
    traffitrack_chatbot()


elif selected == "Statistics":
    st.title('Drug Trafficking Statistics 📊')

    # Generate sample data
    data = generate_sample_data()

    # Display data
    st.subheader("Overview of Detected Drugs")
    st.dataframe(data)

    # Plotting the data
    st.subheader("Detected Instances of Drugs")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data["Drug Name"], data["Detected Instances"], color="#50B498")
    plt.title("Detected Instances of Drugs")
    plt.xlabel("Drug Name")
    plt.ylabel("Detected Instances")
    st.pyplot(fig)

    # Plotting flagged users
    st.subheader("Flagged Users")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data["Drug Name"], data["Flagged Users"], color="#468585")
    plt.title("Flagged Users")
    plt.xlabel("Drug Name")
    plt.ylabel("Flagged Users")
    st.pyplot(fig)

    # Plotting IP addresses
    st.subheader("Detected IP Addresses")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data["Drug Name"], data["IP Addresses"], color="#9CDBA6")
    plt.title("Detected IP Addresses")
    plt.xlabel("Drug Name")
    plt.ylabel("Detected IP Addresses")
    st.pyplot(fig)

# Custom CSS for a better user interface
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #DEF9C4;
        color: #468585;
    }}
    .stButton>button {{
        background-color: #50B498; 
        color: #ffffff; 
        border: none;
        border-radius: 8px;
        font-size: 16px;
        padding: 10px 20px;
        cursor: pointer;
    }}
    .stButton>button:hover {{
        background-color: #9CDBA6;
    }}
    .stTextInput>input {{
        background-color: #468585; 
        color: #ffffff;
        border: 2px solid #50B498;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }}
    h1, h2, h3 {{
        color: #50B498;
    }}
    .stDataFrame {{
        background-color: #ffffff;
        color: #000000;
        border-radius: 10px;
        padding: 10px;
    }}
    </style>
""", unsafe_allow_html=True)
