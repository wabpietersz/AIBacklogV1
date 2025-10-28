import base64
import os
from typing import Dict, Iterable, List

import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from openai import AzureOpenAI

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

client = AzureOpenAI(
    api_key=AOAI_KEY,
    api_version="2024-10-01-preview",
    azure_endpoint=AOAI_ENDPOINT,
)
search = SearchClient(
    AZSEARCH_ENDPOINT,
    AZSEARCH_INDEX,
    AzureKeyCredential(AZSEARCH_API_KEY),
)


def _b64_basic(email: str, token: str) -> str:
    auth = f"{email}:{token}".encode()
    return base64.b64encode(auth).decode()


def fetch_jira_issues(jql: str, fields: Iterable[str], max_results: int = 100):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    start_at = 0
    headers = {
        "Authorization": f"Basic {_b64_basic(JIRA_EMAIL, JIRA_API_TOKEN)}",
        "Accept": "application/json",
    }
    while True:
        params = {
            "jql": jql,
            "fields": ",".join(fields),
            "startAt": start_at,
            "maxResults": max_results,
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        issues = data.get("issues", [])
        for issue in issues:
            yield issue

        start_at += len(issues)
        if start_at >= data.get("total", 0):
            break


def flatten(issue: Dict) -> Dict:
    fields = issue["fields"]
    key = issue["key"]
    project = fields["project"]["key"]
    summary = fields.get("summary") or ""
    description = fields.get("description") or ""
    status = (fields.get("status") or {}).get("name") or ""
    labels = fields.get("labels") or []
    components = [c["name"] for c in fields.get("components") or []]
    created = fields.get("created")
    updated = fields.get("updated")
    url = f"{JIRA_BASE_URL}/browse/{key}"

    parts = [
        f"Summary: {summary}",
        f"Description: {description}",
        f"Labels: {', '.join(labels)}",
        f"Components: {', '.join(components)}",
    ]
    text = "\n".join([part for part in parts if part])

    return {
        "id": key,
        "key": key,
        "project": project,
        "status": status,
        "issuetype": (fields.get("issuetype") or {}).get("name") or "",
        "priority": (fields.get("priority") or {}).get("name") or "",
        "summary": summary,
        "description": description,
        "labels": labels,
        "components": components,
        "created": created,
        "updated": updated,
        "web_url": url,
        "text_for_embedding": text,
    }


def embed(texts: List[str]) -> List[List[float]]:
    response = client.embeddings.create(input=texts, model=EMBED_DEPLOY)
    return [item.embedding for item in response.data]


def upsert_batch(documents: List[Dict], chunk_size: int = 16) -> None:
    for start in range(0, len(documents), chunk_size):
        search.upload_documents(documents=documents[start : start + chunk_size])


def main() -> None:
    jql = "project in (GCSAI, AIBACKLOG) ORDER BY updated DESC"
    fields = [
        "summary",
        "description",
        "status",
        "project",
        "issuetype",
        "priority",
        "labels",
        "components",
        "created",
        "updated",
    ]
    prepared = [flatten(issue) for issue in fetch_jira_issues(jql, fields)]

    if not prepared:
        print("No issues fetched.")
        return

    vectors = embed([item["text_for_embedding"] for item in prepared])
    for document, vector in zip(prepared, vectors):
        document["text_vector"] = vector

    upsert_batch(prepared)
    print(f"Upserted {len(prepared)} issues into {AZSEARCH_INDEX}")


if __name__ == "__main__":
    main()
