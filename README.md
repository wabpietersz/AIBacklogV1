# JIRA Duplicate Detection Agent

An intelligent Azure AI-powered agent that automatically detects similar and duplicate issues in JIRA projects using advanced tiered similarity analysis with percentage-based scoring.

## 🚀 Features

- **🔄 Automatic OAuth Flow**: Seamless authentication with automatic callback capture
- **🎯 Tiered Similarity Detection**: Three-level system (High ≥80%, Medium 50-79%, Low 30-49%)
- **📊 Percentage-Based Scoring**: Easy-to-understand similarity percentages
- **🧠 Multi-Algorithm AI**: Combines TF-IDF, sequence matching, word overlap, and n-gram analysis
- **🔍 Advanced Text Processing**: Intelligent normalization and word mapping (Navigator→Navigation)
- **🤖 Azure AI Integration**: Leverages Azure AI Foundry for enhanced analysis and insights
- **📋 Professional Reporting**: Comprehensive markdown reports with JIRA links
- **💾 Persistent Authentication**: Automatic token refresh for long-term use
- **🧪 Test Mode**: Development and demonstration with sample data

## 📋 Prerequisites

- Python 3.8+
- Azure AI Foundry account with API access
- JIRA Cloud account with OAuth 2.0 app
- Atlassian developer account

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Backlog-AiFoundry
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

## ⚙️ Configuration

### 1. Azure AI Foundry Setup

1. Create an Azure AI Foundry resource
2. Deploy a GPT-4 model (e.g., `gpt-4o`)
3. Get your endpoint, API key, and deployment name
4. Update `.env`:
   ```env
   AZURE_AI_FOUNDRY_ENDPOINT=https://your-resource.cognitiveservices.azure.com
   AZURE_AI_FOUNDRY_API_KEY=your_api_key
   AZURE_AI_FOUNDRY_DEPLOYMENT_NAME=gpt-4o
   AZURE_AI_FOUNDRY_EMBEDDING_MODEL=gpt-4o
   ```

### 2. JIRA OAuth Setup

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Create a new OAuth 2.0 app
3. **Set callback URL to**: `http://localhost:8080/callback`
4. Get your cloud ID from JIRA URL: `https://your-domain.atlassian.net`
5. Update `.env`:
   ```env
   JIRA_SERVER_URL=https://your-domain.atlassian.net
   JIRA_CLIENT_ID=your_client_id
   JIRA_CLIENT_SECRET=your_client_secret
   JIRA_CLOUD_ID=your_cloud_id
   JIRA_REDIRECT_URI=http://localhost:8080/callback
   JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
   ISSUE_TYPE=Story
   SIMILARITY_THRESHOLD=0.3
   ```

## 🚀 Usage

### Quick Start

1. **Run the agent** (automatic authentication):
   ```bash
   source venv/bin/activate
   python main.py
   ```

2. **Test mode** (no JIRA authentication required):
   ```bash
   source venv/bin/activate
   python test_mode_agent.py
   ```

### Authentication Flow

The application handles OAuth 2.0 authentication automatically:

1. **First Run**: Browser opens for authorization
2. **Automatic Callback**: Local server captures authorization code
3. **Token Storage**: Tokens saved for future use
4. **Subsequent Runs**: Automatic token refresh (no re-authentication needed)

## 📊 Tiered Similarity Analysis

### 🔥 High Similarity (≥80%) - Likely Duplicates
- **Action**: Immediate consolidation recommended
- **Example**: "Navigator error" ↔ "Navigation error" (100%)
- **Use Case**: Almost certainly the same issue

### 🟡 Medium Similarity (50-79%) - Potential Duplicates
- **Action**: Manual review for consolidation
- **Example**: Issues sharing significant concepts but different wording
- **Use Case**: May be duplicates requiring human judgment

### 🟠 Low Similarity (30-49%) - Related Issues
- **Action**: Consider for coordination or related work
- **Example**: Issues sharing common themes but likely different
- **Use Case**: Related work that might benefit from coordination

## 📊 Output

The agent generates:

1. **Markdown Report**: `duplicate_analysis_report_{timestamp}.md`
   - Executive summary with similarity tier counts
   - All issues analyzed with complete details
   - Tiered similarity groups with percentage scores
   - AI-powered insights and recommendations
   - Direct JIRA links for easy navigation

2. **JSON Data**: `duplicate_analysis_results_{timestamp}.json`
   - Raw analysis data
   - Similarity scores and metadata
   - Issue information for further processing

## 🔧 Configuration Options

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `SIMILARITY_THRESHOLD` | Base similarity threshold | 0.3 | 0.0-1.0 |
| `JIRA_PROJECT_KEY` | JIRA project to analyze | KAN | Any project key |
| `ISSUE_TYPE` | Type of issues to analyze | Story | Any issue type |
| `MAX_RESULTS` | Maximum issues to fetch | 1000 | 1-1000 |

## 🧠 How It Works

### 1. **Authentication Flow**
- Automatic OAuth 2.0 with local server callback capture
- Persistent token storage and refresh
- No manual intervention required after first setup

### 2. **Data Processing**
- Fetches issues using Atlassian Cloud API
- Combines summary and description fields
- Advanced text normalization and cleaning

### 3. **Similarity Analysis**
Multi-algorithm approach combining:
- **Sequence Matching** (30%): Exact text similarity
- **TF-IDF Cosine Similarity** (30%): Semantic similarity
- **Word Overlap** (20%): Vocabulary matching
- **N-gram Analysis** (20%): Partial text matching

