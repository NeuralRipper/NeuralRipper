"""
TODO:
Use MlflowClient to get experiment and run object.
For fastapi, define BaseModel schema for experiment and run, etc, so fastapi knows how to serialize the object into JSON.
in handler, use client get the results, then use basemodel to extract the content and return the basemodel object instead.
"""
from mlflow import MlflowClient

# connect to DB Backend Stores
client = MlflowClient(tracking_uri="http://localhost:3306")


all_exp = client.search_experiments()
print(all_exp)

for e in all_exp:
    pass
