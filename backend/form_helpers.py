from googleapiclient import discovery
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/forms.body"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
SERVICE_KEY = "../SECRETS/lordran-2f175b91e5ec.json"

class FormWriter():
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(SERVICE_KEY, scopes=SCOPES)
        self.form_service = discovery.build('forms', 'v1', credentials=self.creds)

    def _create_form_json(self, form_info):
        pass

    def create_form(self, form_info):
        #TKTK NOT FINISHED

        # Creates the initial form
        form_json = self._create_form_json(form_info)
        result = self.form_service.forms().create(body=form_json).execute()

        # Adds the question to the form
        # question_setting = self.form_service.forms().batchUpdate(formId=result["formId"], body=question_json).execute()

        # Prints the result to show the question has been added
        get_result = self.form_service.forms().get(formId=result["formId"]).execute()
        return get_result
        
        
