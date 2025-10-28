import os
import re
from typing import Dict, List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

AZSEARCH_ENDPOINT = os.getenv("AZSEARCH_ENDPOINT")
AZSEARCH_API_KEY = os.getenv("AZSEARCH_API_KEY")
AZSEARCH_INDEX = os.getenv("AZSEARCH_INDEX")

AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

search = SearchClient(
    AZSEARCH_ENDPOINT,
    AZSEARCH_INDEX,
    AzureKeyCredential(AZSEARCH_API_KEY),
)
aoai = AzureOpenAI(
    api_key=AOAI_KEY,
    api_version="2024-10-01-preview",
    azure_endpoint=AOAI_ENDPOINT,
)


def extract_key(value: str) -> str | None:
    match = re.search(r"([A-Z][A-Z0-9]+-\d+)", value)
    return match.group(1) if match else None


def get_issue(issue_key: str) -> Dict | None:
    result = search.search(
        search_text=None,
        filter=f"key eq '{issue_key}'",
        top=1,
    )
    for item in result:
        return item
    return None


def embed(text: str) -> List[float]:
    return aoai.embeddings.create(input=text, model=EMBED_DEPLOY).data[0].embedding


def similar_in_same_project(issue_key: str, top_k: int = 5) -> List[Dict]:
    document = get_issue(issue_key)
    if not document:
        return []

    project = document["project"]
    query_vector = embed(document["text_for_embedding"])
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="text_vector",
    )

    results = search.search(
        search_text=document.get("summary"),
        vector_queries=[vector_query],
        filter=f"project eq '{project}' and key ne '{issue_key}'",
        top=top_k,
        query_type="semantic",
        semantic_configuration_name="sem1",
    )

    items: List[Dict] = []
    for result in results:
        items.append(
            {
                "key": result.get("key"),
                "status": result.get("status"),
                "summary": result.get("summary"),
                "web_url": result.get("web_url"),
                "score": result.get("@search.score"),
            }
        )
    return items


def main() -> None:
    value = input("Paste JIRA link or key: ").strip()
    issue_key = extract_key(value) or value

    matches = similar_in_same_project(issue_key)
    if not matches:
        print("No strong matches in this project.")
        return

    print(f"Similar to {issue_key}:")
    for match in matches:
        summary = (match["summary"] or "")[:100]
        print(
            f"- {match['key']} — {match.get('status', '')} — {summary}…  {match.get('web_url', '')}"
        )


if __name__ == "__main__":
    main()
