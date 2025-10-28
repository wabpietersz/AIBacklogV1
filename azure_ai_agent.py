"""
Azure AI Foundry Agent
Main agent class that orchestrates the duplicate detection process
"""
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from typing import List, Dict
import json
from config import Config
from jira_auth import JIRAAuth
from jira_client import JIRAClient
from similarity_detector import SimilarityDetector

class AzureAIAgent:
    """Main Azure AI Foundry agent for duplicate detection"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Initialize Azure AI client
        self.azure_client = AzureOpenAI(
            azure_endpoint=self.config.AZURE_AI_FOUNDRY_ENDPOINT,
            api_key=self.config.AZURE_AI_FOUNDRY_API_KEY,
            api_version="2025-01-01-preview"
        )
        
        # Initialize components
        self.jira_auth = JIRAAuth()
        self.similarity_detector = SimilarityDetector()
        self.jira_client = None  # Will be initialized after authentication
    
    def authenticate_jira(self) -> bool:
        """Authenticate with JIRA using OAuth 2.0 with persistent tokens"""
        try:
            print("Authenticating with JIRA...")

            # Try to get valid tokens first (saved or refreshed)
            tokens = self.jira_auth.get_valid_tokens()

            if not tokens:
                # If no valid tokens, do interactive authentication
                print("No valid tokens found, starting interactive authentication...")
                tokens = self.jira_auth.authenticate_interactive()

            # Initialize JIRA client with access token
            self.jira_client = JIRAClient(tokens['access_token'])

            print("JIRA authentication successful!")
            print("✅ Tokens will be automatically refreshed when needed")
            return True

        except Exception as e:
            print(f"JIRA authentication failed: {e}")
            return False
    
    def fetch_issues(self) -> List[Dict]:
        """Fetch all issues from the Backlog project"""
        if not self.jira_client:
            raise ValueError("JIRA client not initialized. Please authenticate first.")
        
        print(f"Fetching issues from project '{self.config.JIRA_PROJECT_KEY}'...")
        issues = self.jira_client.get_issues(
            project_key=self.config.JIRA_PROJECT_KEY,
            issue_type=self.config.ISSUE_TYPE
        )
        
        print(f"Found {len(issues)} issues")
        return issues
    
    def analyze_duplicates(self, issues: List[Dict]) -> Dict:
        """Analyze issues for duplicates using AI"""
        print("Analyzing issues for duplicates...")
        
        # Find similar issues using embeddings
        similar_groups = self.similarity_detector.find_similar_issues(issues)
        
        # Use Azure AI to generate insights about the duplicates
        insights = self._generate_duplicate_insights(similar_groups)
        
        return {
            'similar_groups': similar_groups,
            'insights': insights,
            'total_issues_analyzed': len(issues),
            'duplicate_groups_found': len(similar_groups)
        }
    
    def _generate_duplicate_insights(self, similar_groups: Dict) -> str:
        """Generate AI-powered insights about duplicate issues"""
        if not similar_groups:
            return "No duplicate issues found."
        
        # Prepare context for AI analysis
        context = "Duplicate Issue Analysis:\n\n"
        
        for group_id, group_data in similar_groups.items():
            context += f"Group {group_id}:\n"
            for issue in group_data['issues']:
                summary = issue.get('fields', {}).get('summary', 'N/A')
                key = issue.get('key', 'N/A')
                context += f"  - {key}: {summary}\n"
            context += f"  Similarity Score: {group_data['avg_similarity']:.3f}\n\n"
        
        # Generate insights using Azure AI
        try:
            response = self.azure_client.chat.completions.create(
                model=self.config.AZURE_AI_FOUNDRY_DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert JIRA administrator analyzing duplicate issues. Provide insights about the duplicate groups found, including recommendations for consolidation and potential root causes."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return "AI insights generation failed."
    
    def generate_report(self, analysis_results: Dict) -> str:
        """Generate a comprehensive report"""
        # Count groups by similarity level
        high_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'High'}
        medium_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'Medium'}
        low_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'Low'}
        
        report = f"""
# JIRA Similarity Analysis Report

## Summary
- **Total Issues Analyzed**: {analysis_results['total_issues_analyzed']}
- **High Similarity Groups (≥80% - Likely Duplicates)**: {len(high_groups)}
- **Medium Similarity Groups (50-79% - Potential Duplicates)**: {len(medium_groups)}
- **Low Similarity Groups (30-49% - Related Issues)**: {len(low_groups)}
- **Total Similarity Groups**: {analysis_results['duplicate_groups_found']}

## All Story Issues Analyzed

### Individual Issue Details

