import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def test_facilities_endpoint():
    """Test the /facilities endpoint"""
    print("🧪 Testing /facilities endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/facilities")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Retrieved {len(data)} facilities")
            if data:
                print("Sample facility:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def test_recommend_endpoint():
    """Test the /recommend endpoint"""
    print("\n🧪 Testing /recommend endpoint...")
    
    # Test query
    test_query = "I need a quiet study area with power outlets"
    
    try:
        response = requests.post(
            f"{BASE_URL}/recommend",
            json={"query": test_query}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Recommendation response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n🧪 Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Health check:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 Starting API Tests...")
    print("=" * 50)
    
    # Test all endpoints
    test_health_endpoint()
    test_facilities_endpoint()
    test_recommend_endpoint()
    
    print("\n" + "=" * 50)
    print("🏁 API Tests Complete!")