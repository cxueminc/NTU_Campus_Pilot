from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from .database import get_db, Facility
from dotenv import load_dotenv

# Import semantic services from app directory
try:
    from .openai_semantic_chat_service import OpenAISemanticChatService as SemanticChatService
    from .vector_db_service import FacilityVectorDB
    SEMANTIC_SEARCH_AVAILABLE = True
    print("OpenAI GPT-4 semantic search and vector database available")
except ImportError as e:
    print(f"Warning: OpenAI semantic search not available: {e}")
    print("Install dependencies: pip install chromadb sentence-transformers openai")
    print("Also set OPENAI_API_KEY environment variable")
    SEMANTIC_SEARCH_AVAILABLE = False

load_dotenv()

app = FastAPI(
    title="NTU Facilities Semantic Search API",
    description="Semantic search for NTU facilities using vector database",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global semantic chat service
semantic_chat = None
if SEMANTIC_SEARCH_AVAILABLE:
    try:
        semantic_chat = SemanticChatService()
        print("Semantic chat service initialized")
    except Exception as e:
        print(f"Failed to initialize semantic chat: {e}")
        SEMANTIC_SEARCH_AVAILABLE = False

# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    max_results: int = 5

class LoadFacilitiesResponse(BaseModel):
    message: str
    total_loaded: int
    vector_db_initialized: bool

class VectorStatsResponse(BaseModel):
    total_documents: int  # Changed from total_facilities to match test expectations
    collections: str      # Changed from collection_name to match test expectations  
    is_available: bool
    sample_documents: Optional[List[str]] = []  # Added for test compatibility

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """Root endpoint to confirm API is running"""
    return {
        "message": "NTU Facilities Semantic Search API is running!", 
        "status": "healthy",
        "semantic_search_available": SEMANTIC_SEARCH_AVAILABLE,
        "version": "1.0.0"
    }

@app.post("/chat")
def semantic_chat_endpoint(request: ChatRequest):
    """
    Main semantic search endpoint using vector database
    Pure conversational interface for facility recommendations with conversation history
    """
    
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Semantic search service not available. Please install required dependencies."
        )
    
    if not semantic_chat:
        raise HTTPException(
            status_code=503,
            detail="Semantic chat service not initialized"
        )
    
    try:
        # Convert conversation history to simple format
        conversation_context = []
        if request.conversation_history:
            conversation_context = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.conversation_history
            ]
        
        result = semantic_chat.process_query(
            request.message, 
            max_results=request.max_results,
            conversation_history=conversation_context
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing semantic search: {str(e)}"
        )

@app.post("/load-facilities", response_model=LoadFacilitiesResponse)
def load_facilities_to_vector_db(db: Session = Depends(get_db)):
    """
    Load all facilities from PostgreSQL database into vector database
    REPLACES existing data (clears and reloads)
    Use this when you want to update with latest database changes
    """
    
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Semantic search service not available"
        )
    
    if not semantic_chat:
        raise HTTPException(
            status_code=503,
            detail="Semantic chat service not initialized"
        )
    
    try:
        # Get all facilities from database
        facilities = db.query(Facility).all()
        
        # Convert to dict format
        facilities_data = []
        for facility in facilities:
            facility_dict = {
                'id': facility.id,
                'name': facility.name,
                'type': facility.type.replace('_', ' '),  # Replace underscores with spaces
                'building': facility.building,
                'floor': facility.floor,
                'attrs': facility.attrs or {},
                'open_days': facility.open_days or [],
                'open_time': str(facility.open_time) if facility.open_time else None,
                'close_time': str(facility.close_time) if facility.close_time else None,
                'unit_number': facility.unit_number,
                'map_url': facility.map_url
            }
            facilities_data.append(facility_dict)
        
        # Load into semantic chat service (REPLACE mode - clears existing data)
        semantic_chat.load_facilities_from_db(facilities_data, update_mode="replace")
        
        return LoadFacilitiesResponse(
            message="Facilities replaced successfully in vector database",
            total_loaded=len(facilities_data),
            facilities_loaded=facilities_data[:10],
            vector_db_initialized=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading facilities: {str(e)}"
        )

@app.get("/vector-stats", response_model=VectorStatsResponse)
def get_vector_database_stats():
    """Get statistics about the vector database"""
    
    if not SEMANTIC_SEARCH_AVAILABLE:
        return VectorStatsResponse(
            total_facilities=0,
            collection_name="not_available",
            is_available=False
        )
    
    if not semantic_chat:
        return VectorStatsResponse(
            total_facilities=0,
            collection_name="not_initialized",
            is_available=False
        )
    
    try:
        stats = semantic_chat.vector_db.get_collection_stats()
        return VectorStatsResponse(
            total_documents=stats['total_facilities'],
            collections=stats['collection_name'],
            is_available=True,
            sample_documents=stats.get('sample_facilities   ', [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting vector database stats: {str(e)}"
        )

@app.get("/facilities")
def get_all_facilities(db: Session = Depends(get_db)):
    """Get all facilities from PostgreSQL database"""
    
    try:
        facilities = db.query(Facility).all()
        
        facilities_list = []
        for facility in facilities:
            facility_dict = {
                'id': facility.id,
                'name': facility.name,
                'type': facility.type.replace('_', ' '),  # Replace underscores with spaces
                'building': facility.building,
                'floor': facility.floor,
                'attrs': facility.attrs or {},
                'open_days': facility.open_days or [],
                'open_time': str(facility.open_time) if facility.open_time else None,
                'close_time': str(facility.close_time) if facility.close_time else None
            }
            facilities_list.append(facility_dict)
        
        return {"facilities": facilities_list, "total": len(facilities_list)}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving facilities: {str(e)}"
        )

@app.get("/facilities/{facility_id}")
def get_facility_by_id(facility_id: int, db: Session = Depends(get_db)):
    """Get a specific facility by ID"""
    
    try:
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        
        if not facility:
            raise HTTPException(
                status_code=404,
                detail=f"Facility with ID {facility_id} not found"
            )
        
        facility_dict = {
            'id': facility.id,
            'name': facility.name,
            'type': facility.type.replace('_', ' '),  # Replace underscores with spaces
            'building': facility.building,
            'floor': facility.floor,
            'attrs': facility.attrs or {},
            'open_days': facility.open_days or [],
            'open_time': str(facility.open_time) if facility.open_time else None,
            'close_time': str(facility.close_time) if facility.close_time else None
        }
        
        return facility_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving facility: {str(e)}"
        )

# ============================================================================
# Health Check and Status
# ============================================================================

@app.get("/health")
def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "semantic_search_available": SEMANTIC_SEARCH_AVAILABLE,
        "semantic_chat_initialized": semantic_chat is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/chromadb-contents")
def get_chromadb_contents():
    """Debug endpoint to view all ChromaDB contents"""
    if not SEMANTIC_SEARCH_AVAILABLE or not semantic_chat:
        raise HTTPException(status_code=503, detail="Vector database not available")
    
    try:
        vector_db = semantic_chat.vector_db
        collection = vector_db.collection
        
        # Get all documents
        results = collection.get()
        
        # Format for API response
        documents = []
        for i, doc_id in enumerate(results['ids']):
            doc_info = {
                "id": doc_id,
                "metadata": results['metadatas'][i] if results['metadatas'] else {},
                "document": results['documents'][i] if results['documents'] else "",
                "embedding_preview": results['embeddings'][i][:5] if results.get('embeddings') else None
            }
            documents.append(doc_info)
        
        return {
            "collection_name": collection.name,
            "total_documents": len(results['ids']),
            "documents": documents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ChromaDB contents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)