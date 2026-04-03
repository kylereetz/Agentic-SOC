import os
from dotenv import load_dotenv

# Load the .env variables so that encryption keys are available for tests
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
