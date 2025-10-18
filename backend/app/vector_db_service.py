"""
Vector Database Service for NTU Facilities Semantic Search
Uses ChromaDB for vector storage and sentence-transformers for embeddings
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
import os
from typing import List, Dict, Any, Optional
import numpy as np

class FacilityVectorDB:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB with persistent storage"""
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize sentence transformer model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="ntu_facilities",
            metadata={"description": "NTU Facilities with semantic search capabilities"}
        )
        
        print(f"Vector DB initialized. Collection size: {self.collection.count()}")
    
    def create_facility_document(self, facility: Dict[str, Any]) -> str:
        """Create a rich text document for each facility for better semantic search"""
        
        # Extract facility information
        name = facility.get('name', '')
        facility_type = facility.get('type', '')
        building = facility.get('building', '')
        floor = facility.get('floor', '')
        unit = facility.get('unit_number', '')
        
        # Extract attributes and create readable descriptions
        attrs = facility.get('attrs', {})
        
        # Create attribute descriptions
        attribute_descriptions = []
        if attrs.get('aircon'):
            attribute_descriptions.append("air conditioning available")
        if attrs.get('quiet_zone'):
            attribute_descriptions.append("quiet study environment")
        if attrs.get('outlet'):
            attribute_descriptions.append("power outlets for charging devices")
        if attrs.get('monitor'):
            attribute_descriptions.append("computer monitors and screens")
        if attrs.get('whiteboard'):
            attribute_descriptions.append("whiteboard for presentations")
        if attrs.get('projector'):
            attribute_descriptions.append("projector for presentations")
        if attrs.get('halal'):
            attribute_descriptions.append("halal food options")
        if attrs.get('vegetarian'):
            attribute_descriptions.append("vegetarian food options")
        if attrs.get('dine_in'):
            attribute_descriptions.append("dine-in seating available")
        if attrs.get('takeaway'):
            attribute_descriptions.append("takeaway options")
        
        # Create opening hours description
        open_days = facility.get('open_days', [])
        open_time = facility.get('open_time', '')
        close_time = facility.get('close_time', '')
        
        schedule_desc = ""
        if open_days and open_time and close_time:
            days_str = ", ".join(open_days)
            schedule_desc = f"Open {days_str} from {open_time} to {close_time}"
        
        # Create comprehensive document
        document_parts = [
            f"Facility Name: {name}",
            f"Type: {facility_type}",
            f"Location: {building}",
        ]
        
        if floor:
            document_parts.append(f"Floor: {floor}")
        if unit:
            document_parts.append(f"Unit: {unit}")
        
        if attribute_descriptions:
            document_parts.append(f"Features: {', '.join(attribute_descriptions)}")
        
        if schedule_desc:
            document_parts.append(schedule_desc)
        
        # Add contextual descriptions based on type
        if facility_type == 'study_area':
            document_parts.append("Perfect for studying, reading, research, homework, and academic work")
        elif facility_type == 'discussion_area':
            document_parts.append("Ideal for group discussions, meetings, team work, and presentations")
        elif facility_type == 'food':
            document_parts.append("Food and dining options, restaurant, meals, eating")
        elif facility_type == 'beverage':
            document_parts.append("Drinks, coffee, tea, beverages, refreshments")
        
        return ". ".join(document_parts)
    
    def add_facilities(self, facilities: List[Dict[str, Any]]):
        """Add facilities to vector database"""
        print(f"Adding {len(facilities)} facilities to vector database...")
        
        # Prepare documents and metadata
        documents = []
        metadatas = []
        ids = []
        
        for facility in facilities:
            # Create semantic document
            document = self.create_facility_document(facility)
            documents.append(document)
            
            # Store complete facility data as metadata (handle None values)
            metadata = {
                'id': str(facility.get('id') or ''),
                'name': str(facility.get('name') or ''),
                'type': str(facility.get('type') or ''),
                'building': str(facility.get('building') or ''),
                'floor': str(facility.get('floor') or ''),
                'unit_number': str(facility.get('unit_number') or ''),
                'open_time': str(facility.get('open_time') or ''),
                'close_time': str(facility.get('close_time') or ''),
                'open_days': json.dumps(facility.get('open_days') or []),
                'attrs': json.dumps(facility.get('attrs') or {}),
                'code': str(facility.get('code') or ''),
                'map_url': str(facility.get('map_url') or '')
            }
            metadatas.append(metadata)
            ids.append(f"facility_{facility.get('id', len(ids))}")
        
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(facilities)} facilities. Total in DB: {self.collection.count()}")
    
    def semantic_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on facilities"""
        print(f"Performing semantic search for: '{query}'")
        
        # Query the vector database
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Process results
        facilities = []
        if results['metadatas'] and results['metadatas'][0]:
            for i, metadata in enumerate(results['metadatas'][0]):
                distance = results['distances'][0][i]
                
                # Reconstruct facility object
                facility = {
                    'id': int(metadata['id']),
                    'name': metadata['name'],
                    'type': metadata['type'].replace('_', ' '),  # Replace underscores with spaces
                    'building': metadata['building'],
                    'floor': metadata['floor'],
                    'unit_number': metadata['unit_number'],
                    'open_time': metadata['open_time'],
                    'close_time': metadata['close_time'],
                    'open_days': json.loads(metadata['open_days']),
                    'attrs': json.loads(metadata['attrs']),
                    'code': metadata['code'],
                    'map_url': metadata['map_url'],
                    'distance': distance,  # Use distance directly
                    'matched_text': results['documents'][0][i]
                }
                facilities.append(facility)
        
        print(f"Found {len(facilities)} semantic matches")
        return facilities
    
    def update_facility(self, facility: Dict[str, Any]):
        """Update a single facility in the vector database"""
        facility_id = f"facility_{facility.get('id')}"
        
        # Create new document
        document = self.create_facility_document(facility)
        
        # Create metadata
        metadata = {
            'id': str(facility.get('id', '')),
            'name': facility.get('name', ''),
            'type': facility.get('type', ''),
            'building': facility.get('building', ''),
            'floor': str(facility.get('floor', '')),
            'unit_number': facility.get('unit_number', ''),
            'open_time': str(facility.get('open_time', '')),
            'close_time': str(facility.get('close_time', '')),
            'open_days': json.dumps(facility.get('open_days', [])),
            'attrs': json.dumps(facility.get('attrs', {})),
            'code': facility.get('code', ''),
            'map_url': facility.get('map_url', '')
        }
        
        # Update in ChromaDB
        self.collection.update(
            ids=[facility_id],
            documents=[document],
            metadatas=[metadata]
        )
        
        print(f"Updated facility: {facility.get('name')}")
    
    def delete_facility(self, facility_id: int):
        """Delete a facility from vector database"""
        self.collection.delete(ids=[f"facility_{facility_id}"])
        print(f"Deleted facility ID: {facility_id}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        
        try:
            count = self.collection.count() or 0
            sample = self.collection.peek(limit=5) or {'metadatas': []} 
            
            metadatas = sample.get('metadatas', [])
            sample_names = []
            if metadatas and isinstance(metadatas, list):
                sample_names = [m.get('name', 'Unnamed') for m in metadatas if isinstance(m, dict)]

            return {
                'total_facilities': count,
                'collection_name': self.collection.name,
                'sample_facilities': sample_names
            }
        except Exception as e:
            print(f"Error retrieving collection stats: {e}")
            raise e
    
    def reset_database(self):
        """Clear all data from the vector database"""
        self.client.delete_collection("ntu_facilities")
        self.collection = self.client.get_or_create_collection(
            name="ntu_facilities",
            metadata={"description": "NTU Facilities with semantic search capabilities"}
        )
        print("Vector database reset complete")

# Standalone functions for easy integration
def initialize_vector_db() -> FacilityVectorDB:
    """Initialize and return vector database instance"""
    return FacilityVectorDB()

def load_facilities_to_vector_db(vector_db: FacilityVectorDB, facilities_data: List[Dict]):
    """Load facilities from your PostgreSQL data into vector database"""
    vector_db.add_facilities(facilities_data)

if __name__ == "__main__":
    # Test the vector database
    print("🧪 Testing Vector Database")
    
    # Sample facility data
    sample_facilities = [
        {
            'id': 1,
            'name': 'Lee Wee Nam Library',
            'type': 'study_area',
            'building': 'North Spine',
            'floor': 3,
            'attrs': {'aircon': True, 'quiet_zone': True, 'outlet': True, 'monitor': True},
            'open_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'open_time': '08:30:00',
            'close_time': '21:30:00'
        },
        {
            'id': 2,
            'name': 'Each a Cup',
            'type': 'food',
            'building': 'North Spine',
            'floor': 1,
            'attrs': {'halal': True, 'dine_in': True},
            'open_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'open_time': '09:00:00',
            'close_time': '21:00:00'
        }
    ]
    
    # Initialize and test
    vector_db = FacilityVectorDB()
    vector_db.add_facilities(sample_facilities)
    
    # Test semantic search
    test_queries = [
        "I need a quiet place to study",
        "Where can I get food?",
        "Study space with computers",
        "Halal dining options"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        results = vector_db.semantic_search(query, n_results=2)
        for result in results:
            print(f"  📍 {result['name']} - Score: {result['semantic_score']:.3f}")