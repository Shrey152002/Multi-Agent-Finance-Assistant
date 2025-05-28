# data_ingestion/embedding_service.py - FIXED VERSION
import numpy as np
from typing import List, Dict, Tuple
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
load_dotenv()

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.documents = []
        self.use_sentence_transformers = False
        
        # Try to use sentence-transformers with proper authentication
        try:
            from sentence_transformers import SentenceTransformer
            
            # Check for HuggingFace token
            hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
            
            if hf_token:
                # Set the token for authentication
                os.environ["HF_TOKEN"] = hf_token
                
            # Try to load the model
            self.model = SentenceTransformer(model_name, use_auth_token=hf_token)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # Try to load FAISS
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
            self.use_sentence_transformers = True
            print("✅ Using SentenceTransformers with FAISS")
            
        except Exception as e:
            print(f"⚠️ SentenceTransformers failed: {e}")
            print("🔄 Falling back to TF-IDF embeddings")
            
            # Fallback to TF-IDF
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.embeddings_matrix = None

    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """Generate embeddings for documents"""
        if self.use_sentence_transformers:
            embeddings = self.model.encode(documents, convert_to_tensor=False)
            return embeddings
        else:
            # Use TF-IDF fallback
            if self.embeddings_matrix is None:
                self.embeddings_matrix = self.vectorizer.fit_transform(documents)
            else:
                # Transform new documents
                new_embeddings = self.vectorizer.transform(documents)
                # Combine with existing embeddings
                from scipy.sparse import vstack
                self.embeddings_matrix = vstack([self.embeddings_matrix, new_embeddings])
            
            return self.embeddings_matrix.toarray()

    def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        """Add documents to the vector store"""
        if self.use_sentence_transformers:
            embeddings = self.embed_documents(documents)
            # Normalize embeddings for cosine similarity
            import faiss
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
        else:
            # For TF-IDF, just fit the vectorizer with all documents
            all_docs = [doc["content"] for doc in self.documents] + documents
            self.embeddings_matrix = self.vectorizer.fit_transform(all_docs)

        # Store documents and metadata
        for i, doc in enumerate(documents):
            doc_data = {
                "content": doc,
                "metadata": metadatas[i] if metadatas else {}
            }
            self.documents.append(doc_data)

    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for similar documents"""
        if len(self.documents) == 0:
            return []
            
        if self.use_sentence_transformers:
            query_embedding = self.model.encode([query])
            import faiss
            faiss.normalize_L2(query_embedding)
            scores, indices = self.index.search(query_embedding, min(k, len(self.documents)))
        else:
            # TF-IDF fallback search
            if self.embeddings_matrix is None:
                return []
                
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.embeddings_matrix).flatten()
            
            # Get top k indices
            top_indices = similarities.argsort()[-k:][::-1]
            scores = [similarities[idx] for idx in top_indices]
            indices = [[top_indices]]

        results = []
        for i, (score, idx) in enumerate(zip(scores[0] if self.use_sentence_transformers else scores, 
                                           indices[0] if self.use_sentence_transformers else top_indices)):
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append((doc["content"], float(score), doc["metadata"]))

        return results

    def save_index(self, filepath: str):
        """Save the index and documents"""
        if self.use_sentence_transformers:
            import faiss
            faiss.write_index(self.index, f"{filepath}.index")
        else:
            # Save TF-IDF vectorizer and matrix
            import joblib
            joblib.dump(self.vectorizer, f"{filepath}.vectorizer")
            joblib.dump(self.embeddings_matrix, f"{filepath}.embeddings")
            
        with open(f"{filepath}.docs", "wb") as f:
            pickle.dump(self.documents, f)

    def load_index(self, filepath: str):
        """Load the index and documents"""
        try:
            if self.use_sentence_transformers:
                import faiss
                self.index = faiss.read_index(f"{filepath}.index")
            else:
                import joblib
                self.vectorizer = joblib.load(f"{filepath}.vectorizer")
                self.embeddings_matrix = joblib.load(f"{filepath}.embeddings")
                
            with open(f"{filepath}.docs", "rb") as f:
                self.documents = pickle.load(f)
        except Exception as e:
            print(f"Failed to load index: {e}")

# Remove the Settings class from here - it should be in config/settings.py

# Alternative: Simple keyword-based search if all else fails
class KeywordEmbeddingService:
    """Ultra-simple fallback using keyword matching"""
    
    def __init__(self):
        self.documents = []
        
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        for i, doc in enumerate(documents):
            doc_data = {
                "content": doc.lower(),
                "metadata": metadatas[i] if metadatas else {},
                "keywords": set(doc.lower().split())
            }
            self.documents.append(doc_data)
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        query_words = set(query.lower().split())
        results = []
        
        for doc in self.documents:
            # Simple keyword overlap scoring
            overlap = len(query_words.intersection(doc["keywords"]))
            if overlap > 0:
                score = overlap / len(query_words.union(doc["keywords"]))
                results.append((doc["content"], score, doc["metadata"]))
        
        # Sort by score and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]