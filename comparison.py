# -*- coding: utf-8 -*-
"""DocumentComparer.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zBW0n0JEF5MAfKHwTWyG_b_9ft3FPviA
"""
import pdfplumber
# prompt: unzip mymodel.zip

# !unzip mymodel.zip

# prompt: define tokenizer and model
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
model = AutoModel.from_pretrained("mymodel")

# ! pip install pdfplumber

# ! pip install python-docx

# # prompt: unzip mymodel and apply it to every 10 sentences in Contact 1.odf

# from transformers import AutoTokenizer, AutoModel
# from sklearn.metrics.pairwise import cosine_similarity
# import difflib
# import pdfplumber  # For PDF extraction
# from docx import Document  # For DOCX extraction
# import numpy as np
# import torch

def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages])


from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import pandas as pd
# Load the model and tokenizer once for efficiency
model = AutoModelForSequenceClassification.from_pretrained("mymodel")
tokenizer = AutoTokenizer.from_pretrained("nlpaueb/bert-base-uncased-contracts")

# List of all clause names
all_class_names = ['Affiliate License-Licensee', 'Affiliate License-Licensor', 'Agreement Date', 'Anti-assignment',
                   'Audit Rights', 'Cap on Liability', 'Change of Control', 'Competitive Restriction Exception',
                   'Covenant not to Sue', 'Document Name', 'Effective Date', 'Exclusivity', 'Expiration Date',
                   'Governing Law', 'IP Ownership Assignment', 'Insurance', 'Irrevocable or Perpetual License',
                   'Joint IP Ownership', 'License Grant', 'Liquidated Damages', 'Minimum Commitment',
                   'Most Favored Nation', 'No-Solicit of Customers', 'Non-Compete', 'Non-Disparagement',
                   'Non-Transferable License', 'Notice Period to Terminate Renewal', 'Notice Period to Terminate Renewal- Answer',
                   'Parties', 'Post-termination Services', 'Price Restrictions', 'ROFR-ROFO-ROFN', 'Renewal Term',
                   'Revenue-Profit Sharing', 'Source Code Escrow', 'Termination for Convenience', 'Third Party Beneficiary',
                   'Uncapped Liability', 'Unlimited/All-You-Can-Eat License', 'Volume Restriction', 'Warranty Duration']
def compare(file1, file2):
    def extract_clauses(document_text):
        clause_dict = {}

        # Iterate through each paragraph in the document
        for paragraph in document_text:
            # Tokenize the paragraph
            inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, padding=True)

            # Make predictions without gradient calculation
            with torch.no_grad():
                outputs = model(**inputs)

            # Extract logits and get the top predicted class index
            logits = outputs.logits[0]
            top_class_index = torch.argmax(logits).item()

            # Get the corresponding clause name from the list
            predicted_clause = all_class_names[top_class_index]

            # Append to dictionary if this clause isn't already added
            if predicted_clause not in clause_dict:
                clause_dict[predicted_clause] = paragraph
            else:
                clause_dict[predicted_clause] += "\n" + paragraph  # Append additional text for the same clause if it appears again

        return clause_dict

    input_text1 = contract_text_1 = extract_text_from_pdf(file1)
    # Split input_text into paragraphs by double newline
    document_text = [paragraph.strip() for paragraph in input_text1.strip().split("\n")]

    # Now document_text is ready for clause extraction
    print(document_text)

    input_text1 = contract_text_1 = extract_text_from_pdf(file1)
    # Split input_text into paragraphs by double newline
    document_text1 = [paragraph.strip() for paragraph in input_text1.strip().split("\n")]

    input_text2 = contract_text_2 = extract_text_from_pdf(file2)
    # Split input_text into paragraphs by double newline
    document_text2 = [paragraph.strip() for paragraph in input_text2.strip().split("\n")]

    clause_extractions1 = extract_clauses(document_text1)
    clause_extractions2 = extract_clauses(document_text2)

    df1 = pd.DataFrame(list(clause_extractions1.items()), columns=['Clause Name', 'First Document'])
    df2 = pd.DataFrame(list(clause_extractions2.items()), columns=['Clause Name', 'Second Document'])

    combined_df = pd.merge(df1, df2, on='Clause Name', how='inner')
    print(combined_df)

    return combined_df

# import plotly.express as px
# import plotly.graph_objects as go
#
# fig = go.Figure(data=[go.Table(
#     header=dict(values=list(combined_df.columns), align='left'),
#     cells=dict(values=[combined_df[col] for col in combined_df.columns], align='left'))
# ])
#
# fig.show()