"""
Main entry point for the JIRA Duplicate Detection Agent
"""
import sys
import json
from datetime import datetime
from azure_ai_agent import AzureAIAgent

def main():
    """Main function to run the duplicate detection agent"""
    print("=" * 60)
    print("JIRA Duplicate Detection Agent")
    print("=" * 60)
    
    try:
        # Initialize the agent
        agent = AzureAIAgent()
        
        # Run the analysis
        results = agent.run_analysis()
        
        if results.get("error"):
            print(f"Error: {results['error']}")
            sys.exit(1)
        
        # Display results
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        
        analysis = results['analysis_results']
        print(f"Total Issues Analyzed: {analysis['total_issues_analyzed']}")
        print(f"Duplicate Groups Found: {analysis['duplicate_groups_found']}")
        
        if analysis['duplicate_groups_found'] > 0:
            print("\nDuplicate Groups:")
            for group_id, group_data in analysis['similar_groups'].items():
                print(f"\n{group_id}:")
                for issue in group_data['issues']:
                    summary = issue.get('fields', {}).get('summary', 'N/A')
                    key = issue.get('key', 'N/A')
                    print(f"  - {key}: {summary}")
                print(f"  Similarity: {group_data['avg_similarity']:.3f}")
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"duplicate_analysis_report_{timestamp}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(results['report'])
        
        print(f"\nDetailed report saved to: {report_filename}")
        
        # Save raw results as JSON
        json_filename = f"duplicate_analysis_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"Raw results saved to: {json_filename}")
        
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()




