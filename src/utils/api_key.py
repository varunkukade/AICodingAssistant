import os
import getpass


# Function to get API keys from the user
def get_api_key(env_var: str, prompt: str) -> None:
    if not os.environ.get(env_var):
        os.environ[env_var] = getpass.getpass(prompt)
