import requests
import os
import csv
import base64
import sys
from PyPDF2 import PdfReader

def log_message(message):
    print(f"[LOG] {message}")

def pdf_to_csv(pdf_path, csv_path):
    log_message(f"Converting PDF at {pdf_path} to CSV at {csv_path}")
    try:
        reader = PdfReader(pdf_path)
        csv_data = []

        for page in reader.pages:
            text = page.extract_text().splitlines()
            csv_data.append(text)

        with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for row in csv_data:
                writer.writerow(row)
        log_message(f"CSV conversion completed successfully at {csv_path}")
    except Exception as e:
        log_message(f"Error during PDF to CSV conversion: {str(e)}")
        raise

def get_file_sha(repo, path, token):
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    return None

def upload_to_github(csv_file, repo, branch, token):
    file_path = f"csv-folder/{os.path.basename(csv_file)}"
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    log_message(f"Uploading CSV to GitHub at {api_url}")
    
    try:
        with open(csv_file, 'rb') as file:
            content = file.read()

        encoded_content = base64.b64encode(content).decode('utf-8')
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        sha = get_file_sha(repo, file_path, token)
        
        data = {
            "message": "Adding or updating converted CSV file",
            "content": encoded_content,
            "branch": branch
        }
        
        if sha:
            data["sha"] = sha

        response = requests.put(api_url, headers=headers, json=data)
        log_message(f"Response status code: {response.status_code}")
        log_message(f"Response content: {response.text}")
        response.raise_for_status()
        log_message(f"CSV uploaded successfully to GitHub with status code {response.status_code}")
        return response.status_code
    except Exception as e:
        log_message(f"Error during GitHub upload: {str(e)}")
        raise

def main(pdf_path, repo, branch, token):
    log_message(f"Main function called with pdf_path: {pdf_path}, repo: {repo}, branch: {branch}")
    if not pdf_path:
        log_message("Error: PDF path is empty")
        return

    file_name = os.path.basename(pdf_path)
    csv_path = os.path.join("csv-folder", file_name.replace(".pdf", ".csv"))

    try:
        pdf_to_csv(pdf_path, csv_path)
        status_code = upload_to_github(csv_path, repo, branch, token)
        log_message(f"Process completed successfully with status code {status_code}")
    except Exception as e:
        log_message(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        log_message("Usage: python pdf_to_csv.py <pdf_path> <repo> <branch> <token>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3]
    token = sys.argv[4]

    main(pdf_path, repo, branch, token)
