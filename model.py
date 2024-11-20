# # from safetensors import torch
# import torch
# from transformers import AutoModelForSequenceClassification, AutoTokenizer
#
# model_path = 'mymodel'
#
# all_class_names = ['Affiliate License-Licensee', 'Affiliate License-Licensor',
#                    'Agreement Date', 'Anti-assignment', 'Audit Rights',
#                    'Cap on Liability', 'Change of Control',
#                    'Competitive Restriction Exception', 'Covenant not to Sue',
#                    'Document Name', 'Effective Date', 'Exclusivity',
#                    'Expiration Date', 'Governing Law', 'IP Ownership Assignment',
#                    'Insurance', 'Irrevocable or Perpetual License',
#                    'Joint IP Ownership', 'License Grant', 'Liquidated Damages',
#                    'Minimum Commitment', 'Most Favored Nation',
#                    'No-Solicit of Customers', 'Non-Compete',
#                    'Non-Disparagement', 'Non-Transferable License',
#                    'Notice Period to Terminate Renewal',
#                    'Notice Period to Terminate Renewal- Answer', 'Parties',
#                    'Post-termination Services', 'Price Restrictions',
#                    'ROFR-ROFO-ROFN', 'Renewal Term', 'Revenue-Profit Sharing',
#                    'Source Code Escrow', 'Termination for Convenience',
#                    'Third Party Beneficiary', 'Uncapped Liability',
#                    'Unlimited/All-You-Can-Eat License', 'Volume Restriction',
#                    'Warranty Duration']
# def extract_clauses(paragraph):
#   model = AutoModelForSequenceClassification.from_pretrained(model_path)
#   tokenizer = AutoTokenizer.from_pretrained("nlpaueb/bert-base-uncased-contracts")
#
#   # Tokenize the input text
#   inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, padding=True)
#
#   # Make predictions without gradient calculation
#   # Get predictions
#   with torch.no_grad():
#       outputs = model(**inputs)
#
#   # Extract logits and get the top 3 indices
#   logits = outputs.logits[0]
#   top_3_indices = torch.topk(logits, 3).indices.tolist()
#
#   # Map the indices to class names
#   top_3_classes = [(all_class_names[i], logits[i].item()) for i in top_3_indices]
#
#   return top_3_classes


import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import fitz  # PyMuPDF for PDF processing
import re
import os

model_path = 'mymodel'

all_class_names = [
    'Affiliate License-Licensee', 'Affiliate License-Licensor',
    'Agreement Date', 'Anti-assignment', 'Audit Rights',
    'Cap on Liability', 'Change of Control',
    'Competitive Restriction Exception', 'Covenant not to Sue',
    'Document Name', 'Effective Date', 'Exclusivity',
    'Expiration Date', 'Governing Law', 'IP Ownership Assignment',
    'Insurance', 'Irrevocable or Perpetual License',
    'Joint IP Ownership', 'License Grant', 'Liquidated Damages',
    'Minimum Commitment', 'Most Favored Nation',
    'No-Solicit of Customers', 'Non-Compete',
    'Non-Disparagement', 'Non-Transferable License',
    'Notice Period to Terminate Renewal',
    'Notice Period to Terminate Renewal- Answer', 'Parties',
    'Post-termination Services', 'Price Restrictions',
    'ROFR-ROFO-ROFN', 'Renewal Term', 'Revenue-Profit Sharing',
    'Source Code Escrow', 'Termination for Convenience',
    'Third Party Beneficiary', 'Uncapped Liability',
    'Unlimited/All-You-Can-Eat License', 'Volume Restriction',
    'Warranty Duration'
]

