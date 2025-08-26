# import requests
# import dotenv
# import os

# url = "https://api.primeintellect.ai/api/v1/availability/"
# dotenv.load_dotenv("..")
# prime_api_key = os.getenv("PRIME_API_KEY")
# print(prime_api_key)
# headers = {
#     "Authorization": f"Bearer {prime_api_key}"
# }

# res = requests.get(url, headers=headers)
# if res.status_code != 200:
#     print("Failed to access PI")
# else:
#     data = res.json()
#     print(data)


"""
export every secret in the shell while docker start, load it from env vars
"""
import os

import aiohttp

class PrimeIntellectClient:
    def __init__(self):
        self.__base_url = "https://api.primeintellect.ai/api/v1/pods/"
        self.__api_key = os.environ['PRIME_API_KEY']


    async def create_pod(self):
        """Create pod and load Mlflow models from S3"""
        # 1. Pool: Reuses connections instead of creating new ones each time
        # 2. Context manager: Automatically closes connections
        async with aiohttp.ClientSession() as session:
            payload = {

            }

            headers = {
                "Authorization": f"Bearer {self.__api_key}",
                "Content-Type": "application/json"
            }
            
            

        

    