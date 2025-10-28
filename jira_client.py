"""
JIRA API Client
Handles communication with JIRA REST API
"""
import requests
import json
from typing import List, Dict, Optional
from config import Config

class JIRAClient:
    """JIRA API client for fetching issues"""
    
    def __init__(self, access_token: str):
        self.server_url = Config.JIRA_SERVER_URL
        self.access_token = access_token
        self.cloud_id = Config.JIRA_CLOUD_ID
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_issues(self, project_key: str, issue_type: str, max_results: int = 1000) -> List[Dict]:
        """Fetch all issues from a JIRA project using Atlassian Cloud API"""
        url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/3/search/jql"
        
        # Build JQL query based on whether issue_type is specified
        if issue_type and issue_type.strip():
            jql = f"project = {project_key} AND issuetype = {issue_type} ORDER BY created DESC"
        else:
            jql = f"project = {project_key} ORDER BY created DESC"
        
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary",
                "description",
                "status",
                "assignee",
                "reporter",
                "priority",
                "created",
                "updated"
            ]
        }
        
        all_issues = []
        start_at = 0
        
        while True:
            if start_at > 0:
                payload['startAt'] = start_at
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            if not issues:
                break
            
            all_issues.extend(issues)
            start_at += len(issues)
            
            if len(issues) < payload['maxResults']:
                break
        
        return all_issues
    
    def get_issue_details(self, issue_key: str) -> Dict:
        """Get detailed information about a specific issue"""
        url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/3/issue/{issue_key}"
        
        params = {
            'fields': 'id,key,summary,description,status,created,updated,assignee,reporter,labels,components,priority'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def search_issues(self, jql: str, max_results: int = 100) -> List[Dict]:
        """Search issues using JQL with Atlassian Cloud API"""
        url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/3/search/jql"
        
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary",
                "description",
                "status",
                "assignee",
                "reporter",
                "priority",
                "created",
                "updated"
            ]
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get('issues', [])
