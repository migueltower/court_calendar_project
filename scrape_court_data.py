
import os
import re
import requests
import pprint as pp
import logging
from datetime import datetime, date
from bs4 import BeautifulSoup
from pyairtable import Api, Table

# Setting today's date as a  basic variable
TODAY = datetime.today()

# Setting up a logger to log errors 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG (or another level)

#Let's log to the console
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

def access_api():
    # creating a variable called api_key which accesses the personal token i've saved to my environment
    api_key = os.environ['KEY']
    # connect to api
    api = Api(api_key)
    # table variable uses the table class from pyairtable to access the Maricopa County Homicides table
    # in the homicides base
    table = api.table('TK', 'TK')
    return table

def get_records(table):
    # getting all records from the 'everything' view of the table and collecting just the ID and Case # fields
    # This comes in the form of a list of RecorDicts, dictionaries with multiple dictionaries contained within
    records = table.all(view = 'viwKYJ9lIvDKK67rN', fields= ['ID','Case #'])
    for record in records:
        id_value = record.pop('id')
        # Add 'id' to the 'fields' dictionary
        record['fields']['id'] = id_value

    return records

def scrape_records(records):
    # extracting just the fields dictionary within the RecorDict response 
    list_of_fields = [record_dict['fields'] for record_dict in records]

    # We only care about the people who have both an ID and a case # 
    # So this line of code filters for only the fields dictionaries that have both
    list_of_fields_filtered = [i for i in list_of_fields if 'ID' in i and 'Case #' in i]

    # Step 2: hit every link in the list that is pulled
    list_of_links = []

    # for each person 
    for record in list_of_fields_filtered:
        trial_dates = []
        sentencing_dates = []
        # get the link from the case number field 
        link = record.get('Case #', '')
        # regex pattern to find a link inside parens
        regex_pattern = "\((.*?)\)"
        match = re.search(regex_pattern, link)
        # if you find a link inside parens 
        if match:
            # collect that link
            link = match.group(1)
            # check to see if the link is in the list of links 
            if link in list_of_links:
                record['Co-defendant'] = 'yes'
            # append the link to the list of links 
            list_of_links.append(link)
            # make the link a new item in our dict 
            record['Link'] = link
            try:
                # get the link 
                response = requests.get(link)
                # save the content of the response as a variable called response
                html = response.content
                # make the long string of html useful by parsing it with bs4 
                soup = BeautifulSoup(html, features="html.parser")
                # find the table w id 'tblForms4' — this is where the calendar information is saved 
                table = soup.find(id='tblForms4')
                # collect the rows from that table with the 'row g-0' class -- these rows are where
                # the calendar information is stored 
                rows = table.find_all('div', class_='row g-0')

                # for each row in rows 
                for row in rows:
                    # if program finds a div with the 'col-6 col-lg-2' class inside the row 
                    # (so as to avoid the headers)
                    if row.find('div', class_='col-6 col-lg-2'):
                        # the date is always the first div, so find and save 
                        date = row.find('div', class_='col-6 col-lg-2')
                        # strip the html bullshit from the date and just save it as a date 
                        date_text = date.get_text(strip=True)
                        # This is the date format that we're working with : m or mm/ d or dd/ yyyy
                        date_format = "%m/%d/%Y"
                        # parse the date 
                        date_clean = datetime.strptime(date_text, date_format) 
                        # the event is in a div separate from the others, a div that has a class of 'col-6 col-lg-8', 
                        # so grab that 
                        event = row.find('div', class_='col-6 col-lg-8')
                        # strip the html bullshit from the event and save it 
                        event_clean = event.get_text(strip=True)
                        # put the event and the date in a little list of their own
                        # If the event is a trial or a sentencing  
                        if event_clean in ["Trial"]:
                            trial_lst = [event_clean, date_clean]
                            trial_dates.append(trial_lst)
                        elif event_clean in ["Sentencing"]:
                            sentencing_lst = [event_clean, date_clean]
                            sentencing_dates.append(sentencing_lst)

                    else:
                        pass
            except Exception as e:
                logger.exception("No page found: %s", e)

        else:
            logger.info("no hyperlink")


        future_trials = [date for date in trial_dates if date[1] >= TODAY]
        future_sentences = [date for date in sentencing_dates if date[1] >= TODAY]
        if future_trials:
            closest_trial = min(future_trials, key=lambda x: x[1])
            record['Trial Date'] = closest_trial[1].strftime("%Y-%m-%d")
            #print(record)
        else:
            logger.info("No trial dates forward in time")
        if future_sentences:
            closest_sentence = min(future_sentences, key=lambda x: x[1])
            record['Sentencing Date']= closest_sentence[1].strftime("%Y-%m-%d")
            #print(record)
        else:
            logger.info("No sentencing dates forward in time")

    return list_of_fields_filtered

def write_to_airtable():
    table = access_api()
    records = get_records(table)
    records_final = scrape_records(records)
    for record in records_final:
        if 'Trial Date' in record and 'Sentencing Date' in record:
            id = record['id']
            trial_date = record['Trial Date']
            sentencing_date = record['Sentencing Date']
            if trial_date > sentencing_date:
                fields = {'Trial Date': record['Trial Date'], 'Sentencing Date': record['Sentencing Date'], 'Flag Trial': 'yes'}
            else:
                fields = {'Trial Date': record['Trial Date'], 'Sentencing Date': record['Sentencing Date']}
            table.update(id, fields) 
        elif 'Trial Date' in record:
            id = record['id']
            fields = {'Trial Date': record['Trial Date']}
            table.update(id, fields) 
        elif 'Sentencing Date' in record:
            id = record['id']
            fields = {'Sentencing Date': record['Sentencing Date']}
            table.update(id,fields)
        if 'Co-defendant' in record:
            id = record['id']
            fields = {'Co-defendant': 'yes'}
            table.update(id,fields)

# here, we're making it so if we want to pull functions from this 
# script into other scripts -- essentially, if we want to treat this script as a MODULE
# it won't execute the below code chunk.
# 
if __name__ == "__main__":
    write_to_airtable()



