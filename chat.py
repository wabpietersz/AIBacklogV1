import os, re
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

load_dotenv()

AZSEARCH_ENDPOINT = os.getenv("AZSEARCH_ENDPOINT")
AZSEARCH_API_KEY = os.getenv("AZSEARCH_API_KEY")
AZSEARCH_INDEX = os.getenv("AZSEARCH_INDEX")

AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

search = SearchClient(AZSEARCH_ENDPOINT, AZSEARCH_INDEX, AzureKeyCredential(AZSEARCH_API_KEY))
aoai = AzureOpenAI(api_key=AOAI_KEY, api_version="2024-10-01-preview", azure_endpoint=AOAI_ENDPOINT)


def extract_key(s: str) -> str | None:
    m = re.search(r"([A-Z][A-Z0-9]+-\d+)", s)
    return m.group(1) if m else None


def get_issue(key: str):
    r = search.search(search_text=None, filter=f"key eq '{key}'", top=1)
    for doc in r: return doc
    return None


def embed(text: str):
    return aoai.embeddings.create(input=text, model=EMBED_DEPLOY).data[0].embedding


def similar_in_same_project(issue_key: str, top_k=5):
    doc = get_issue(issue_key)
    if not doc:
        return []
    project = doc["project"]
    query_vec = embed(doc["text_for_embedding"])
    vq = VectorizedQuery(vector=query_vec, k_nearest_neighbors=top_k, fields="text_vector")

    # Hybrid (BM25 + Vector): include summary as search_text to help semantic ranker
    results = search.search(
        search_text=doc["summary"],
        vector_queries=[vq],
        filter=f"project eq '{project}' and key ne '{issue_key}'",
        top=top_k,
        query_type="semantic",
        semantic_configuration_name="sem1"
    )
    items = []
    for r in results:
        items.append({
            "key": r["key"],
            "status": r.get("status", ""),
            "summary": r.get("summary", ""),
            "web_url": r.get("web_url", ""),
            "score": r["@search.score"]
        })
    return items


if __name__ == "__main__":
    url = input("Paste JIRA link or key: ").strip()
    key = extract_key(url) or url
    sims = similar_in_same_project(key)
    if not sims:
        print("No strong matches in this project.")
    else:
        print(f"Similar to {key}:")
        for s in sims:
            print(f"- {s['key']} — {s['status']} — {s['summary'][:100]}…  {s['web_url']}")
