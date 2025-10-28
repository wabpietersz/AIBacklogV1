import os
import math
import time
import base64
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

AZSEARCH_ENDPOINT = os.getenv("AZSEARCH_ENDPOINT")
AZSEARCH_API_KEY = os.getenv("AZSEARCH_API_KEY")
AZSEARCH_INDEX = os.getenv("AZSEARCH_INDEX")

AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

client = AzureOpenAI(api_key=AOAI_KEY, api_version="2024-10-01-preview", azure_endpoint=AOAI_ENDPOINT)
search = SearchClient(AZSEARCH_ENDPOINT, AZSEARCH_INDEX, AzureKeyCredential(AZSEARCH_API_KEY))


def b64_basic(email, token):
    return base64.b64encode(f"{email}:{token}".encode()).decode()


def fetch_jira_issues(jql, fields, max_results=100):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    start_at = 0
    headers = {
        "Authorization": f"Basic {b64_basic(JIRA_EMAIL, JIRA_API_TOKEN)}",
        "Accept": "application/json"
    }
    while True:
        params = {
            "jql": jql,
            "fields": ",".join(fields),
            "startAt": start_at,
            "maxResults": max_results
        }
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        for issue in data.get("issues", []):
            yield issue
        start_at += len(data.get("issues", []))
        if start_at >= data.get("total", 0):
            break


def flatten(issue):
    f = issue["fields"]
    key = issue["key"]
    project = f["project"]["key"]
    summary = f.get("summary") or ""
    description = (f.get("description") or "")
    status = (f.get("status") or {}).get("name") or ""
    labels = f.get("labels") or []
    components = [c["name"] for c in f.get("components") or []]
    created = f.get("created")
    updated = f.get("updated")
    url = f"{JIRA_BASE_URL}/browse/{key}"

    # Make a compact chunk for embedding
    parts = [
        f"Summary: {summary}",
        f"Description: {description}",
        f"Labels: {', '.join(labels)}",
        f"Components: {', '.join(components)}"
    ]
    text = "\n".join([p for p in parts if p and p != ""])

    return {
        "id": key,
        "key": key,
        "project": project,
        "status": status,
        "issuetype": (f.get('issuetype') or {}).get('name') or "",
        "priority": (f.get('priority') or {}).get('name') or "",
        "summary": summary,
        "description": description,
        "labels": labels,
        "components": components,
        "created": created,
        "updated": updated,
        "web_url": url,
        "text_for_embedding": text
    }


def embed(texts):
    # Azure OpenAI embeddings (batch for throughput if you like)
    resp = client.embeddings.create(input=texts, model=EMBED_DEPLOY)
    return [d.embedding for d in resp.data]


def upsert_batch(docs):
    # Add vectors then push
    CHUNK = 16
    for i in range(0, len(docs), CHUNK):
        search.upload_documents(documents=docs[i:i+CHUNK])


def main():
    # Example JQL: adjust projects and time window for incremental loads
    jql = "project in (GCSAI, AIBACKLOG) ORDER BY updated DESC"
    fields = [
        "summary","description","status","project","issuetype","priority",
        "labels","components","created","updated"
    ]
    prepared = []
    for issue in fetch_jira_issues(jql, fields):
        doc = flatten(issue)
        prepared.append(doc)

    if not prepared:
        print("No issues fetched.")
        return

    # Create embeddings
    vecs = embed([d["text_for_embedding"] for d in prepared])
    for d, v in zip(prepared, vecs):
        d["text_vector"] = v

    upsert_batch(prepared)
    print(f"Upserted {len(prepared)} issues into {AZSEARCH_INDEX}")


if __name__ == "__main__":
    main()
