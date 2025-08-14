import json
import boto3

class SecretManager:
    def __init__(self, secret_name="neuralripper", region_name="us-west-2"):
        self.secret_name = secret_name
        self.region_name = region_name
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self):
        res = self.client.get_secret_value(SecretId=self.secret_name)
        return json.loads(res['SecretString'])

_shared_secret_manager = None

def get_secret_manager():
    global _shared_secret_manager
    if not _shared_secret_manager:
        _shared_secret_manager = SecretManager()
    return _shared_secret_manager

if __name__ == "__main__":
    manager = get_secret_manager()
    secrets = manager.get_secret()
    for k, v in secrets.items():
        print(k, v)