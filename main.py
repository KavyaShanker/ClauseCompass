import base64
import re
import time

import pdfplumber
import streamlit as st
import hashlib
from datetime import datetime
from streamlit_pdf_viewer import pdf_viewer
from PIL import Image
from pymongo import MongoClient
from bson import ObjectId
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv
# from transformers import AutoConfig
import fitz
from transformers import AutoConfig

from comparison import compare
from model import extract_clauses, process_pdf

# Load environment variables
load_dotenv()

model_path = 'mymodel'
config = AutoConfig.from_pretrained(model_path)
# print(config)



# def extract_text_from_pdf(file):
#     # Open the PDF file
#     doc = fitz.open(stream=file.read(), filetype="pdf")
#
#     text = ""
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)
#         text += page.get_text()  # Extract text from the page
#
#     return text

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages])

class DatabaseManager:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        self.client = MongoClient(connection_string)
        self.db = self.client.contract_analyzer

        # Create indexes
        self.db.users.create_index("username", unique=True)
        self.db.documents.create_index([("user_id", 1), ("uploaded_at", -1)])

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username: str, password: str) -> Optional[str]:
        try:
            result = self.db.users.insert_one({
                "username": username,
                "password_hash": self.hash_password(password),
                "created_at": datetime.utcnow()
            })
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error adding user: {e}")
            return None

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        try:
            user = self.db.users.find_one({"username": username})
            if user and user["password_hash"] == self.hash_password(password):
                return {
                    "user_id": str(user["_id"]),
                    "username": user["username"]
                }
            return None
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None

    def save_document(self, user_id: str, filename: str, analysis: list) -> bool:
        try:
            # Convert string user_id to ObjectId
            user_object_id = ObjectId(user_id)

            result = self.db.documents.insert_one({
                "user_id": user_object_id,
                "filename": filename,
                "analysis": analysis,
                "uploaded_at": datetime.utcnow()
            })
            return bool(result.inserted_id)
        except Exception as e:
            print(f"Error saving document: {e}")
            return False

    def get_user_documents(self, user_id: str) -> List[Dict]:
        try:
            # Convert string user_id to ObjectId
            user_object_id = ObjectId(user_id)

            documents = self.db.documents.find(
                {"user_id": user_object_id}
            ).sort("uploaded_at", -1)

            # Convert documents to list and handle ObjectId serialization
            return [{
                "id": str(doc["_id"]),
                "filename": doc["filename"],
                # "summary": doc["summary"],
                "analysis": doc["analysis"],
                "uploaded_at": doc["uploaded_at"].strftime("%d %b, %Y at %H:%M:%S")
            } for doc in documents]
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []


def analyze_contract(contract_text: str) -> tuple[str, str]:
    # Placeholder for contract analysis logic
    summary = f"Sample summary of contract ({len(contract_text)} characters)"
    analysis = "Sample detailed analysis of key terms and conditions"
    return summary, analysis

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

