"""
query_chromadb.py

Query the HNU knowledge base built with ChromaDB and OpenAI embeddings.
Replaces the old FAISS-based query_kb.py with ChromaDB for better performance.
"""

import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChromaKnowledgeBaseQuery:
    """Query ChromaDB knowledge base with OpenAI embeddings"""

    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "hnu_knowledge_base",
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize ChromaDB query interface

        Args:
            persist_directory: Where ChromaDB data is stored
            collection_name: Name of the collection to query
            openai_api_key: OpenAI API key (uses env variable if not provided)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Get API key
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY or pass it as argument.")

        # Initialize OpenAI embedding function
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name="text-embedding-3-small"
        )

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.openai_ef
            )
            print(f"✅ Loaded ChromaDB collection: {collection_name}")
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found. Run generate_chromadb_kb.py first. Error: {e}")

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_language: Optional[str] = None,
        filter_user_type: Optional[str] = None,
        filter_intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base

        Args:
            query_text: Query string
            top_k: Number of results to return
            filter_language: Filter by language ('en' or 'de')
            filter_user_type: Filter by user type ('employee', 'student', 'partner', 'all')
            filter_intent: Filter by specific intent

        Returns:
            List of results with text, metadata, and similarity score
        """
        # Build metadata filter
        where_filter = {}
        if filter_language:
            where_filter["language"] = filter_language
        if filter_user_type and filter_user_type != 'all':
            where_filter["user_type"] = filter_user_type
        if filter_intent:
            where_filter["intent"] = filter_intent

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        # Format results
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted_results.append({
                'text': doc,
                'intent': metadata.get('intent', 'unknown'),
                'language': metadata.get('language', 'unknown'),
                'user_type': metadata.get('user_type', 'unknown'),
                'source_type': metadata.get('source_type', 'unknown'),
                'source_file': metadata.get('source_file', 'unknown'),
                'similarity_score': float(1 - distance),  # Convert distance to similarity
                'distance': float(distance)
            })

        return formatted_results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        return {
            'collection_name': self.collection_name,
            'total_documents': self.collection.count(),
            'persist_directory': self.persist_directory
        }


# Standalone query function (for backward compatibility with old FAISS code)
def query_kb(
    query: str,
    chromadb_dir: str = "./data/chromadb",
    collection_name: str = "hnu_knowledge_base",
    top_k: int = 5,
    filter_language: Optional[str] = None,
    filter_user_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query ChromaDB knowledge base (backward compatible with old FAISS query_kb)

    Args:
        query: Query text
        chromadb_dir: Directory where ChromaDB is stored
        collection_name: Collection name
        top_k: Number of results
        filter_language: Language filter
        filter_user_type: User type filter

    Returns:
        List of matching documents with metadata and scores
    """
    kb = ChromaKnowledgeBaseQuery(
        persist_directory=chromadb_dir,
        collection_name=collection_name
    )

    return kb.query(
        query_text=query,
        top_k=top_k,
        filter_language=filter_language,
        filter_user_type=filter_user_type
    )


def main():
    """Interactive CLI for querying the knowledge base"""
    import argparse

    parser = argparse.ArgumentParser(description='Query HNU ChromaDB knowledge base')
    parser.add_argument('--chromadb_dir', type=str, default='./data/chromadb',
                       help='ChromaDB storage directory')
    parser.add_argument('--collection', type=str, default='hnu_knowledge_base',
                       help='Collection name')
    parser.add_argument('--top_k', type=int, default=5,
                       help='Number of results to return')
    parser.add_argument('--language', type=str, choices=['en', 'de', None], default=None,
                       help='Filter by language')
    parser.add_argument('--user_type', type=str, choices=['employee', 'student', 'partner', 'all', None],
                       default=None, help='Filter by user type')
    parser.add_argument('--query', type=str, default=None,
                       help='Single query to run (if not provided, enters interactive mode)')

    args = parser.parse_args()

    # Initialize query interface
    try:
        kb = ChromaKnowledgeBaseQuery(
            persist_directory=args.chromadb_dir,
            collection_name=args.collection
        )
    except Exception as e:
        print(f"❌ Error initializing ChromaDB: {e}")
        return

    # Print stats
    stats = kb.get_stats()
    print(f"\n📊 Knowledge Base Statistics:")
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Total Documents: {stats['total_documents']}")
    print(f"   Location: {stats['persist_directory']}\n")

    # Single query mode
    if args.query:
        results = kb.query(
            query_text=args.query,
            top_k=args.top_k,
            filter_language=args.language,
            filter_user_type=args.user_type
        )

        print(f"🔍 Query: {args.query}")
        print("="*70)
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Intent: {result['intent']} | Lang: {result['language']} | Type: {result['user_type']}")
            print(f"    Similarity: {result['similarity_score']:.4f}")
            print(f"    Text: {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")
        return

    # Interactive mode
    print("✅ Knowledge base loaded. Type your queries (English or German). Type 'exit' to quit.\n")
    print("Optional filters: ':lang=en/de' or ':type=employee/student/partner'")
    print("Example: 'How to reset password :lang=en :type=employee'\n")

    while True:
        try:
            user_input = input("🔎 Query: ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                break

            if not user_input:
                continue

            # Parse filters from query
            parts = user_input.split(':')
            query_text = parts[0].strip()

            filter_lang = args.language
            filter_type = args.user_type

            for part in parts[1:]:
                if 'lang=' in part:
                    filter_lang = part.split('=')[1].strip()
                elif 'type=' in part:
                    filter_type = part.split('=')[1].strip()

            # Query
            results = kb.query(
                query_text=query_text,
                top_k=args.top_k,
                filter_language=filter_lang,
                filter_user_type=filter_type
            )

            print("\n" + "="*70)
            print(f"📊 Found {len(results)} results:")
            print("="*70)

            for i, result in enumerate(results, 1):
                print(f"\n[{i}] Intent: {result['intent']} | Lang: {result['language']} | Type: {result['user_type']}")
                print(f"    Similarity: {result['similarity_score']:.4f}")
                print(f"    Source: {result['source_type']}")
                print(f"    Text: {result['text'][:250]}{'...' if len(result['text']) > 250 else ''}")

            print("\n")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