clause_risks = {
    "Affiliate License-Licensee": "This clause often permits affiliates to use the licensed materials, which could broaden the scope of who has access. Small businesses should be cautious as this could lead to unauthorized or unintended usage.",
    "Affiliate License-Licensor": "If licensors allow their affiliates to enforce or modify terms, it may increase potential restrictions. Small businesses should be mindful of how this affects their control over usage rights.",
    "Agreement Date": "Missing or ambiguous agreement dates can lead to confusion about contract validity or enforceability. Small business owners need clear dates to avoid any contractual disputes over timing.",
    "Anti-assignment": "Prevents a business from assigning contract benefits to another party, which can limit flexibility if the business is sold or restructured. Small businesses should ensure they retain the right to assign when needed.",
    "Audit Rights": "Allows the other party to inspect financial records or usage, which can be costly and intrusive. Small businesses should assess the extent of these rights and negotiate limitations if necessary.",
    "Cap on Liability": "Limits the amount one party can claim for damages, potentially restricting recourse in the event of major issues. Small businesses should check that the cap is reasonable and doesn’t leave them under-compensated.",
    "Change of Control": "Allows termination or renegotiation if a business changes ownership. Small businesses planning for growth or sale should ensure they won’t be unfairly penalized under these terms.",
    "Competitive Restriction Exception": "Limits the business’s ability to work with competitors, which can stifle growth and revenue opportunities. Small businesses should carefully evaluate if these restrictions are too burdensome.",
    "Covenant not to Sue": "Prevents legal action, which can be risky if the other party breaches the agreement. Small businesses need to retain their rights to pursue claims if terms aren’t honored.",
    "Document Name": "Ensures clarity on the official name of the agreement for legal referencing. Small businesses should confirm this is accurate to avoid confusion in legal contexts.",
    "Effective Date": "The date on which the contract terms begin to apply. Ambiguity here can lead to disputes about obligations. Clear dates help small businesses plan their obligations accurately.",
    "Exclusivity": "Can prevent the business from working with other partners, limiting growth. Small businesses should carefully consider if exclusivity is necessary and negotiate time limits if possible.",
    "Expiration Date": "Indicates when the contract ends, which is crucial for planning. Small businesses should clarify this to prevent unexpected renewals or abrupt terminations.",
    "Governing Law": "Specifies the legal jurisdiction, which can affect legal proceedings and costs. Small businesses should aim for local jurisdictions or ones with favorable laws.",
    "IP Ownership Assignment": "Transfers ownership of intellectual property, which can be a major loss of value. Small businesses should be cautious about giving up IP rights that are core to their brand or technology.",
    "Insurance": "Requires the business to maintain specific insurance, which can be costly. Small businesses should confirm they can afford and obtain the required coverage.",
    "Irrevocable or Perpetual License": "Allows indefinite use of a license, which may limit a business's future revenue opportunities. Small businesses should assess if this is necessary or negotiate time-limited terms.",
    "Joint IP Ownership": "Sharing IP ownership can complicate future decisions and restrict full control. Small businesses should consider if joint ownership aligns with their long-term goals.",
    "License Grant": "Defines the scope of permissions given, which can be broad or restrictive. Small businesses should ensure the license terms are clear and avoid granting overly broad rights.",
    "Liquidated Damages": "Predetermined damages in case of a breach, which can be financially burdensome. Small businesses should negotiate fair amounts to avoid excessive liabilities.",
    "Minimum Commitment": "Requires the business to purchase or commit to minimum levels, which can be a financial strain. Small businesses should avoid high minimums to maintain flexibility.",
    "Most Favored Nation": "Ensures one party receives the best terms, which can limit flexibility in future deals. Small businesses should consider if they can realistically offer this clause.",
    "No-Solicit of Customers": "Restricts the business from approaching certain customers, which could limit growth. Small businesses should clarify if the scope is too broad for their needs.",
    "Non-Compete": "Limits the ability to work in specific markets or with certain clients, potentially stifling growth. Small businesses should carefully consider the duration and geographic scope.",
    "Non-Disparagement": "Prevents speaking negatively about the other party, which could limit free speech or responses to public criticism. Small businesses should evaluate if this could restrict their responses in a dispute.",
    "Non-Transferable License": "Prevents transferring the license, which can limit flexibility if ownership changes. Small businesses should ensure this aligns with their long-term plans.",
    "Notice Period to Terminate Renewal": "Requires advance notice for termination, which can lead to automatic renewals if missed. Small businesses should ensure the notice period is manageable.",
    "Notice Period to Terminate Renewal- Answer": "Clarifies response expectations, helping avoid automatic renewals or penalties. Small businesses should confirm they can meet the specified timeframe.",
    "Parties": "Lists all contract participants, crucial for enforcing terms. Small businesses should confirm that only relevant entities are included to avoid unnecessary liabilities.",
    "Post-termination Services": "May require providing services after termination, which can be a financial or operational burden. Small businesses should clarify the extent of these services.",
    "Price Restrictions": "Sets limits on pricing, which can limit revenue potential. Small businesses should confirm they have enough flexibility in setting prices.",
    "ROFR-ROFO-ROFN": "Right of first refusal, offer, or negotiation, which may limit business options. Small businesses should evaluate if these rights align with future growth plans.",
    "Renewal Term": "Defines contract renewal conditions, which can lead to automatic renewals. Small businesses should ensure terms are clear and allow for easy termination if needed.",
    "Revenue-Profit Sharing": "Shares profits with the other party, which can reduce profitability. Small businesses should ensure these terms are fair and sustainable.",
    "Source Code Escrow": "Requires depositing source code in escrow, which can expose valuable IP. Small businesses should consider if this is necessary and negotiate strong protections.",
    "Termination for Convenience": "Allows the other party to end the contract at any time, which can disrupt business plans. Small businesses should negotiate fair notice periods or fees for early termination.",
    "Third Party Beneficiary": "Allows third parties to benefit from the contract, potentially increasing liability. Small businesses should limit this to reduce risk.",
    "Uncapped Liability": "Exposes the business to unlimited financial liability, which can be catastrophic. Small businesses should negotiate caps to prevent excessive exposure.",
    "Unlimited/All-You-Can-Eat License": "Gives broad, unlimited access, potentially undervaluing resources. Small businesses should ensure this type of license aligns with their revenue model.",
    "Volume Restriction": "Limits the quantity a business can sell or use, potentially hindering growth. Small businesses should ensure they have sufficient capacity to meet demand.",
    "Warranty Duration": "Defines the length of warranties, which can be costly if too long. Small businesses should ensure they can meet the warranty terms within reasonable costs."
}


