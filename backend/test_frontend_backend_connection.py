#!/usr/bin/env python3
"""
Simple script to test if the backend API is working
Run this from the backend directory to verify everything works
"""

import requests
import json
import sys

def test_backend():
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing NTU Navigation Backend API")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1️⃣ Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Semantic search: {data.get('semantic_search_available', False)}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False
    
    # Test 2: Chat endpoint
    print("\n2️⃣ Testing chat endpoint...")
    try:
        test_query = {
            "message": "Where can I find a quiet study area?",
            "max_results": 3
        }
        
        response = requests.post(
            f"{base_url}/chat",
            headers={"Content-Type": "application/json"},
            json=test_query
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working")
            print(f"   Response length: {len(data.get('response', ''))}")
            print(f"   Facilities found: {len(data.get('retrieved_facilities', []))}")
            print(f"   Query day: {data.get('query_day', 'None')}")
            print(f"   LLM provider: {data.get('llm_provider', 'Unknown')}")
            
            # Show first part of response
            response_text = data.get('response', '')
            if response_text:
                preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
                print(f"   Response preview: {preview}")
            
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 3: Vector stats
    print("\n3️⃣ Testing vector database stats...")
    try:
        response = requests.get(f"{base_url}/vector-stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Vector stats working")
            print(f"   Total documents: {data.get('total_documents', 'unknown')}")
            print(f"   Available: {data.get('is_available', False)}")
        else:
            print(f"⚠️ Vector stats failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Vector stats error: {e}")
    
    print("\n🎉 Backend API tests completed successfully!")
    print("\n📱 Frontend connection instructions:")
    print("   1. Make sure your backend is running on http://127.0.0.1:8000")
    print("   2. Update frontend API_BASE if needed")
    print("   3. Test the chat functionality")
    
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)