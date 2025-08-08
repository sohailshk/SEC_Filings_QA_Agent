"""
Vector Database Service using FAISS

This module handles vector embeddings storage and retrieval using FAISS
for fast similarity search on SEC filing document chunks.

Best Practices Followed:
- Efficient vector storage and retrieval
- Metadata preservation for source attribution
- Batch processing for better performance
- Error handling and logging
"""

import faiss
import numpy as np
import pickle
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
import json

# Setup logging for this module
logger = logging.getLogger(__name__)

class VectorDatabaseService:
    """
    FAISS-based vector database for semantic search on document chunks.
    
    This service handles:
    - Text embedding generation using sentence transformers
    - Vector storage and indexing with FAISS
    - Similarity search and retrieval
    - Metadata management for source attribution
    """
    
    def __init__(self, vector_db_path: str, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize vector database service.
        
        Args:
            vector_db_path (str): Path to store FAISS index and metadata
            embedding_model (str): Name of sentence transformer model to use
        """
        self.vector_db_path = vector_db_path
        self.embedding_model_name = embedding_model
        self.index_file = os.path.join(vector_db_path, "faiss_index.bin")
        self.metadata_file = os.path.join(vector_db_path, "metadata.pkl")
        
        # Initialize sentence transformer model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index and metadata storage
        self.faiss_index = None
        self.metadata_store = []  # List to store metadata for each vector
        self.vector_count = 0
        
        self.ensure_directory_exists()
        self.load_or_create_index()
        
        logger.info(f"Vector database service initialized with {self.vector_count} vectors")
    
    def ensure_directory_exists(self):
        """Create vector database directory if it doesn't exist."""
        if not os.path.exists(self.vector_db_path):
            os.makedirs(self.vector_db_path)
            logger.info(f"Created vector database directory: {self.vector_db_path}")
    
    def load_or_create_index(self):
        """
        Load existing FAISS index or create a new one.
        Also loads associated metadata.
        """
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            # Load existing index and metadata
            try:
                self.faiss_index = faiss.read_index(self.index_file)
                
                with open(self.metadata_file, 'rb') as f:
                    self.metadata_store = pickle.load(f)
                
                self.vector_count = self.faiss_index.ntotal
                logger.info(f"Loaded existing FAISS index with {self.vector_count} vectors")
                
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
                self.create_new_index()
        else:
            self.create_new_index()
    
    def create_new_index(self):
        """Create a new FAISS index for vector storage."""
        # Create FAISS index for L2 (Euclidean) distance
        # L2 distance works well for sentence transformer embeddings
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dimension)
        self.metadata_store = []
        self.vector_count = 0
        logger.info(f"Created new FAISS index with dimension: {self.embedding_dimension}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using sentence transformers.
        
        Args:
            texts (List[str]): List of text chunks to embed
            
        Returns:
            np.ndarray: Array of embeddings with shape (len(texts), embedding_dimension)
        """
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        try:
            # Generate embeddings in batch for efficiency
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10  # Show progress for large batches
            )
            
            # Ensure embeddings are float32 for FAISS compatibility
            embeddings = embeddings.astype(np.float32)
            
            logger.debug(f"Generated embeddings with shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def add_documents(self, texts: List[str], metadata_list: List[Dict[str, Any]]) -> List[int]:
        """
        Add documents to the vector database.
        
        Args:
            texts (List[str]): List of text chunks to add
            metadata_list (List[Dict[str, Any]]): Metadata for each text chunk
            
        Returns:
            List[int]: List of vector IDs for the added documents
        """
        if len(texts) != len(metadata_list):
            raise ValueError("Number of texts must match number of metadata entries")
        
        logger.info(f"Adding {len(texts)} documents to vector database")
        
        # Generate embeddings for all texts
        embeddings = self.generate_embeddings(texts)
        
        # Add embeddings to FAISS index
        start_id = self.vector_count
        self.faiss_index.add(embeddings)
        
        # Store metadata for each vector
        for i, metadata in enumerate(metadata_list):
            vector_id = start_id + i
            # Add vector ID to metadata for easy reference
            metadata_with_id = {**metadata, 'vector_id': vector_id, 'text': texts[i]}
            self.metadata_store.append(metadata_with_id)
        
        self.vector_count = self.faiss_index.ntotal
        vector_ids = list(range(start_id, self.vector_count))
        
        logger.info(f"Added {len(texts)} documents. Total vectors: {self.vector_count}")
        return vector_ids
    
    def search_similar(self, query_text: str, k: int = 5, 
                      metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            query_text (str): Query text to search for
            k (int): Number of similar documents to return
            metadata_filter (Dict[str, Any]): Optional filter by metadata fields
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with metadata and scores
        """
        if self.vector_count == 0:
            logger.warning("No vectors in database for search")
            return []
        
        logger.debug(f"Searching for '{query_text[:100]}...' with k={k}")
        
        # Generate embedding for query
        query_embedding = self.generate_embeddings([query_text])
        
        # Search FAISS index
        distances, indices = self.faiss_index.search(query_embedding, min(k, self.vector_count))
        
        # Prepare results with metadata
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
                
            metadata = self.metadata_store[idx].copy()
            
            # Apply metadata filtering if specified
            if metadata_filter:
                if not self._matches_filter(metadata, metadata_filter):
                    continue
            
            # Convert distance to similarity score (lower distance = higher similarity)
            similarity_score = 1.0 / (1.0 + distance)
            
            result = {
                'text': metadata.get('text', ''),
                'metadata': metadata,
                'similarity_score': float(similarity_score),
                'distance': float(distance),
                'vector_id': metadata.get('vector_id', idx)
            }
            results.append(result)
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.debug(f"Found {len(results)} similar documents")
        return results[:k]  # Return top k results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_criteria: Dict[str, Any]) -> bool:
        """
        Check if metadata matches filter criteria.
        
        Args:
            metadata (Dict[str, Any]): Document metadata
            filter_criteria (Dict[str, Any]): Filter criteria to match
            
        Returns:
            bool: True if metadata matches all filter criteria
        """
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True
    
    def get_document_by_vector_id(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by vector ID.
        
        Args:
            vector_id (int): Vector ID to retrieve
            
        Returns:
            Dict[str, Any]: Document with metadata or None if not found
        """
        if 0 <= vector_id < len(self.metadata_store):
            return self.metadata_store[vector_id].copy()
        return None
    
    def save_index(self):
        """
        Save FAISS index and metadata to disk.
        Should be called after adding documents to persist changes.
        """
        try:
            # Save FAISS index
            faiss.write_index(self.faiss_index, self.index_file)
            
            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata_store, f)
            
            logger.info(f"Saved FAISS index with {self.vector_count} vectors")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector database statistics.
        
        Returns:
            Dict[str, Any]: Database statistics
        """
        stats = {
            'total_vectors': self.vector_count,
            'embedding_dimension': self.embedding_dimension,
            'model_name': self.embedding_model_name,
            'index_type': type(self.faiss_index).__name__,
            'index_file_exists': os.path.exists(self.index_file),
            'metadata_file_exists': os.path.exists(self.metadata_file)
        }
        
        # Add file sizes if files exist
        if stats['index_file_exists']:
            stats['index_file_size_mb'] = os.path.getsize(self.index_file) / (1024 * 1024)
        if stats['metadata_file_exists']:
            stats['metadata_file_size_mb'] = os.path.getsize(self.metadata_file) / (1024 * 1024)
        
        return stats
    
    def clear_database(self):
        """
        Clear all vectors and metadata from the database.
        Use with caution - this operation cannot be undone.
        """
        logger.warning("Clearing vector database - all data will be lost")
        
        self.create_new_index()
        
        # Remove index files if they exist
        for file_path in [self.index_file, self.metadata_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        logger.info("Vector database cleared successfully")
