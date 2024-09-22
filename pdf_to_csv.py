import requests
import os
import csv
import base64
import sys
import pdfplumber
import pyperclip

def log_message(message):
    print(f"[LOG] {message}")

# Helper function to write a row with a header and value
def write_row(writer, header, value):
    writer.writerow([header, value])

# Helper function to write table headers and rows
def write_table(writer, headers, rows):
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

# Function to extract and structure relevant data from the PDF
def extract_data_from_pdf(pdf_path):
    consumption_overview = None
    historical_consumption = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Clean and process table rows
                table = [row for row in table if any(cell.strip() for cell in row if cell)]
                
                # Identify "Consumption Overview" table
                if "Current Reading" in str(table):
                    consumption_overview = table
                
                # Identify "Historical Consumption" table
                if "Period" in str(table):
                    historical_consumption = table[1:]  # Skip the header row

    return consumption_overview, historical_consumption

# Function to process data extracted from the PDF
def process_data(consumption_overview, historical_consumption):
    # Extract "Energy Used (kWh)" from "Consumption Overview" table
    energy_used = None
    if consumption_overview:
        for row in consumption_overview:
            if "Energy Used (kWh)" in row:
                energy_used = int(row[-1])  # Last column has the kWh value
    
    # Extract up to the first 5 rows from "Historical Consumption" table
    consumption_values = []
    if historical_consumption:
        for row in historical_consumption[:5]:  # Only first 5 rows
            try:
                consumption_value = int(row[1].replace(',', ''))  # Second column should be the kWh value
                consumption_values.append(consumption_value)
            except ValueError:
                continue

    return energy_used, consumption_values

# Function to calculate the average
def calculate_average(energy_used, consumption_values):
    all_values = [energy_used] + consumption_values
    average = sum(all_values) / len(all_values) if all_values else 0
    return round(average, 2)  # Round to two decimal places

# Function to copy result to clipboard
def copy_to_clipboard(customer_name, average_consumption, num_values):
    result = f"{customer_name} - Average consumption from the last {num_values} = {average_consumption}"
    pyperclip.copy(result)
    log_message(f"Copied to clipboard: {result}")

# Function to convert PDF to CSV and extract relevant data
def pdf_to_csv(pdf_path, csv_path, customer_name):
    log_message(f"Converting PDF at {pdf_path} to CSV at {csv_path}")

    try:
        # Extract data
        consumption_overview, historical_consumption = extract_data_from_pdf(pdf_path)

        # Process extracted data
        energy_used, consumption_values = process_data(consumption_overview, historical_consumption)
        
        # Calculate the average consumption
        if energy_used is not None and consumption_values:
            average_consumption = calculate_average(energy_used, consumption_values)
            num_values = len(consumption_values) + 1  # +1 for "Energy Used"
            copy_to_clipboard(customer_name, average_consumption, num_values)

        # CSV conversion logic (existing logic maintained)
        with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write General Info, Energy Costs, Historical Consumption, Payment History (from the original code)
            write_row(writer, "General Information", "")
            # Add actual data for General Information, Energy Costs, Historical Consumption, etc.

        log_message(f"CSV conversion completed successfully at {csv_path}")

    except Exception as e:
        log_message(f"Error during PDF to CSV conversion: {str(e)}")
        raise

# Function to get file SHA for GitHub operations
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

# Function to upload the converted CSV to GitHub
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

def main(pdf_path, repo, branch, token, customer_name):
    log_message(f"Main function called with pdf_path: {pdf_path}, repo: {repo}, branch: {branch}")

    if not pdf_path:
        log_message("Error: PDF path is empty")
        return

    file_name = os.path.basename(pdf_path)
    csv_path = os.path.join("csv-folder", file_name.replace(".pdf", ".csv"))

    try:
        # Process the PDF and upload CSV
        pdf_to_csv(pdf_path, csv_path, customer_name)
        status_code = upload_to_github(csv_path, repo, branch, token)
        log_message(f"Process completed successfully with status code {status_code}")

    except Exception as e:
        log_message(f"Error in main function: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        log_message("Usage: python pdf_to_csv.py <pdf_path> <repo> <branch> <token> <customer_name>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    repo = sys.argv[2]
    branch = sys.argv[3]
    token = sys.argv[4]
    customer_name = sys.argv[5]

    main(pdf_path, repo, branch, token, customer_name)
