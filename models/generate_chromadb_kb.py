"""
Generate ChromaDB Knowledge Base with OpenAI Embeddings

This script creates a local ChromaDB vector database containing:
1. All synthetic training data (TSV files) - queries with intent labels
2. Intent response templates (pre-written responses for each intent)

Uses OpenAI's text-embedding-3-small model for high-quality embeddings.
"""

import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pandas as pd
import json
from typing import List, Dict, Any
from tqdm import tqdm

class ChromaKnowledgeBaseGenerator:
    """Generate ChromaDB knowledge base with OpenAI embeddings"""

    def __init__(self, openai_api_key: str, persist_directory: str = "./data/chromadb"):
        """
        Initialize ChromaDB generator

        Args:
            openai_api_key: OpenAI API key for embeddings
            persist_directory: Where to store ChromaDB data
        """
        self.persist_directory = persist_directory

        # Initialize OpenAI embedding function
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name="text-embedding-3-small"  # Latest, most efficient model
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        print(f"✅ ChromaDB initialized at: {persist_directory}")
        print(f"✅ Using OpenAI embedding model: text-embedding-3-small")

    def reset_collection(self, collection_name: str = "hnu_knowledge_base"):
        """Delete existing collection if it exists"""
        try:
            self.client.delete_collection(collection_name)
            print(f"🗑️  Deleted existing collection: {collection_name}")
        except:
            print(f"📝 No existing collection to delete")

    def create_collection(self, collection_name: str = "hnu_knowledge_base"):
        """Create ChromaDB collection with OpenAI embeddings"""
        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.openai_ef,
            metadata={"description": "HNU University chatbot knowledge base"}
        )
        print(f"✅ Created collection: {collection_name}")
        return self.collection

    def load_tsv_data(self, tsv_path: str, language: str, user_type: str) -> List[Dict[str, Any]]:
        """
        Load training data from TSV files

        Args:
            tsv_path: Path to TSV file
            language: 'en' or 'de'
            user_type: 'employee', 'student', or 'partner'

        Returns:
            List of documents with text, metadata
        """
        df = pd.read_csv(tsv_path, sep='\t')

        documents = []
        for idx, row in df.iterrows():
            doc = {
                'text': row['text'],
                'intent': row['label'],
                'language': language,
                'user_type': user_type,
                'source_type': 'training_query',
                'source_file': os.path.basename(tsv_path)
            }
            documents.append(doc)

        print(f"   Loaded {len(documents)} queries from {os.path.basename(tsv_path)}")
        return documents

    def generate_intent_responses(self) -> List[Dict[str, Any]]:
        """
        Generate synthetic intent response templates

        These are pre-written responses for each intent that the chatbot can use
        as context when generating responses.

        Returns:
            List of intent response documents
        """
        # Common intents across user types
        intents = {
            # Employee intents
            'it_support_employee': {
                'en': 'For IT support, please contact the IT helpdesk at it-support@hnu.de or call +49 731 9762-1234. You can also submit a ticket through the HNU intranet portal.',
                'de': 'Für IT-Support wenden Sie sich bitte an den IT-Helpdesk unter it-support@hnu.de oder rufen Sie +49 731 9762-1234 an. Sie können auch ein Ticket über das HNU-Intranet einreichen.'
            },
            'room_booking': {
                'en': 'To book a room, please visit the room booking system at rooms.hnu.de or contact facilities@hnu.de. You will need your employee credentials to access the booking system.',
                'de': 'Um einen Raum zu buchen, besuchen Sie bitte das Raumbuchungssystem unter rooms.hnu.de oder kontaktieren Sie facilities@hnu.de. Sie benötigen Ihre Mitarbeiter-Zugangsdaten für das Buchungssystem.'
            },
            'password_reset_employee': {
                'en': 'To reset your password, visit the self-service portal at password.hnu.de or contact IT support at it-support@hnu.de. Have your employee ID ready.',
                'de': 'Um Ihr Passwort zurückzusetzen, besuchen Sie das Self-Service-Portal unter password.hnu.de oder kontaktieren Sie den IT-Support unter it-support@hnu.de. Halten Sie Ihre Mitarbeiternummer bereit.'
            },
            'vpn_access': {
                'en': 'VPN access can be configured by downloading the VPN client from vpn.hnu.de. For setup instructions, refer to the IT documentation or contact it-support@hnu.de.',
                'de': 'VPN-Zugang kann durch Herunterladen des VPN-Clients von vpn.hnu.de konfiguriert werden. Anweisungen finden Sie in der IT-Dokumentation oder kontaktieren Sie it-support@hnu.de.'
            },
            'payroll_inquiry': {
                'en': 'For payroll inquiries, please contact the HR department at hr@hnu.de or call +49 731 9762-2000. Payroll is processed on the 15th of each month.',
                'de': 'Für Gehaltsanfragen wenden Sie sich bitte an die Personalabteilung unter hr@hnu.de oder rufen Sie +49 731 9762-2000 an. Die Gehaltsabrechnung erfolgt am 15. jeden Monats.'
            },
            'vacation_request': {
                'en': 'To request vacation time, submit your request through the HR portal at hr.hnu.de or email your supervisor and HR at hr@hnu.de. Requests should be submitted at least 2 weeks in advance.',
                'de': 'Um Urlaub zu beantragen, reichen Sie Ihren Antrag über das HR-Portal unter hr.hnu.de ein oder senden Sie eine E-Mail an Ihren Vorgesetzten und HR unter hr@hnu.de. Anträge sollten mindestens 2 Wochen im Voraus eingereicht werden.'
            },

            # Student intents
            'enrollment_inquiry': {
                'en': 'For enrollment information, visit the student portal at portal.hnu.de or contact the academic office at student@hnu.de or +49 731 9762-1500.',
                'de': 'Für Informationen zur Einschreibung besuchen Sie das Studierendenportal unter portal.hnu.de oder kontaktieren Sie das Prüfungsamt unter student@hnu.de oder +49 731 9762-1500.'
            },
            'course_inquiry': {
                'en': 'Course information can be found in the course catalog at catalog.hnu.de. For specific questions, contact your academic advisor or student@hnu.de.',
                'de': 'Kursinformationen finden Sie im Kursverzeichnis unter catalog.hnu.de. Bei Fragen wenden Sie sich an Ihren Studienberater oder student@hnu.de.'
            },
            'transcript_request': {
                'en': 'To request an official transcript, submit a request through the student portal or email student@hnu.de. Processing typically takes 5-7 business days.',
                'de': 'Um eine offizielle Bescheinigung anzufordern, reichen Sie einen Antrag über das Studierendenportal ein oder senden Sie eine E-Mail an student@hnu.de. Die Bearbeitung dauert in der Regel 5-7 Werktage.'
            },
            'library_inquiry': {
                'en': 'The library is open Monday-Friday 8:00-20:00 and Saturday 9:00-16:00. For research assistance, contact library@hnu.de or visit the library information desk.',
                'de': 'Die Bibliothek ist Montag-Freitag 8:00-20:00 und Samstag 9:00-16:00 geöffnet. Für Rechercheunterstützung kontaktieren Sie library@hnu.de oder besuchen Sie die Informationstheke der Bibliothek.'
            },

            # Partner intents
            'partnership_inquiry': {
                'en': 'For partnership opportunities, please contact our partnerships office at partnerships@hnu.de or call +49 731 9762-3000. We welcome collaborations with industry and academic institutions.',
                'de': 'Für Partnerschaftsmöglichkeiten kontaktieren Sie bitte unser Partnerschaftsbüro unter partnerships@hnu.de oder rufen Sie +49 731 9762-3000 an. Wir begrüßen Kooperationen mit Industrie und akademischen Institutionen.'
            },
            'collaboration_inquiry': {
                'en': 'We offer various collaboration opportunities including research projects, internships, and guest lectures. Contact partnerships@hnu.de to discuss possibilities.',
                'de': 'Wir bieten verschiedene Kooperationsmöglichkeiten, darunter Forschungsprojekte, Praktika und Gastvorträge. Kontaktieren Sie partnerships@hnu.de, um Möglichkeiten zu besprechen.'
            },

            # General intents
            'general_inquiry': {
                'en': 'For general inquiries about HNU, visit our website at www.hnu.de or contact our main office at info@hnu.de or +49 731 9762-0.',
                'de': 'Für allgemeine Anfragen zur HNU besuchen Sie unsere Website unter www.hnu.de oder kontaktieren Sie unser Hauptbüro unter info@hnu.de oder +49 731 9762-0.'
            },
            'contact_inquiry': {
                'en': 'You can find contact information for all departments on our website at www.hnu.de/contact or call our main switchboard at +49 731 9762-0.',
                'de': 'Kontaktinformationen für alle Abteilungen finden Sie auf unserer Website unter www.hnu.de/kontakt oder rufen Sie unsere Zentrale unter +49 731 9762-0 an.'
            },
        }

        documents = []
        for intent, responses in intents.items():
            for language, text in responses.items():
                doc = {
                    'text': text,
                    'intent': intent,
                    'language': language,
                    'user_type': 'all',
                    'source_type': 'intent_response',
                    'source_file': 'generated_responses'
                }
                documents.append(doc)

        print(f"   Generated {len(documents)} intent response templates")
        return documents

    def add_documents_to_collection(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        Add documents to ChromaDB collection in batches

        Args:
            documents: List of document dictionaries
            batch_size: Number of documents to add per batch
        """
        total_docs = len(documents)
        print(f"📝 Adding {total_docs} documents to ChromaDB (batch size: {batch_size})...")

        for i in tqdm(range(0, total_docs, batch_size)):
            batch = documents[i:i + batch_size]

            # Prepare batch data
            ids = [f"doc_{i+j}" for j in range(len(batch))]
            texts = [doc['text'] for doc in batch]
            metadatas = [
                {
                    'intent': doc['intent'],
                    'language': doc['language'],
                    'user_type': doc['user_type'],
                    'source_type': doc['source_type'],
                    'source_file': doc['source_file']
                }
                for doc in batch
            ]

            # Add to collection (OpenAI embedding happens automatically)
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )

    def generate_knowledge_base(self, data_dir: str = "./data/bot_data/synthetic_data"):
        """
        Main method to generate complete knowledge base

        Args:
            data_dir: Directory containing TSV training data
        """
        print("\n" + "="*70)
        print("🚀 GENERATING CHROMADB KNOWLEDGE BASE WITH OPENAI EMBEDDINGS")
        print("="*70 + "\n")

        all_documents = []

        # 1. Load TSV training data
        print("📊 Loading TSV training data...")
        for language in ['en', 'de']:
            for user_type in ['employee', 'student', 'partner']:
                tsv_path = os.path.join(data_dir, language, f"{user_type}_data.tsv")

                if os.path.exists(tsv_path):
                    docs = self.load_tsv_data(tsv_path, language, user_type)
                    all_documents.extend(docs)
                else:
                    print(f"   ⚠️  Warning: File not found: {tsv_path}")

        print(f"✅ Loaded {len(all_documents)} training queries\n")

        # 2. Generate intent response templates
        print("🎯 Generating intent response templates...")
        response_docs = self.generate_intent_responses()
        all_documents.extend(response_docs)
        print(f"✅ Total documents to embed: {len(all_documents)}\n")

        # 3. Add all documents to ChromaDB
        self.add_documents_to_collection(all_documents)

        # 4. Save configuration
        config = {
            'total_documents': len(all_documents),
            'training_queries': len(all_documents) - len(response_docs),
            'intent_responses': len(response_docs),
            'embedding_model': 'text-embedding-3-small',
            'embedding_provider': 'openai',
            'collection_name': 'hnu_knowledge_base',
            'languages': ['en', 'de'],
            'user_types': ['employee', 'student', 'partner']
        }

        config_path = os.path.join(self.persist_directory, 'kb_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✅ Knowledge base created successfully!")
        print(f"📊 Statistics:")
        print(f"   - Total documents: {config['total_documents']}")
        print(f"   - Training queries: {config['training_queries']}")
        print(f"   - Intent responses: {config['intent_responses']}")
        print(f"   - Embedding model: {config['embedding_model']}")
        print(f"   - Storage location: {self.persist_directory}")
        print(f"   - Config saved to: {config_path}")
        print("\n" + "="*70 + "\n")

    def test_query(self, query: str, n_results: int = 5):
        """
        Test the knowledge base with a sample query

        Args:
            query: Query string
            n_results: Number of results to return
        """
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 70)

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        print(f"📊 Found {len(results['documents'][0])} results:\n")

        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"{i}. [Intent: {metadata['intent']} | Lang: {metadata['language']} | Type: {metadata['user_type']}]")
            print(f"   Similarity: {1 - distance:.4f}")
            print(f"   Text: {doc[:150]}{'...' if len(doc) > 150 else ''}")
            print()


def main():
    """Main execution function"""
    import argparse
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description='Generate ChromaDB knowledge base with OpenAI embeddings')
    parser.add_argument('--data_dir', type=str, default='./data/bot_data/synthetic_data',
                       help='Directory containing TSV training data')
    parser.add_argument('--persist_dir', type=str, default='./data/chromadb',
                       help='Directory to store ChromaDB data')
    parser.add_argument('--openai_key', type=str, default=None,
                       help='OpenAI API key (or set OPENAI_API_KEY env variable or .env file)')
    parser.add_argument('--reset', action='store_true',
                       help='Reset existing collection before creating new one')
    parser.add_argument('--test', action='store_true',
                       help='Run test queries after generation')

    args = parser.parse_args()

    # Get OpenAI API key (priority: CLI arg > env variable > .env file)
    openai_api_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ Error: OpenAI API key not provided!")
        print("   Options:")
        print("   1. Create a .env file with: OPENAI_API_KEY=your_key_here")
        print("   2. Set OPENAI_API_KEY environment variable")
        print("   3. Use --openai_key argument")
        return

    # Initialize generator
    generator = ChromaKnowledgeBaseGenerator(
        openai_api_key=openai_api_key,
        persist_directory=args.persist_dir
    )

    # Reset collection if requested
    if args.reset:
        generator.reset_collection()

    # Create collection
    generator.create_collection()

    # Generate knowledge base
    generator.generate_knowledge_base(data_dir=args.data_dir)

    # Test queries
    if args.test:
        print("\n" + "="*70)
        print("🧪 RUNNING TEST QUERIES")
        print("="*70)

        test_queries = [
            "How do I reset my password?",
            "Wie kann ich einen Raum buchen?",
            "What are the library hours?",
            "Ich brauche IT-Support",
            "How to enroll in courses?"
        ]

        for query in test_queries:
            generator.test_query(query, n_results=3)


if __name__ == "__main__":
    main()
