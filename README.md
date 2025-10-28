# Jira Similarity Toolkit

This repo contains a minimal Python setup that does two things:

1. `ingest_jira.py` — pulls issues from Jira, builds Azure OpenAI embeddings, and upserts docs (with vectors) into Azure AI Search.
2. `chat.py` — given a pasted Jira link (or key), finds similar issues in the same project and shows their status.

---

## 1) Project layout

```
jira-similarity/
├─ .env                  # your secrets (see template below)
├─ requirements.txt
├─ index_schema.json     # Azure AI Search index definition
├─ ingest_jira.py        # one-time + incremental loader
└─ chat.py               # CLI chat demo (paste a JIRA URL)
```

---

## 2) `.env` (template)

```
# JIRA
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=atlassian_pat_token_here

# Azure AI Search
AZSEARCH_ENDPOINT=https://ais-gcsai-167-eastus.search.windows.net
AZSEARCH_API_KEY=search_admin_or_query_key
AZSEARCH_INDEX=idx-jira-issues

# Azure OpenAI / AI Foundry (Embeddings + Chat)
AZURE_OPENAI_ENDPOINT=https://aif-gcsai-167-eastus.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
```

> Store this file securely and never commit it.

---

## 3) `requirements.txt`

```
python-dotenv==1.0.1
requests==2.32.3
openai==1.47.0
azure-search-documents==11.6.0b4   # vector & hybrid support
```

---

## 4) `index_schema.json`

Upload once using REST (`curl`) or the Azure portal.

---

## 5) `ingest_jira.py`

Run to fetch Jira issues, embed them with Azure OpenAI, and upload to Azure AI Search.

```bash
python ingest_jira.py
```

Adjust the JQL for incremental loads (e.g., add `updated >= -1d`).

---

## 6) `chat.py`

Paste a Jira issue key or URL to find similar issues in the same project.

```bash
python chat.py
```

---

## 7) What changed vs. a Key Vault + portal plan

* Secrets live in `.env` (loaded with `python-dotenv`).
* Embeddings are created in Python (`openai` Azure client) instead of a Search skillset/vectorizer.
* Ingestion happens in a single script rather than via Data Factory/Logic Apps.
* Search still uses hybrid + vector + semantic queries through the SDK.
* You can extend this into FastAPI, Teams, etc., later.

---

## 8) First-run checklist

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Create the index: POST `index_schema.json` to `https://<search-name>.search.windows.net/indexes?api-version=2024-07-01`.
4. `python ingest_jira.py`
5. `python chat.py` → paste a Jira URL like `https://…/browse/GCSAI-167`.

---

## 9) Notes & tweaks

* `text-embedding-3-large` emits 3072-d vectors; update `index_schema.json` if you change models.
* Jira statuses come through as-is from your workflow.
* For incremental ingestion, keep a timestamp watermark and narrow the JQL window.
* `.env` is fine for dev; move to Key Vault/CI secrets when ready for team use.
* Both Azure AI Search and Azure OpenAI endpoints in the template point to East US—update for your region.