### 4. **Intelligent Text Processing**
- Converts to lowercase and removes special characters
- Removes common words (error, issue, bug, problem)
- **Word Mapping**: navigator→navigation, designer→design, manager→manage, configuration→config
- Handles variations in terminology

### 5. **Tiered Grouping**
- Groups issues by similarity thresholds
- Prevents over-processing with smart indexing
- Creates separate groups for each similarity level

### 6. **AI-Powered Insights**
- Uses Azure AI Foundry for intelligent analysis
- Generates recommendations for each similarity group
- Provides actionable insights for board admins

## 📁 Project Structure

```
Backlog-AiFoundry/
├── main.py                    # 🚀 Main entry point
├── azure_ai_agent.py         # 🧠 Core orchestrator
├── jira_auth.py              # 🔐 OAuth authentication
├── jira_client.py            # 📡 JIRA API client
├── similarity_detector.py    # 🔍 AI similarity analysis
├── config.py                 # ⚙️ Configuration management
├── test_mode_agent.py        # 🧪 Test mode with sample data
├── requirements.txt          # 📦 Python dependencies
├── env.example              # 📋 Environment template
├── .gitignore               # 🚫 Git ignore rules
└── README.md                # 📚 This file
```

## 🔍 Example Output

```
# JIRA Similarity Analysis Report

## Summary
- **Total Issues Analyzed**: 5
- **High Similarity Groups (≥80% - Likely Duplicates)**: 1
- **Medium Similarity Groups (50-79% - Potential Duplicates)**: 0
- **Low Similarity Groups (30-49% - Related Issues)**: 1
- **Total Similarity Groups**: 2

## Similarity Groups

### 🔥 High Similarity Groups (≥80% - Likely Duplicates)

#### high_similarity_group_1 (Average Similarity: 100.0%)
| JIRA Key | Summary | Status | Assignee | JIRA Link |
|----------|---------|--------|----------|----------|
| KAN-1 | Navigator error | To Do | John Doe | [View](https://your-domain.atlassian.net/browse/KAN-1) |
| KAN-4 | Navigation error | To Do | Jane Smith | [View](https://your-domain.atlassian.net/browse/KAN-4) |

### 🟠 Low Similarity Groups (30-49% - Related Issues)

#### low_similarity_group_1 (Average Similarity: 33.4%)
| JIRA Key | Summary | Status | Assignee | JIRA Link |
|----------|---------|--------|----------|----------|
| KAN-2 | Page designer error | To Do | Bob Wilson | [View](https://your-domain.atlassian.net/browse/KAN-2) |
| KAN-3 | Configuration manager error | To Do | Alice Johnson | [View](https://your-domain.atlassian.net/browse/KAN-3) |

## AI Analysis
### Insights on Duplicate Group Found: `high_similarity_group_1`

**Duplicate Issues:**
- **KAN-4:** Navigation error
- **KAN-1:** Navigator error

**Analysis:**
These two issues are highly similar (100% match), indicating a likely duplicate. The core problem described in both is related to 'navigation' functionality, which our enhanced similarity detection has correctly identified as semantically equivalent.

**Recommendations for Consolidation:**
1. **Merge Issues:** Merge KAN-1 into KAN-4 to consolidate efforts
2. **Update Descriptions:** Ensure the merged issue captures all relevant information
3. **Communicate:** Inform reporters and assignees about the consolidation
4. **Close as Duplicate:** Close KAN-1 as a duplicate, linking it to KAN-4
```

## 🛡️ Security

- **OAuth 2.0**: Secure authentication with automatic token refresh
- **Local Token Storage**: Tokens stored in `jira_tokens.json` (excluded from git)
- **Environment Variables**: API keys stored securely in `.env` file
- **Automatic Cleanup**: Sensitive data excluded from version control
- **Timeout Protection**: 5-minute timeout for authentication flow

## 🧪 Testing

### Test Mode
Run with sample data without JIRA authentication:
```bash
python test_mode_agent.py
```

### Expected Test Results
- **5 sample issues** analyzed
- **1 low similarity group** detected (33.4% similarity)
- **Comprehensive report** generated
- **AI insights** provided

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Error**: 
   - Ensure callback URL is `http://localhost:8080/callback`
   - Check OAuth app configuration in Atlassian Developer Console

2. **API Connection Issues**:
   - Verify Azure AI Foundry endpoint and API key
   - Check JIRA server URL and cloud ID

3. **Similarity Detection Issues**:
   - Adjust `SIMILARITY_THRESHOLD` in `.env`
   - Check issue type and project key configuration

### Debug Mode
Enable verbose logging by setting environment variables:
```bash
export DEBUG=1
python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the generated logs and error messages
3. Open an issue on GitHub with detailed information
4. Include your configuration (without sensitive data)

## 🔄 Version History

- **v2.0.0**: Tiered similarity detection with percentage scoring
- **v1.5.0**: Automatic OAuth callback capture
- **v1.0.0**: Initial release with OAuth 2.0 and Azure AI integration
- Enhanced similarity detection with multi-algorithm approach
- Persistent authentication for long-term use
- Comprehensive reporting with AI insights

## 🎯 Key Improvements in v2.0.0

- **🎯 Tiered Analysis**: Three-level similarity system (High/Medium/Low)
- **📊 Percentage Display**: Easy-to-understand similarity scores
- **🔄 Automatic OAuth**: No manual code copying required
- **🧠 Enhanced AI**: Better text normalization and word mapping
- **📋 Professional Reports**: Improved formatting and structure
- **🧪 Test Mode**: Development and demonstration capabilities