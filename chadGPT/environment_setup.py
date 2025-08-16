import logging
import os

logger = logging.getLogger(__name__)


def read_secrets_into_environment() -> None:
        env_file = os.path.join(os.path.dirname(__file__), '..', 'secrets.txt')
        logger.debug(f"Reading secrets from {env_file}")
        if os.path.exists(env_file):
            logger.debug(f"Secrets file {env_file} exists. Loading into environment variables.")
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip():
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                        logger.debug(f"Set environment variable {key} to {'*'*len(value)}")
        else:
            logger.debug(f"Secrets file {env_file} does not exist.")

        return None

read_secrets_into_environment()
is_environment_ready = os.getenv('OPENAI_API_KEY') is not None
if not is_environment_ready:
    logger.warning("Environment not properly set up. Please ensure all required environment variables are set.")