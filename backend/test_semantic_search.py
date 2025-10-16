#!/usr/bin/env python3
"""
Test Semantic Search System

This script tests the semantic search functionality using the ChromaDB vector database.
It sends various natural language queries to see:
- How well the system understands natural language queries
- How semantic search retrieves relevant facilities
- How the LLM generates helpful responses
- How the RAG (Retrieval-Augmented Generation) pipeline works
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def test_semantic_search():
    """Test semantic search with various natural language queries"""
    
    test_cases = [
        {
            "name": "🍔 Food Query - General",
            "query": "I'm hungry, where can I eat around campus?"
        },
        {
            "name": "🥗 Food Query - Healthy",
            "query": "Looking for healthy food options with halal certification"
        },
        {
            "name": "☕ Beverage Query",
            "query": "Where can I get good coffee or tea?"
        },
        {
            "name": "🚻 Facilities Query - Restrooms",
            "query": "I need to find a clean restroom with ladies facilities"
        },
        {
            "name": "📚 Study Query - General",
            "query": "Where can I study quietly with good wifi?"
        },
        {
            "name": "🏢 Building-specific Query",
            "query": "What facilities are available in North Hill?"
        },
        {
            "name": "🌙 Late night Query",
            "query": "What places are open late at night for studying?"
        },
        {
            "name": "❄️ Comfort Query",
            "query": "I need somewhere cool to study with air conditioning"
        },
        {
            "name": "🔌 Technical Query",
            "query": "Where can I charge my laptop and work with multiple monitors?"
        },
        {
            "name": "🍜 Cuisine Query",
            "query": "I want to eat Asian food, preferably something with bubble tea"
        },
        {
            "name": "🏃 Quick Query",
            "query": "Fast food options near me"
        },
        {
            "name": "👥 Social Query",
            "query": "Good places to hang out and chat with friends"
        },
        {
            "name": "🎯 Specific Feature Query",
            "query": "Find me a place with dine-in seating and air conditioning"
        },
        {
            "name": "🔍 Vague Query Test",
            "query": "What's available?"
        },
        {
            "name": "🚿 Hygiene Query",
            "query": "Where can I freshen up and use clean facilities?"
        }
    ]
    
    print("🧪 Testing Semantic Search System")
    print("=" * 80)
    print(f"🎯 Testing {len(test_cases)} different natural language queries")
    print(f"🔗 API Base URL: {BASE_URL}")
    print("📋 This will test the complete RAG pipeline:")
    print("   1. 🔍 Query → ChromaDB vector search")
    print("   2. 📚 Retrieve relevant facilities")
    print("   3. 🤖 LLM processes and generates response")
    print("   4. 📝 Natural language recommendation")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 TEST {i}/{len(test_cases)}: {test_case['name']}")
        print(f"❓ Query: \"{test_case['query']}\"")
        print("-" * 60)
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"message": test_case['query']},
                headers={"Content-Type": "application/json"}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"⏱️  Response Time: {response_time:.2f} seconds")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response data
                llm_response = data.get('response', '')
                retrieved_facilities = data.get('retrieved_facilities', [])
                
                print("✅ SUCCESS - Semantic search completed")
                print(f"🔍 Retrieved {len(retrieved_facilities)} relevant facilities")
                
                # Show retrieved facilities
                if retrieved_facilities:
                    print("📚 Retrieved Facilities:")
                    for j, facility in enumerate(retrieved_facilities[:3], 1):  # Show top 3
                        name = facility.get('name', 'Unknown')
                        building = facility.get('building', 'Unknown Building')
                        facility_type = facility.get('type', 'Unknown Type').replace('_', ' ')  # Replace underscores with spaces
                        print(f"   {j}. {name} ({facility_type}) in {building}")
                
                # Show LLM response
                print("🤖 LLM Response:")
                response_lines = llm_response.split('\n')
                for line in response_lines[:5]:  # Show first 5 lines
                    if line.strip():
                        print(f"   {line}")
                
                if len(response_lines) > 5:
                    print(f"   ... and {len(response_lines) - 5} more lines")
                    
            else:
                print(f"❌ ERROR: Status {response.status_code}")
                print(f"📝 Error details: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR: Cannot connect to the API")
            print("💡 Make sure the FastAPI server is running with: uvicorn app.main:app --reload")
            break
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
        
        print("\n" + "=" * 60)
        
        # Small delay between requests to be nice to the server
        if i < len(test_cases):
            time.sleep(0.5)

def test_vector_db_status():
    """Test vector database status and statistics"""
    
    print("\n🗄️  Vector Database Status Check")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/vector-stats")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Vector Database Status:")
            print(f"   📊 Total Documents: {data.get('total_documents', 'Unknown')}")
            print(f"   🏢 Collections: {data.get('collections', 'Unknown')}")
            
            # Show sample documents if available
            sample_docs = data.get('sample_documents', [])
            if sample_docs:
                print(f"   📝 Sample Documents:")
                for i, doc in enumerate(sample_docs[:3], 1):
                    print(f"      {i}. {doc}")
        else:
            print(f"❌ Error getting vector stats: {response.status_code}")
            print(f"📝 Details: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking vector database: {e}")

def test_basic_connectivity():
    """Test basic API connectivity"""
    
    print("\n🔧 Basic Connectivity Tests")
    print("=" * 50)
    
    # Test root endpoint
    print("🏠 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
        else:
            print(f"❌ Root endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach root endpoint: {e}")
        return False
    
    # Test if facilities are loaded
    print("📚 Testing facility loading status...")
    try:
        response = requests.post(f"{BASE_URL}/load-facilities", json={"mode": "check"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Facilities status: {data.get('message', 'Unknown')}")
        else:
            print(f"❌ Facility loading check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot check facility status: {e}")
    
    return True

def run_comprehensive_test():
    """Run all tests in sequence"""
    
    print("🚀 Semantic Search Test Suite")
    print("=" * 80)
    print("This comprehensive test will:")
    print("  • ✅ Check API connectivity")
    print("  • ✅ Verify vector database status")
    print("  • ✅ Test semantic search with natural language queries")
    print("  • ✅ Validate RAG pipeline functionality")
    print("  • ✅ Measure response times")
    print("=" * 80)
    
    # Run basic connectivity test first
    if not test_basic_connectivity():
        print("\n❌ Basic connectivity failed. Please start the API server first.")
        print("💡 Run: uvicorn app.main:app --reload")
        return
    
    # Check vector database status
    test_vector_db_status()
    
    # Run semantic search tests
    test_semantic_search()
    
    print("\n" + "=" * 80)
    print("🏁 Semantic Search Testing Complete!")
    print("\n💡 What this tested:")
    print("   1. 🔍 Natural language query understanding")
    print("   2. 🗃️  ChromaDB vector similarity search")
    print("   3. 📚 Facility retrieval based on semantic meaning")
    print("   4. 🤖 LLM response generation with context")
    print("   5. ⚡ End-to-end RAG pipeline performance")
    print("\n🎯 The system now uses pure semantic search instead of constraints!")
    print("   - No more rigid attribute filtering")
    print("   - Natural language understanding")
    print("   - Context-aware responses")
    print("   - Vector database for similarity matching")

if __name__ == "__main__":
    run_comprehensive_test()