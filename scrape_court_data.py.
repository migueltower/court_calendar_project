import requests
from bs4 import BeautifulSoup
from pyairtable import Table

# Define the URL of the website
URL = 'https://superiorcourt.maricopa.gov/calendar/today/' # Replace with the URL of the court calendar page

# Make the request and parse the page
response = requests.get (URL)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all table rows with court information (excluding header row)
table_rows = soup.find_all('tr')[1:]

# Airtable configuration with Personal Access Token
AIRTABLE_ACCESS_TOKEN = 'patWNcr7ifBkQ6sld'  # Replace with your personal access token
AIRTABLE_BASE_ID = 'appqvyaQYtdZfJOBa'
AIRTABLE_TABLE_ID = 'tblZxwC90ozs1D00l'  # Ensure there is no leading space here

# Airtable configuration with Personal Access Token
AIRTABLE_ACCESS_TOKEN = 'patWNcr7ifBkQ6sld'  # Replace with your personal access token
AIRTABLE_BASE_ID = 'appqvyaQYtdZfJOBa'
AIRTABLE_TABLE_ID = 'tblZxwC90ozs1D00l'  # Ensure there is no leading space here

# URL of the court calendar page
URL = 'https://superiorcourt.maricopa.gov/calendar/today/'

# Make the request to get the page content
response = requests.get(URL)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the rows in the court calendar table
rows = soup.find_all('tr')

# Parse relevant data from each row
data = []
for row in rows[1:]:  # Skipping the header row
    cols = row.find_all('td')
    if len(cols) >= 6:
        name = cols[0].text.strip()
        building = cols[1].text.strip()
        time = cols[4].text.strip()
        case_number = cols[5].text.strip()
        
        # Only process case numbers starting with 'CR'
        if case_number.startswith("CR"):
            data.append({
                'Name': name,
                'Building': building,
                'Time': time,
                'Case Number': case_number
            })

# Function to send data to Airtable
def send_to_airtable(data):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_ACCESS_TOKEN}',  # Use Personal Access Token here
        'Content-Type': 'application/json'
    }
    
    for record in data:
        fields = {
            'Name': record['Name'],
            'Building': record['Building'],
            'Time': record['Time'],
            'Case Number': record['Case Number']
        }
        
        response = requests.post(url, headers=headers, data=json.dumps({'fields': fields}))
        if response.status_code == 201:
            print(f"Successfully added {record['Name']} to Airtable")
        else:
            print(f"Failed to add {record['Name']} to Airtable: {response.text}")

# Send the data to Airtable
send_to_airtable(data)
