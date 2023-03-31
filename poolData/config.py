import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    def __init__(self):
        self.api_url = os.environ.get("API_URL")
        self.api_url_free = os.environ.get("API_URL_FREE")
    
    def get_api_url(self):
        return self.api_url
    
    def get_api_url_free(self):
        return self.api_url_free