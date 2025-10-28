#!/usr/bin/env python3
"""
Test Mode JIRA Agent
This runs the agent in test mode without requiring real JIRA authentication.
"""

import json
import datetime
from similarity_detector import SimilarityDetector
from openai import AzureOpenAI
from config import Config

class TestModeJIRAClient:
    """Mock JIRA client for testing without authentication"""
    
    def __init__(self):
        self.sample_issues = [
            {
                "key": "KAN-1",
                "fields": {
                    "summary": "Fix login bug in user authentication",
                    "description": "Users are unable to log in due to authentication error. The login form is not validating credentials properly.",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "John Doe"},
                    "reporter": {"displayName": "Jane Smith"},
                    "created": "2024-01-15T10:30:00.000+0000",
                    "updated": "2024-01-16T14:20:00.000+0000"
                }
            },
            {
                "key": "KAN-2",
                "fields": {
                    "summary": "Resolve authentication issue for login",
                    "description": "Login functionality is broken and needs to be fixed. Users cannot access their accounts.",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Bob Wilson"},
                    "reporter": {"displayName": "Alice Johnson"},
                    "created": "2024-01-14T09:15:00.000+0000",
                    "updated": "2024-01-14T09:15:00.000+0000"
                }
            },
            {
                "key": "KAN-3",
                "fields": {
                    "summary": "Add new feature for user dashboard",
                    "description": "Create a new dashboard for users to view their data and analytics.",
                    "status": {"name": "Done"},
                    "assignee": {"displayName": "Sarah Davis"},
                    "reporter": {"displayName": "Mike Brown"},
                    "created": "2024-01-10T11:00:00.000+0000",
                    "updated": "2024-01-12T16:45:00.000+0000"
                }
            },
            {
                "key": "KAN-4",
                "fields": {
                    "summary": "Fix user login authentication problem",
                    "description": "The user login system has authentication issues that prevent users from accessing their accounts.",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "John Doe"},
                    "reporter": {"displayName": "Jane Smith"},
                    "created": "2024-01-13T08:30:00.000+0000",
                    "updated": "2024-01-15T12:10:00.000+0000"
                }
            },
            {
                "key": "KAN-5",
                "fields": {
                    "summary": "Implement user profile management",
                    "description": "Add functionality for users to manage their profiles and settings.",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Tom Wilson"},
                    "reporter": {"displayName": "Lisa Green"},
                    "created": "2024-01-11T14:20:00.000+0000",
                    "updated": "2024-01-11T14:20:00.000+0000"
                }
            }
        ]
    
    def get_issues(self, project_key: str, issue_type: str, max_results: int = 1000):
        """Return sample issues for testing"""
        print(f"📋 Using sample data for testing (project: {project_key}, type: {issue_type})")
        return self.sample_issues[:max_results]

