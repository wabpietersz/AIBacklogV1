"""
Configuration management for the JIRA Duplicate Detection Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # Azure AI Foundry Configuration
    AZURE_AI_FOUNDRY_ENDPOINT = os.getenv('AZURE_AI_FOUNDRY_ENDPOINT')
    AZURE_AI_FOUNDRY_API_KEY = os.getenv('AZURE_AI_FOUNDRY_API_KEY')
    AZURE_AI_FOUNDRY_DEPLOYMENT_NAME = os.getenv('AZURE_AI_FOUNDRY_DEPLOYMENT_NAME', 'gpt-4')
    
    # JIRA Configuration
    JIRA_SERVER_URL = os.getenv('JIRA_SERVER_URL')
    JIRA_CLIENT_ID = os.getenv('JIRA_CLIENT_ID')
    JIRA_CLIENT_SECRET = os.getenv('JIRA_CLIENT_SECRET')
    JIRA_REDIRECT_URI = os.getenv('JIRA_REDIRECT_URI', 'http://localhost:8080/callback')
    JIRA_CLOUD_ID = os.getenv('JIRA_CLOUD_ID', '54734819-e768-4f8e-98b3-853acf0df524')
    
    # Azure AI Configuration (for embeddings)
    AZURE_AI_FOUNDRY_EMBEDDING_MODEL = os.getenv('AZURE_AI_FOUNDRY_EMBEDDING_MODEL', 'text-embedding-ada-002')
    
    # Project Configuration
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'Backlog')
    ISSUE_TYPE = os.getenv('ISSUE_TYPE', 'Story')
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.8'))
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'AZURE_AI_FOUNDRY_ENDPOINT',
            'AZURE_AI_FOUNDRY_API_KEY',
            'JIRA_SERVER_URL',
            'JIRA_CLIENT_ID',
            'JIRA_CLIENT_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
