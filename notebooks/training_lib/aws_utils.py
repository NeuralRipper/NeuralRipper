"""
AWS utilities for secret management.
Simple secret loading from AWS Secrets Manager.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AWSSecretManager:
    """Simple AWS Secrets Manager client with caching."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.region_name = region_name
        self._client = None
        self._secrets_cache = {}
    
    @property
    def client(self):
        """Lazy initialization of boto3 client."""
        if self._client is None:
            self._client = boto3.client('secretsmanager', region_name=self.region_name)
        return self._client
    
    def get_secret(self, secret_name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get secret from AWS Secrets Manager with caching."""
        logger.info(f"Loading secret: {secret_name} (region: {self.region_name})")
        
        if not force_refresh and secret_name in self._secrets_cache:
            logger.info(f"Secret {secret_name} found in cache")
            return self._secrets_cache[secret_name]
        
        try:
            logger.info(f"Calling AWS Secrets Manager for: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_dict = json.loads(response['SecretString'])
            self._secrets_cache[secret_name] = secret_dict
            logger.info(f"Successfully loaded secret {secret_name} with {len(secret_dict)} keys")
            return secret_dict
        except Exception as e:
            logger.error(f"Failed to load secret {secret_name}: {e}")
            return None
    
    def get_secret_value(self, secret_name: str, key: str, default: Any = None) -> Any:
        """Get specific value from a secret."""
        secret = self.get_secret(secret_name)
        return secret.get(key, default) if secret else default

def get_neuralripper_secrets() -> Optional[Dict[str, Any]]:
    """Get neuralripper secrets from AWS Secrets Manager."""
    return _secret_manager.get_secret('neuralripper')


def get_mlflow_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get MLflow username and password from secrets."""
    logger.info("🔐 Getting MLflow credentials...")
    secrets = get_neuralripper_secrets()
    if not secrets:
        logger.warning("No neuralripper secrets available")
        return None, None
    
    username = secrets.get('MLFLOW_SERVER_USERNAME')
    password = secrets.get('MLFLOW_SERVER_PASSWORD')
    
    logger.info(f"🔐 MLflow credentials: username={'✅' if username else '❌'}, password={'✅' if password else '❌'}")
    return username, password


def build_mlflow_uri(base_url: str = "https://neuralripper.com/mlflow/") -> str:
    """Build MLflow URI with credentials from AWS Secrets Manager."""
    logger.info(f"🌐 Building MLflow URI from base: {base_url}")
    username, password = get_mlflow_credentials()
    
    if username and password and base_url.startswith("https://"):
        # Insert credentials: https://username:password@domain/path
        domain_path = base_url[8:]  # Remove https://
        uri = f"https://{username}:{password}@{domain_path}"
        logger.info("MLflow URI built with credentials")
        return uri
    
    # Return base URL if no credentials or not HTTPS
    logger.warning("MLflow URI built WITHOUT credentials - using base URL")
    return base_url

# Global instance
_secret_manager = AWSSecretManager()