class TestModeAgent:
    """Test mode agent that doesn't require JIRA authentication"""
    
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
        self.jira_client = TestModeJIRAClient()
        self.similarity_detector = SimilarityDetector()
    
    def run(self):
        """Run the agent in test mode"""
        print("=" * 60)
        print("JIRA Duplicate Detection Agent - TEST MODE".center(60))
        print("=" * 60)
        print("🧪 Running in test mode with sample data")
        print("✅ No JIRA authentication required")
        print("✅ Using sample issues for demonstration")
        
        # Fetch sample issues
        print("\n📋 Fetching sample issues...")
        issues = self.jira_client.get_issues('KAN', 'Story')
        print(f"✅ Found {len(issues)} sample issues")
        
        # Analyze for duplicates
        print("\n🧠 Analyzing issues for similarity...")
        similar_groups = self.similarity_detector.find_similar_issues(issues)
        print(f"✅ Found {len(similar_groups)} groups of similar issues")
        
        # Generate AI insights
        print("\n🤖 Generating AI insights...")
        ai_insights = self.generate_ai_insights(similar_groups)
        
        # Generate report
        print("\n📊 Generating report...")
        self.generate_report(issues, similar_groups, ai_insights)
        
        print("\n🎉 Test mode analysis complete!")
        print("✅ Check the generated report files for results")
    
    def generate_ai_insights(self, similar_groups):
        """Generate AI insights for duplicate issues"""
        if not similar_groups:
            return "No similar issues found to generate insights."
        
        context = "The following groups of JIRA issues have been identified as similar:\n\n"
        for group_name, group_data in similar_groups.items():
            context += f"Group: {group_name}\n"
            for issue in group_data['issues']:
                key = issue.get('key', 'N/A')
                summary = issue.get('fields', {}).get('summary', 'N/A')
                context += f"  - {key}: {summary}\n"
            context += f"  Similarity Score: {group_data['avg_similarity']:.3f}\n\n"
        
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
            return "Could not generate AI insights due to an error."
    
    def generate_report(self, issues, similar_groups, ai_insights):
        """Generate a comprehensive report"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"test_mode_report_{timestamp}.md"
        json_filename = f"test_mode_results_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            f.write(f"# JIRA Duplicate Issue Analysis Report - TEST MODE\n\n")
            f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Mode:** Test Mode (Sample Data)\n")
            f.write(f"**Total Issues Analyzed:** {len(issues)}\n")
            f.write(f"**Issue Type:** Story\n")
            f.write(f"**Similarity Threshold:** {self.config.SIMILARITY_THRESHOLD}\n\n")
            
            # Add detailed issue information section
            f.write("## All Story Issues Analyzed\n\n")
            f.write("### Individual Issue Details\n\n")
            for i, issue in enumerate(issues, 1):
                key = issue.get('key', 'N/A')
                summary = issue.get('fields', {}).get('summary', 'N/A')
                description = issue.get('fields', {}).get('description', 'N/A')
                status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
                assignee = issue.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')
                reporter = issue.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown')
                created = issue.get('fields', {}).get('created', 'N/A')
                updated = issue.get('fields', {}).get('updated', 'N/A')
                
                # Create mock JIRA link
                jira_link = f"https://warren-pietersz.atlassian.net/browse/{key}"
                
                f.write(f"#### {i}. {key}\n")
                f.write(f"**Summary:** {summary}\n\n")
                f.write(f"**Description:**\n{description}\n\n")
                f.write(f"**Status:** {status}  \n")
                f.write(f"**Assignee:** {assignee}  \n")
                f.write(f"**Reporter:** {reporter}  \n")
                f.write(f"**Created:** {created}  \n")
                f.write(f"**Updated:** {updated}  \n")
                f.write(f"**JIRA Link:** [{jira_link}]({jira_link})\n\n")
                f.write("---\n\n")
            
            f.write("## Similar Issue Groups\n\n")
            if similar_groups:
                for group_name, group_data in similar_groups.items():
                    f.write(f"### {group_name} (Average Similarity: {group_data['avg_similarity']:.3f})\n")
                    f.write("| JIRA Key | Summary | Status | Assignee | JIRA Link |\n")
                    f.write("|----------|---------|--------|----------|----------|\n")
                    for issue in group_data['issues']:
                        key = issue.get('key', 'N/A')
                        summary = issue.get('fields', {}).get('summary', 'N/A')
                        status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
                        assignee = issue.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')
                        jira_link = f"https://warren-pietersz.atlassian.net/browse/{key}"
                        f.write(f"| {key} | {summary} | {status} | {assignee} | [View]({jira_link}) |\n")
                    f.write("\n")
                    
                    # Add detailed information for each issue in the group
                    f.write(f"#### Detailed Information for {group_name}\n\n")
                    for issue in group_data['issues']:
                        key = issue.get('key', 'N/A')
                        summary = issue.get('fields', {}).get('summary', 'N/A')
                        description = issue.get('fields', {}).get('description', 'N/A')
                        status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
                        assignee = issue.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')
                        reporter = issue.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown')
                        created = issue.get('fields', {}).get('created', 'N/A')
                        updated = issue.get('fields', {}).get('updated', 'N/A')
                        jira_link = f"https://warren-pietersz.atlassian.net/browse/{key}"
                        
                        f.write(f"**{key}:** {summary}\n")
                        f.write(f"- **Description:** {description}\n")
                        f.write(f"- **Status:** {status}\n")
                        f.write(f"- **Assignee:** {assignee}\n")
                        f.write(f"- **Reporter:** {reporter}\n")
                        f.write(f"- **Created:** {created}\n")
                        f.write(f"- **Updated:** {updated}\n")
                        f.write(f"- **Link:** [{jira_link}]({jira_link})\n\n")
            else:
                f.write("No similar issue groups found.\n\n")
            
            f.write("## AI Insights and Recommendations\n\n")
            f.write(ai_insights)
            f.write("\n")
        
        with open(json_filename, 'w') as f:
            json.dump({
                "mode": "test",
                "project_key": "KAN",
                "issue_type": "Story",
                "similarity_threshold": self.config.SIMILARITY_THRESHOLD,
                "total_issues_analyzed": len(issues),
                "similar_groups": similar_groups,
                "ai_insights": ai_insights
            }, f, indent=2)
        
        print(f"✅ Test report saved to: {report_filename}")
        print(f"✅ Test data saved to: {json_filename}")

if __name__ == "__main__":
    agent = TestModeAgent()
    agent.run()
