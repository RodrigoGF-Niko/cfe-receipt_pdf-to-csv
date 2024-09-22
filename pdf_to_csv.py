import requests
import os
import csv
import base64
from PyPDF2 import PdfReader

# Step 1: Function to download the PDF
def download_pdf(pdf_url, download_path):
    response = requests.get(pdf_url)
    with open(download_path, 'wb') as file:
        file.write(response.content)
    return download_path

# Step 2: Convert the PDF into a CSV
def pdf_to_csv(pdf_path, csv_path):
    reader = PdfReader(pdf_path)
    csv_data = []

    for page in reader.pages:
        text = page.extract_text().splitlines()
        csv_data.append(text)

    # Write the extracted data to a CSV
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in csv_data:
            writer.writerow(row)

# Step 3: Upload the CSV back to GitHub using GitHub API
def upload_to_github(csv_file, repo, branch, token):
    api_url = f"https://api.github.com/repos/{repo}/contents/{os.path.basename(csv_file)}"
    with open(csv_file, 'rb') as file:
        content = file.read()

    encoded_content = base64.b64encode(content).decode('utf-8')
    
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }

    data = {
        "message": "Adding converted CSV file",
        "content": encoded_content,
        "branch": branch
    }

    response = requests.put(api_url, headers=headers, json=data)
    return response.status_code

# Step 4: Main function
def main(pdf_url, repo, branch, token):
    # Dynamic filename from URL
    file_name = os.path.basename(pdf_url)
    pdf_path = f"/tmp/{file_name}"
    csv_path = pdf_path.replace(".pdf", ".csv")

    # Download and convert the PDF
    download_pdf(pdf_url, pdf_path)
    pdf_to_csv(pdf_path, csv_path)

    # Upload the CSV to GitHub
    status_code = upload_to_github(csv_path, repo, branch, token)
    return status_code

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python pdf_to_csv.py <pdf_url> <repo> <branch> <token>")
        sys.exit(1)

    pdf_url = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3]
    token = sys.argv[4]

    main(pdf_url, repo, branch, token)
