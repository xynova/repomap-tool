"""Embedding-based semantic matcher using CodeRankEmbed."""

import hashlib
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.logging_service import get_logger
from ..core.cache_manager import CacheManager

logger = get_logger(__name__)


class EmbeddingMatcher:
    """Semantic matching using CodeRankEmbed embeddings with persistent caching."""

    def __init__(
        self,
        model_name: str = "nomic-ai/CodeRankEmbed",
        cache_manager: Optional[CacheManager] = None,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize EmbeddingMatcher with CodeRankEmbed model.

        Args:
            model_name: Model name (default: CodeRankEmbed)
            cache_manager: Optional CacheManager for file change detection
            cache_dir: Directory for persistent embedding cache
        """
        self.model_name = model_name
        self.cache_manager = cache_manager
        self.cache_dir = cache_dir or ".repomap/cache/embeddings"
        self.enabled = False
        self.model = None
        self.embedding_cache: Dict[str, np.ndarray] = {}

        # Initialize model with GPU detection
        try:
            logger.debug(f"Initializing EmbeddingMatcher with model: {model_name}")
            logger.debug(f"Cache directory: {self.cache_dir}")

            # Detect and use GPU if available
            device = self._detect_best_device()
            logger.debug(f"Using device: {device}")

            self.model = SentenceTransformer(
                model_name, trust_remote_code=True, device=device
            )
            self.enabled = True
            logger.debug(f"✓ EmbeddingMatcher initialized successfully on {device}")
        except Exception as e:
            logger.warning(f"Failed to initialize EmbeddingMatcher: {e}")
            logger.warning("Embedding-based search will be disabled")

        # Create cache directory
        if self.enabled:
            try:
                Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create cache directory: {e}")

    def _detect_best_device(self) -> str:
        """
        Detect the best available device for embedding computation.

        Returns:
            Device string ('cuda', 'mps', or 'cpu')
        """
        try:
            import torch

            # Check for CUDA (NVIDIA GPU)
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA GPU detected: {gpu_name} (count: {gpu_count})")
                return "cuda"

            # Check for MPS (Apple Silicon GPU)
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("Apple Silicon GPU (MPS) detected")
                return "mps"

            # Fallback to CPU
            else:
                logger.debug("No GPU detected, using CPU")
                return "cpu"

        except ImportError:
            logger.warning("PyTorch not available, using CPU")
            return "cpu"
        except Exception as e:
            logger.warning(f"Error detecting GPU: {e}, falling back to CPU")
            return "cpu"

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cached embedding."""
        return Path(self.cache_dir) / f"{cache_key}.npy"

    def get_embedding(
        self, text: str, file_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Get embedding for text, using cache if available.

        Args:
            text: Text to embed
            file_path: Optional file path for cache association

        Returns:
            Embedding vector or None if disabled
        """
        if not self.enabled:
            logger.debug("EmbeddingMatcher is disabled")
            return None

        if self.model is None:
            logger.error(
                "Model is None despite enabled=True - attempting re-initialization"
            )
            try:
                self.model = SentenceTransformer(
                    self.model_name, trust_remote_code=True
                )
                logger.info("Model re-initialized successfully")
            except Exception as e:
                logger.error(f"Failed to re-initialize model: {e}")
                self.enabled = False
                return None

        # Check in-memory cache first
        cache_key = self._get_cache_key(text)
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        # Check persistent cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                # Check if file is still valid via cache manager
                if self.cache_manager and file_path:
                    # If file was modified, cache is invalid
                    # For now, just load - cache invalidation happens at index time
                    pass
                else:
                    embedding = np.load(cache_path)
                    self.embedding_cache[cache_key] = embedding
                    return embedding  # type: ignore[no-any-return]
            except Exception as e:
                logger.debug(f"Failed to load cached embedding: {e}")

        # Compute embedding
        try:
            logger.debug(f"Computing embedding for text: '{text[:50]}...'")
            logger.debug(f"Model type: {type(self.model)}")
            logger.debug(f"Model enabled: {self.enabled}")
            if hasattr(self.model, "tokenizer"):
                logger.debug(f"Model tokenizer: {type(self.model.tokenizer)}")
            else:
                logger.debug("Model has no tokenizer attribute")

            # Model should be valid at this point
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Save to persistent cache
            try:
                np.save(cache_path, embedding)
            except Exception as e:
                logger.debug(f"Failed to save embedding to cache: {e}")

            # Store in memory cache
            self.embedding_cache[cache_key] = embedding
            return embedding

        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None

    def batch_compute_embeddings(
        self, identifiers: Dict[str, str]
    ) -> Dict[str, np.ndarray]:
        """
        Batch compute embeddings for multiple identifiers.

        Args:
            identifiers: Dict mapping identifier text to file path

        Returns:
            Dict mapping identifier text to embedding vector
        """
        if not self.enabled or not self.model:
            return {}

        results = {}
        to_compute = []
        to_compute_keys = []

        # Check what's already cached
        for identifier, file_path in identifiers.items():
            cache_key = self._get_cache_key(identifier)
            cache_path = self._get_cache_path(cache_key)

            # Check in-memory cache
            if cache_key in self.embedding_cache:
                results[identifier] = self.embedding_cache[cache_key]
                continue

            # Check persistent cache
            if cache_path.exists():
                try:
                    embedding = np.load(cache_path)
                    self.embedding_cache[cache_key] = embedding
                    results[identifier] = embedding
                    continue
                except Exception:
                    pass

            # Need to compute
            to_compute.append(identifier)
            to_compute_keys.append(cache_key)

        # Batch compute remaining
        if to_compute:
            try:
                logger.info(
                    f"Computing embeddings for {len(to_compute)} identifiers..."
                )
                embeddings = self.model.encode(to_compute, convert_to_numpy=True)

                for i, identifier in enumerate(to_compute):
                    embedding = embeddings[i]
                    cache_key = to_compute_keys[i]
                    cache_path = self._get_cache_path(cache_key)

                    # Save to persistent cache
                    try:
                        np.save(cache_path, embedding)
                    except Exception as e:
                        logger.debug(f"Failed to save embedding: {e}")

                    # Store in memory and results
                    self.embedding_cache[cache_key] = embedding
                    results[identifier] = embedding

            except Exception as e:
                logger.error(f"Failed to batch compute embeddings: {e}")

        return results

    def load_cached_embeddings(self, identifiers: Set[str]) -> Dict[str, np.ndarray]:
        """
        Load cached embeddings for identifiers.

        Args:
            identifiers: Set of identifier texts

        Returns:
            Dict mapping identifier to embedding (only successfully loaded)
        """
        results = {}

        for identifier in identifiers:
            cache_key = self._get_cache_key(identifier)

            # Check in-memory cache
            if cache_key in self.embedding_cache:
                results[identifier] = self.embedding_cache[cache_key]
                continue

            # Check persistent cache
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                try:
                    embedding = np.load(cache_path)
                    self.embedding_cache[cache_key] = embedding
                    results[identifier] = embedding
                except Exception:
                    pass

        return results

    def find_semantic_matches(
        self, query: str, identifiers: Set[str], threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find semantically similar identifiers using embeddings.

        Args:
            query: Query text
            identifiers: Set of identifier texts to search
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of (identifier, similarity_score) tuples, sorted by score
        """
        if not self.enabled or not self.model:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            return []

        # Load cached embeddings
        cached_embeddings = self.load_cached_embeddings(identifiers)

        # Compute missing embeddings on demand
        missing = identifiers - set(cached_embeddings.keys())
        if missing:
            for identifier in missing:
                embedding = self.get_embedding(identifier)
                if embedding is not None:
                    cached_embeddings[identifier] = embedding

        # Calculate similarities
        matches = []
        query_embedding_2d = query_embedding.reshape(1, -1)

        for identifier, embedding in cached_embeddings.items():
            embedding_2d = embedding.reshape(1, -1)
            similarity = cosine_similarity(query_embedding_2d, embedding_2d)[0][0]

            if similarity >= threshold:
                matches.append((identifier, float(similarity)))

        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def clear_cache(self) -> None:
        """Clear in-memory embedding cache."""
        self.embedding_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        persistent_count = 0
        if Path(self.cache_dir).exists():
            persistent_count = len(list(Path(self.cache_dir).glob("*.npy")))

        return {
            "memory_cache_size": len(self.embedding_cache),
            "persistent_cache_size": persistent_count,
        }
