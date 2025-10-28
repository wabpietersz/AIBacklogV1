"""
Similarity Detection Module
Uses Azure AI Foundry embeddings to find similar/duplicate issues
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Tuple
from config import Config
from openai import AzureOpenAI
import re
from difflib import SequenceMatcher

class SimilarityDetector:
    """Detects similar issues using Azure AI Foundry embeddings"""
    
    def __init__(self):
        self.config = Config()
        # Use tiered thresholds instead of single threshold
        self.high_threshold = 0.8
        self.medium_threshold = 0.5
        self.low_threshold = 0.3
        # Keep the old threshold for backward compatibility
        self.similarity_threshold = self.config.SIMILARITY_THRESHOLD
        
        # Initialize Azure AI client for embeddings
        self.azure_client = AzureOpenAI(
            azure_endpoint=self.config.AZURE_AI_FOUNDRY_ENDPOINT,
            api_key=self.config.AZURE_AI_FOUNDRY_API_KEY,
            api_version="2025-01-01-preview"
        )
        
        # Initialize TF-IDF vectorizer for text similarity
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            max_features=1000,
            lowercase=True
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Azure AI Foundry"""
        try:
            # Try embeddings first
            response = self.azure_client.embeddings.create(
                model=self.config.AZURE_AI_FOUNDRY_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embeddings not available, using text similarity: {e}")
            # Fallback to text-based similarity
            return self._text_to_vector(text)
    
    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to a simple vector representation for similarity"""
        import hashlib
        import re
        
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Create a simple vector based on word frequency and text characteristics
        vector = []
        
        # Add text length features
        vector.append(len(text) / 1000.0)  # Normalized length
        vector.append(len(words) / 100.0)  # Normalized word count
        
        # Add word frequency features (first 50 words)
        word_freq = {}
        for word in words[:50]:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Add frequency features to vector
        for i in range(50):
            if i < len(words):
                vector.append(word_freq.get(words[i], 0) / len(words))
            else:
                vector.append(0.0)
        
        # Add hash-based features for consistency
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        vector.append((hash_val % 1000) / 1000.0)
        
        # Pad or truncate to fixed size
        target_size = 100
        if len(vector) < target_size:
            vector.extend([0.0] * (target_size - len(vector)))
        else:
            vector = vector[:target_size]
        
        return vector

    def normalize_text(self, text: str) -> str:
        """Normalize text for better similarity detection"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common words that don't add meaning
        common_words = {'error', 'issue', 'bug', 'problem', 'fix', 'resolve'}
        words = text.split()
        words = [word for word in words if word not in common_words]
        
        # Stem similar words for better matching
        word_mapping = {
            'navigator': 'navigation',
            'navigate': 'navigation',
            'navigating': 'navigation',
            'designer': 'design',
            'designing': 'design',
            'manager': 'manage',
            'managing': 'manage',
            'configuration': 'config',
            'configure': 'config'
        }
        
        normalized_words = []
        for word in words:
            if word in word_mapping:
                normalized_words.append(word_mapping[word])
            else:
                normalized_words.append(word)
        
        return ' '.join(normalized_words).strip()

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using multiple methods"""
        if not text1 or not text2:
            return 0.0
        
        # Method 1: Sequence similarity (good for exact matches)
        seq_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Method 2: TF-IDF cosine similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            tfidf_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            tfidf_similarity = 0.0
        
        # Method 3: Word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        if words1 or words2:
            overlap_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            overlap_similarity = 0.0
        
        # Method 4: Character n-gram similarity
        def get_ngrams(text, n=3):
            return set(text[i:i+n] for i in range(len(text)-n+1))
        
        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)
        if ngrams1 or ngrams2:
            ngram_similarity = len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))
        else:
            ngram_similarity = 0.0
        
        # Weighted combination of all methods
        final_similarity = (
            0.3 * seq_similarity +
            0.3 * tfidf_similarity +
            0.2 * overlap_similarity +
            0.2 * ngram_similarity
        )
        
        return final_similarity

    def prepare_text_for_embedding(self, issue: Dict) -> str:
        """Prepare issue text for embedding by combining summary and description"""
        summary = issue.get('fields', {}).get('summary', '')
        description = issue.get('fields', {}).get('description', '')
        
        # Clean and combine text
        if description:
            # Remove HTML tags and clean description
            import re
            description = re.sub(r'<[^>]+>', '', str(description))
            description = description.strip()
        
        # Combine summary and description
        combined_text = f"{summary}"
        if description:
            combined_text += f" {description}"
        
        return combined_text.strip()
    
    def calculate_similarities(self, issues: List[Dict]) -> List[Tuple[int, int, float]]:
        """Calculate similarity scores between all pairs of issues"""
        print("Preparing text for embedding...")
        
        # Prepare texts and get embeddings
        texts = []
        valid_indices = []
        
        for i, issue in enumerate(issues):
            text = self.prepare_text_for_embedding(issue)
            if text:
                texts.append(text)
                valid_indices.append(i)
        
        print(f"Getting embeddings for {len(texts)} issues...")
        
        # Get embeddings
        embeddings = []
        for i, text in enumerate(texts):
            print(f"Processing issue {i+1}/{len(texts)}")
            embedding = self.get_embedding(text)
            if embedding:
                embeddings.append(embedding)
            else:
                # If embedding fails, add zero vector
                embeddings.append([0.0] * 1536)  # ada-002 has 1536 dimensions
        
        embeddings = np.array(embeddings)
        
        print("Calculating similarity matrix...")
        
        # Calculate cosine similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find similar pairs above threshold
        similar_pairs = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = similarity_matrix[i][j]
                if similarity >= self.similarity_threshold:
                    original_i = valid_indices[i]
                    original_j = valid_indices[j]
                    similar_pairs.append((original_i, original_j, similarity))
        
        # Sort by similarity score (highest first)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def find_similar_issues(self, issues: List[Dict]) -> Dict[str, Dict]:
        """Find similar issues using tiered similarity detection"""
        if not issues:
            return {}

        print(f"🔍 Analyzing {len(issues)} issues for similarity...")
        
        # Prepare texts for all issues using enhanced normalization
        issue_texts = []
        for issue in issues:
            summary = issue.get('fields', {}).get('summary', '')
            description = issue.get('fields', {}).get('description', '')
            
            # Focus primarily on summary, add description if available
            text = summary
            if description:
                # Clean description
                description = re.sub(r'<[^>]+>', '', str(description))
                description = description.strip()
                if description:
                    text += f" {description}"
            
            normalized_text = self.normalize_text(text)
            issue_texts.append(normalized_text)
            print(f"   {issue.get('key', 'N/A')}: '{normalized_text}'")

        # Calculate similarity matrix using enhanced text similarity
        n = len(issues)
        similarity_matrix = np.zeros((n, n))
        
        print("📊 Calculating similarity scores...")
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.calculate_text_similarity(issue_texts[i], issue_texts[j])
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity
                
                # Categorize similarity levels
                similarity_percent = similarity * 100
                if similarity >= self.high_threshold:
                    print(f"   🔥 High similarity: {issues[i].get('key', 'N/A')} ↔ {issues[j].get('key', 'N/A')} = {similarity_percent:.1f}%")
                elif similarity >= self.medium_threshold:
                    print(f"   🟡 Medium similarity: {issues[i].get('key', 'N/A')} ↔ {issues[j].get('key', 'N/A')} = {similarity_percent:.1f}%")
                elif similarity >= self.low_threshold:
                    print(f"   🟠 Low similarity: {issues[i].get('key', 'N/A')} ↔ {issues[j].get('key', 'N/A')} = {similarity_percent:.1f}%")

        # Group similar issues with tiered thresholds
        similar_groups = {}
        group_counter = 1

        # First pass: High similarity groups (>= 0.8)
        high_processed = set()
        for i in range(n):
            if i in high_processed:
                continue

            # Find all issues with high similarity to this one
            similar_indices = [i]
            for j in range(i + 1, n):
                if j not in high_processed and similarity_matrix[i][j] >= self.high_threshold:
                    similar_indices.append(j)
                    high_processed.add(j)

            # If we found high similarity issues, create a group
            if len(similar_indices) > 1:
                group_issues = [issues[idx] for idx in similar_indices]
                
                # Calculate average similarity for the group
                similarities = []
                for k in range(len(similar_indices)):
                    for l in range(k + 1, len(similar_indices)):
                        idx1, idx2 = similar_indices[k], similar_indices[l]
                        similarities.append(similarity_matrix[idx1][idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                
                similar_groups[f"high_similarity_group_{group_counter}"] = {
                    "issues": group_issues,
                    "avg_similarity": avg_similarity,
                    "similarity_level": "High",
                    "threshold_used": self.high_threshold
                }
                
                avg_percent = avg_similarity * 100
                print(f"✅ High Similarity Group {group_counter}: {len(group_issues)} issues (avg: {avg_percent:.1f}%)")
                for issue in group_issues:
                    print(f"     - {issue.get('key', 'N/A')}: {issue.get('fields', {}).get('summary', 'N/A')}")
                
                group_counter += 1

            # Only mark as processed if we created a group
            if len(similar_indices) > 1:
                high_processed.add(i)

        # Second pass: Medium similarity groups (0.5 - 0.8)
        medium_processed = set()
        for i in range(n):
            if i in medium_processed or i in high_processed:
                continue

            # Find all issues with medium similarity to this one
            similar_indices = [i]
            for j in range(i + 1, n):
                if j not in medium_processed and j not in high_processed and self.medium_threshold <= similarity_matrix[i][j] < self.high_threshold:
                    similar_indices.append(j)
                    medium_processed.add(j)

            # If we found medium similarity issues, create a group
            if len(similar_indices) > 1:
                group_issues = [issues[idx] for idx in similar_indices]
                
                # Calculate average similarity for the group
                similarities = []
                for k in range(len(similar_indices)):
                    for l in range(k + 1, len(similar_indices)):
                        idx1, idx2 = similar_indices[k], similar_indices[l]
                        similarities.append(similarity_matrix[idx1][idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                
                similar_groups[f"medium_similarity_group_{group_counter}"] = {
                    "issues": group_issues,
                    "avg_similarity": avg_similarity,
                    "similarity_level": "Medium",
                    "threshold_used": self.medium_threshold
                }
                
                avg_percent = avg_similarity * 100
                print(f"🟡 Medium Similarity Group {group_counter}: {len(group_issues)} issues (avg: {avg_percent:.1f}%)")
                for issue in group_issues:
                    print(f"     - {issue.get('key', 'N/A')}: {issue.get('fields', {}).get('summary', 'N/A')}")
                
                group_counter += 1

            # Only mark as processed if we created a group
            if len(similar_indices) > 1:
                medium_processed.add(i)

        # Third pass: Low similarity groups (0.3 - 0.5)
        low_processed = set()
        for i in range(n):
            if i in low_processed or i in medium_processed or i in high_processed:
                continue

            # Find all issues with low similarity to this one
            similar_indices = [i]
            for j in range(i + 1, n):
                if j not in low_processed and j not in medium_processed and j not in high_processed and self.low_threshold <= similarity_matrix[i][j] < self.medium_threshold:
                    similar_indices.append(j)
                    low_processed.add(j)

            # If we found low similarity issues, create a group
            if len(similar_indices) > 1:
                group_issues = [issues[idx] for idx in similar_indices]
                
                # Calculate average similarity for the group
                similarities = []
                for k in range(len(similar_indices)):
                    for l in range(k + 1, len(similar_indices)):
                        idx1, idx2 = similar_indices[k], similar_indices[l]
                        similarities.append(similarity_matrix[idx1][idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                
                similar_groups[f"low_similarity_group_{group_counter}"] = {
                    "issues": group_issues,
                    "avg_similarity": avg_similarity,
                    "similarity_level": "Low",
                    "threshold_used": self.low_threshold
                }
                
                avg_percent = avg_similarity * 100
                print(f"🟠 Low Similarity Group {group_counter}: {len(group_issues)} issues (avg: {avg_percent:.1f}%)")
                for issue in group_issues:
                    print(f"     - {issue.get('key', 'N/A')}: {issue.get('fields', {}).get('summary', 'N/A')}")
                
                group_counter += 1

            # Only mark as processed if we created a group
            if len(similar_indices) > 1:
                low_processed.add(i)

        return similar_groups
