from googleapiclient import discovery
from google.oauth2 import service_account
import datetime

SCOPES = ["https://www.googleapis.com/auth/forms.body"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
SERVICE_KEY = "../SECRETS/lordran-2f175b91e5ec.json"


class FormWriter:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_KEY, scopes=SCOPES
        )
        self.form_service = discovery.build("forms", "v1", credentials=self.creds)

    @staticmethod
    def make_hours_array(start_time, end_time, event_length):

        start_parts = start_time.split(":")
        end_parts = end_time.split(":")

        if int(start_parts[1]) == 0:
            first_hour = int(start_parts[0])
        else:
            first_hour = int(start_parts[0]) + 1

        latest_feasible_start = datetime.timedelta(hours = int(end_parts[0]), minutes = int(end_parts[1])) - datetime.timedelta(hours=event_length)

        last_hour = latest_feasible_start.seconds // 3600 # WHY

        return range(first_hour, last_hour + 1)

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
            form_info["event_length"],
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
                            "title": "Time doe",
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