def main():
    st.set_page_config(page_title="Contract Analyzer", layout="wide")

    # Initialize session state
    init_session_state()

    # Initialize database connection
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    db = DatabaseManager(mongo_uri)


    # Sidebar for navigation
    if not st.session_state.logged_in:
        st.sidebar.markdown("<h1><b>Welcome to<br>Clause Compass</b></h1>",
                            unsafe_allow_html=True)
        auth_option = st.sidebar.radio("Choose an action:", ["Login", "Register"])

        if auth_option == "Login":
            image = Image.open('eight.jpg')  # Replace with the path to your image
            # Create two columns
            left_column, right_column = st.columns([1.5, 1],
                                                   gap="large")  # Adjust the width ratio between columns if needed

            # image in the left column
            with left_column:
                # st.title("")
                st.image(image, caption="", width=580)

            # right column
            with right_column:
                st.title("")
                st.subheader("")
                # st.title("")
                st.header("Login")

                with st.form("login_form"):
                    username = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    submit_button = st.form_submit_button("Login")

                    if submit_button:
                        user_info = db.verify_user(username, password)
                        if user_info:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_info["user_id"]
                            st.session_state.username = user_info["username"]
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password")

        else:  # Sign Up
            image = Image.open('nine.jpg')  # Replace with the path to your image

            # Create two columns
            left_column, right_column = st.columns([1.5, 1],
                                                   gap="large")  # Adjust the width ratio between columns if needed

            # image in the left column
            with left_column:
                st.title("")
                st.image(image, caption="", width=650)

            with right_column:
                # st.title("")
                st.subheader("")
                # st.title("")
                st.header("Sign Up")

                with st.form("signup_form"):
                    new_username = st.text_input("Enter Email")
                    new_password = st.text_input("Choose Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    submit_button = st.form_submit_button("Sign Up")

                    if submit_button:
                        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_username):
                            st.error("Please enter a valid email address.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match!")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters long!")
                        else:
                            user_id = db.add_user(new_username, new_password)
                            if user_id:
                                st.success("Account created successfully! Please login.")
                            else:
                                st.error("Username already exists!")

    else:
        # Show username in sidebar
        # st.sidebar.write(f"Logged in as: {st.session_state.username}")
        st.sidebar.title("Clause Compass")


        # Navigation
        page = st.sidebar.radio("Navigation", ["Analyse", "Compare", "History"])
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        st.sidebar.title("")
        # st.sidebar.title("")
        # st.sidebar.title("")
        # st.sidebar.title("")
        # st.sidebar.title("")

        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
        # clauses = [('',''), ('',''), ('','')]
        clauses = [('',''), ('',''), ('','')]
        summary =''
        if page == "Analyse":
            st.header("Analyse")
            # st.markdown("Your AI-Powered Contract Analysis Tool")
            with st.container(border=True):
                # st.write("Upload a contract document for instant analysis and summary")

                col1, col2 = st.columns(2, gap="large")

                with col1:
                    with st.container(border=True):
                        uploaded_file = st.file_uploader("Upload a legal document", type=["pdf"])

                        if uploaded_file is not None:
                            # st.write(f"File uploaded: {uploaded_file.name}")
                            text = extract_text_from_pdf(uploaded_file)
                            # print(extract_clauses(pararapghs))

                            if st.button("Analyze"):
                                with st.spinner("Analyzing..."):

                                    # analysis = extract_clauses(text)
                                    # clauses = extract_clauses(text)
                                    # clauses = extract_clauses(text)
                                    clauses = process_pdf(uploaded_file)
                                    # print(clauses)

                                    summary = "Summary goes here."
                                    # print("Critical Clauses: ", clauses)
                                    # st.info("Please upload a legal document for analysis.")
                                    # Simulating document analysis
                                    time.sleep(2)  # Simulating processing time
                                    if uploaded_file:
                                        binary_data = uploaded_file.getvalue()
                                        pdf_viewer(input=binary_data)

                                        # summary, analysis = analyze_contract(contract_text)
                                        summary="Summary Function Call"
                                        analysis = clauses

                                        db.save_document(
                                            st.session_state.user_id,
                                            uploaded_file.name,
                                            analysis
                                        )
                                        st.session_state.analysis = analysis
                                        st.session_state.summary = summary

                                    else:
                                        st.info("Please upload a legal document for analysis.")

                with col2:
                    # st.write("Analysis results will appear here")
                    if 'analysis' in st.session_state:
                        st.subheader("Critical Clauses")
                        # st.write("1. " + clauses)
                        st.write(clauses)
                        # st.write("1. " + clauses[0])
                        # st.write("2. " + clauses[1])
                        # st.write("3. " + clauses[2])
                        # st.write(summary)
                        # st.subheader("Summary")
                        # st.write(summary)

                        # st.write("Critical", analysis)
                        st.session_state.critical = clauses

                        # if st.button("Download Analyzed Document"):
                        #     # In a real application, you would generate this file
                        #     mock_pdf_bytes = b"Mock PDF content"
                        #     b64 = base64.b64encode(mock_pdf_bytes).decode()
                        #     href = f'<a href="data:application/pdf;base64,{b64}" download="analyzed_contract.pdf">Download Analyzed Document</a>'
                        #     st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.write("Analysis results will appear here")


        if page == "History":  # View History
            st.header("History")
            # st.session_state.analysis=None

            if st.session_state.user_id:
                documents = db.get_user_documents(st.session_state.user_id)

                print("Documents: ", documents)

                if not documents:
                    st.info("No documents analyzed yet!")
                else:
                    for doc in documents:
                        with st.expander(f"{doc['filename']} ⊛ {doc['uploaded_at']}"):
                            st.subheader("Critical Clauses")
                            st.write(doc['analysis'])
                            # st.write("1. " + doc['analysis'][0][0])
                            # st.write("2. " + doc['analysis'][1][0])
                            # st.write("3. " + doc['analysis'][2][0])
                            # st.subheader("Summary")
                            # st.write(doc['summary'])
                            # st.write("The Social Media Management Contractual Agreement outlines the terms between the Client and the Social Media Manager, detailing the services to be provided, including strategy development, content creation, posting, monitoring, and advertising. It specifies that all original content created will belong to the Client, mandates confidentiality, allows for termination with notice, addresses force majeure events, and includes provisions for renewal, fees, amendments, severability, and dispute resolution under specified laws. The agreement concludes with signature lines for both parties.")
                            # st.write(doc['analysis'])
                            # st.button("Download")
                                # In a real application, you would generate this file
                                # mock_pdf_bytes = b"Mock PDF content"
                                # b64 = base64.b64encode(mock_pdf_bytes).decode()
                                # href = f'<a href="data:application/pdf;base64,{b64}" download="analyzed_contract.pdf">Download Analyzed Document</a>'
                                # st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("User ID not found. Please log out and log in again.")

        elif page=="Compare": #Compare
            st.header("Compare")

            # File uploader for two PDFs
            col1, col2 = st.columns(2)

            with col1:
                pdf_file_1 = st.file_uploader("Upload First Contract", type="pdf")

            with col2:
                pdf_file_2 = st.file_uploader("Upload Second Contract", type="pdf")



            # Display PDFs side by side
            if pdf_file_1 and pdf_file_2:
                comparison = compare(pdf_file_1, pdf_file_2)
            #     # st.dataframe(comparison, use_container_width=True)
                st.dataframe(comparison, use_container_width=True)




if __name__ == "__main__":
    main()