from googleapiclient import discovery
from google.oauth2 import service_account
import datetime
from collections import defaultdict
import json
import base64
import os

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly"
    ]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
SERVICE_KEY = json.loads(base64.b64decode(os.environ["FORMS_CREDENTIALS"]).decode('ascii'))


class Form:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_info(
            SERVICE_KEY, scopes=SCOPES
        )
        self.form_service = discovery.build("forms", "v1", credentials=self.creds)

    @staticmethod
    def make_hours_array(start_time, end_time):

        start_parts = start_time.split(":")
        end_parts = end_time.split(":")

        if int(start_parts[1]) == 0:
            first_hour = int(start_parts[0])
        else:
            first_hour = int(start_parts[0]) + 1

        last_hour = int(end_parts[0])

        return range(first_hour, last_hour + 1)
        

class FormWriter(Form):
    def __init__(self):
        super().__init__()

    @staticmethod
    def create_hours_entry(hour):
        return {
            "questionId": str(hour),
            "rowQuestion": {"title": f"{hour}:00"},
        }

    @staticmethod
    def create_days_entry(date_str):
        return {"value": date_str}

    def _create_form_json(self, form_info):

        hours = self.make_hours_array(
            form_info["time_of_day"][0],
            form_info["time_of_day"][1],
        )

        hr_arr = [self.create_hours_entry(h) for h in hours]
        day_arr = [self.create_days_entry(d) for d in form_info["dates"]]

        form_init = {
            "info": {
                "title": f"Planning for {form_info['name']}",
            },
        }

        question_json = {
            "requests": [
                {
                    "createItem": {
                        "item": {
                            "title": f"What times are you available for a {form_info['event_length']} hour event?",
                            "description": f"Times are in UTC{form_info['timezone']}",
                            "questionGroupItem": {
                                "questions": hr_arr,
                                "grid": {
                                    "columns": {"type": "CHECKBOX", "options": day_arr}
                                },
                            },
                        },
                        "location": {"index": 0},
                    }
                }
            ]
        }

        return form_init, question_json

    def create_form(self, form_info):

        # Creates the initial form
        form_init, question_json = self._create_form_json(form_info)
        form = self.form_service.forms().create(body=form_init).execute()

        # Adds the question to the form
        self.form_service.forms().batchUpdate(
            formId=form["formId"], body=question_json
        ).execute()

        return form["formId"], form["responderUri"]

class FormReader(Form):
    def __init__(self, form_id):
        super().__init__()
        self.form_id = form_id

    def read_form(self):
        self.form_results = self.form_service.forms().responses().list(formId=self.form_id).execute()
        if 'responses' in self.form_results:
            self.parsed_results = [self._parse_response(response) for response in self.form_results["responses"]]
            self.ordered_reponders = [response['responseId'] for response in self.form_results["responses"]]
        else:
            self.parsed_results = None
            self.ordered_reponders = None
 
    def _parse_response(self, response):
        response_dict = defaultdict(list)
        for tm, answer in response["answers"].items():
            for date in answer["textAnswers"]["answers"]:
                response_dict[date['value']].append(int(tm))                
        return response_dict

def build_availability(parsed_results, start_time, end_time):

    availability = defaultdict(lambda: 0)

    start_times = Form.make_hours_array(start_time, end_time)

    n_total_responses = len(parsed_results)
    
    for s in start_times: # all starts
        for res in parsed_results: # each response
            for date, times in res.items(): # available date/time
                if s in times:
                    availability[(date, s)] += 1

    max_key = max(availability, key=availability.get)
    max_value = availability[max_key]

    return max_key, max_value, n_total_responses