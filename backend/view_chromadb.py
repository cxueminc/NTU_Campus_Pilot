#!/usr/bin/env python3
"""
View ChromaDB Contents
Quick script to see what's stored in the vector database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.vector_db_service import FacilityVectorDB
import json

def view_chromadb_contents():
    """View all contents stored in ChromaDB"""
    
    print("🗄️  ChromaDB Contents Viewer")
    print("=" * 60)
    
    try:
        # Initialize vector database
        vector_db = FacilityVectorDB()
        
        # Get collection info
        collection = vector_db.collection
        
        # Get all documents
        results = collection.get()
        
        print(f"📊 Collection: {collection.name}")
        print(f"📈 Total Documents: {len(results['ids'])}")
        print("=" * 60)
        
        # Display each document
        for i, doc_id in enumerate(results['ids'], 1):
            metadata = results['metadatas'][i-1] if results['metadatas'] else {}
            document = results['documents'][i-1] if results['documents'] else ""
            
            print(f"\n📄 Document {i} (ID: {doc_id})")
            print("-" * 40)
            
            # Print metadata (facility info)
            if metadata:
                print("🏷️  Metadata:")
                for key, value in metadata.items():
                    if value is not None:
                        print(f"   {key}: {value}")
            
            # Print document text (searchable content)
            if document:
                print(f"📝 Searchable Text:")
                print(f"   {document[:200]}{'...' if len(document) > 200 else ''}")
            
            print("-" * 40)
        
        print(f"\n✅ Successfully displayed {len(results['ids'])} documents from ChromaDB")
        
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")
        print("💡 Make sure ChromaDB is initialized and contains data")

if __name__ == "__main__":
    view_chromadb_contents()