def extract_clauses(paragraph):
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained("nlpaueb/bert-base-uncased-contracts")

    # Tokenize the input text
    inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, padding=True)

    # Make predictions without gradient calculation
    with torch.no_grad():
        outputs = model(**inputs)

    # Extract logits and get the top 3 indices
    logits = outputs.logits[0]
    top_3_indices = torch.topk(logits, 3).indices.tolist()

    # Map the indices to class names
    top_3_classes = [(all_class_names[i], logits[i].item()) for i in top_3_indices]

    return top_3_classes


def segment_text(text):
    # Simple segmentation by splitting paragraphs (can be adjusted as needed)
    segments = re.split(r'\n\s*\n', text.strip())
    return segments


# def process_pdf(pdf_path):
#     # Open the PDF
#     # doc = fitz.open(pdf_path)
#     doc = fitz.open(stream=pdf_path.read(), filetype="pdf")
#     results = []
#
#     for page_num in range(doc.page_count):
#         page = doc[page_num]
#         text = page.get_text("text")  # Extract text from the page
#
#         # Segment text into paragraphs or clauses
#         segments = segment_text(text)
#
#         # Process each segment
#         for segment in segments:
#             clause_predictions = extract_clauses(segment)
#
#             for clause_name, _ in clause_predictions:
#                 # Get the risk explanation for the predicted clause
#                 risk = clause_risks.get(clause_name, "No specific risk explanation available.")
#
#                 # Format the output as specified
#                 formatted_string = f"Clause: {clause_name}\nSegment: {segment}\nRisk: {risk}\n\n"
#                 results.append(formatted_string)
#
#     doc.close()
#     return results


import fitz  # PyMuPDF

def process_pdf(pdf_file):
    pdf_file.seek(0)
    # Open the PDF file using the file-like object directly
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    results = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")  # Extract text from the page

        # Segment text into paragraphs or clauses
        segments = segment_text(text)

        # Process each segment
        for segment in segments:
            clause_predictions = extract_clauses(segment)

            for clause_name, _ in clause_predictions:
                # Get the risk explanation for the predicted clause
                risk = clause_risks.get(clause_name, "No specific risk explanation available.")

                # Format the output as specified
                formatted_string = f"Clause: {clause_name}\nSegment: {segment}\nRisk: {risk}\n\n"
                results.append(formatted_string)

    doc.close()
    return results




# Example usage
# pdf_path = "C:/Users/mauma/Downloads/Contract 1.pdf"
# results = process_pdf(pdf_path)
#
# # Display results
# for result in results:
#     print(result)