"""
        
        # Add detailed information for all issues
        all_issues = []
        for group_data in analysis_results['similar_groups'].values():
            all_issues.extend(group_data['issues'])
        
        for i, issue in enumerate(all_issues, 1):
            key = issue.get('key', 'N/A')
            fields = issue.get('fields', {}) or {}
            summary = fields.get('summary', 'N/A')
            description = fields.get('description', 'N/A')
            status = fields.get('status', {}) or {}
            status_name = status.get('name', 'N/A') if status else 'N/A'
            assignee = fields.get('assignee', {}) or {}
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
            reporter = fields.get('reporter', {}) or {}
            reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'
            priority = fields.get('priority', {}) or {}
            priority_name = priority.get('name', 'N/A') if priority else 'N/A'
            created = fields.get('created', 'N/A')
            updated = fields.get('updated', 'N/A')
            jira_link = f"https://warren-pietersz.atlassian.net/browse/{key}"
            
            report += f"#### {i}. {key}\n"
            report += f"**Summary:** {summary}\n\n"
            report += f"**Description:**\n{description}\n\n"
            report += f"**Status:** {status_name}  \n"
            report += f"**Priority:** {priority_name}  \n"
            report += f"**Assignee:** {assignee_name}  \n"
            report += f"**Reporter:** {reporter_name}  \n"
            report += f"**Created:** {created}  \n"
            report += f"**Updated:** {updated}  \n"
            report += f"**JIRA Link:** [{jira_link}]({jira_link})\n\n"
            report += "---\n\n"

        report += "## Similarity Groups\n\n"
        
        # Group by similarity level
        high_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'High'}
        medium_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'Medium'}
        low_groups = {k: v for k, v in analysis_results['similar_groups'].items() if v.get('similarity_level') == 'Low'}
        
        # High Similarity Groups (Likely Duplicates)
        if high_groups:
            report += "### 🔥 High Similarity Groups (≥80% - Likely Duplicates)\n\n"
            for group_id, group_data in high_groups.items():
                avg_percent = group_data['avg_similarity'] * 100
                report += f"#### {group_id} (Average Similarity: {avg_percent:.1f}%)\n"
                report += "| JIRA Key | Summary | Status | Assignee | JIRA Link |\n"
                report += "|----------|---------|--------|----------|----------|\n"
                
                for issue in group_data['issues']:
                    key = issue.get('key', 'N/A')
                    fields = issue.get('fields', {}) or {}
                    summary = fields.get('summary', 'N/A')
                    status = fields.get('status', {}) or {}
                    status_name = status.get('name', 'N/A') if status else 'N/A'
                    assignee = fields.get('assignee', {}) or {}
                    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                    jira_link = f"{self.config.JIRA_SERVER_URL}/browse/{key}"
                    report += f"| {key} | {summary} | {status_name} | {assignee_name} | [View]({jira_link}) |\n"
                
                report += "\n"
        
        # Medium Similarity Groups (Potential Duplicates)
        if medium_groups:
            report += "### 🟡 Medium Similarity Groups (50-79% - Potential Duplicates)\n\n"
            for group_id, group_data in medium_groups.items():
                avg_percent = group_data['avg_similarity'] * 100
                report += f"#### {group_id} (Average Similarity: {avg_percent:.1f}%)\n"
                report += "| JIRA Key | Summary | Status | Assignee | JIRA Link |\n"
                report += "|----------|---------|--------|----------|----------|\n"
                
                for issue in group_data['issues']:
                    key = issue.get('key', 'N/A')
                    fields = issue.get('fields', {}) or {}
                    summary = fields.get('summary', 'N/A')
                    status = fields.get('status', {}) or {}
                    status_name = status.get('name', 'N/A') if status else 'N/A'
                    assignee = fields.get('assignee', {}) or {}
                    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                    jira_link = f"{self.config.JIRA_SERVER_URL}/browse/{key}"
                    report += f"| {key} | {summary} | {status_name} | {assignee_name} | [View]({jira_link}) |\n"
                
                report += "\n"
        
        # Low Similarity Groups (Related Issues)
        if low_groups:
            report += "### 🟠 Low Similarity Groups (30-49% - Related Issues)\n\n"
            for group_id, group_data in low_groups.items():
                avg_percent = group_data['avg_similarity'] * 100
                report += f"#### {group_id} (Average Similarity: {avg_percent:.1f}%)\n"
                report += "| JIRA Key | Summary | Status | Assignee | JIRA Link |\n"
                report += "|----------|---------|--------|----------|----------|\n"
                
                for issue in group_data['issues']:
                    key = issue.get('key', 'N/A')
                    fields = issue.get('fields', {}) or {}
                    summary = fields.get('summary', 'N/A')
                    status = fields.get('status', {}) or {}
                    status_name = status.get('name', 'N/A') if status else 'N/A'
                    assignee = fields.get('assignee', {}) or {}
                    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                    jira_link = f"{self.config.JIRA_SERVER_URL}/browse/{key}"
                    report += f"| {key} | {summary} | {status_name} | {assignee_name} | [View]({jira_link}) |\n"
                
                report += "\n"
        
        # Add AI insights
        insights = analysis_results.get('insights', 'No AI insights available.')
        report += f"## AI Analysis\n\n{insights}\n"
        
        return report
    
    def run_analysis(self) -> Dict:
        """Run the complete duplicate detection analysis"""
        print("Starting JIRA Duplicate Detection Analysis...")
        
        # Authenticate with JIRA
        if not self.authenticate_jira():
            return {"error": "JIRA authentication failed"}
        
        # Fetch issues
        try:
            issues = self.fetch_issues()
        except Exception as e:
            return {"error": f"Failed to fetch issues: {e}"}
        
        # Analyze for duplicates
        try:
            analysis_results = self.analyze_duplicates(issues)
        except Exception as e:
            return {"error": f"Failed to analyze duplicates: {e}"}
        
        # Generate report
        try:
            report = self.generate_report(analysis_results)
        except Exception as e:
            return {"error": f"Failed to generate report: {e}"}
        
        return {
            "success": True,
            "analysis_results": analysis_results,
            "report": report
        }
