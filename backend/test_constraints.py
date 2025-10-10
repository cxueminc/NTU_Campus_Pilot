import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def test_constraint_checking():
    """Test constraint checking with detailed logging"""
    
    test_cases = [
        {
            "name": "🏢 Study area with aircon (OPEN facilities only)",
            "request": {
                "query": "I need a study area with air conditioning",
                "constraints": {
                    "open_now": True,
                    "attributes": {
                        "aircon": True
                    }
                }
            }
        },
        {
            "name": "🔇 Quiet study with power outlets",
            "request": {
                "query": "Find me a quiet study area with power outlets",
                "constraints": {
                    "open_now": True,
                    "attributes": {
                        "quiet": True,
                        "sockets": True
                    }
                }
            }
        },
        {
            "name": "🏢 Specific building + aircon",
            "request": {
                "query": "Study space in North Spine with aircon",
                "constraints": {
                    "building": "North Spine",
                    "open_now": True,
                    "attributes": {
                        "aircon": True
                    }
                }
            }
        },
        {
            "name": "⏰ Any time (including closed facilities)",
            "request": {
                "query": "Study areas with monitors (any time)",
                "constraints": {
                    "open_now": False,  # Don't filter by opening hours
                    "attributes": {
                        "monitor": True
                    }
                }
            }
        },
        {
            "name": "📅 Day-specific query (Saturday)",
            "request": {
                "query": "Where can I study on Saturday?",
                "constraints": {
                    "open_now": False,  # We're asking about Saturday, not now
                    "attributes": {}
                }
            }
        },
        {
            "name": "📅 Day-specific query with attributes (Saturday + aircon)",
            "request": {
                "query": "Study places with aircon on Saturday",
                "constraints": {
                    "open_now": False,  # Saturday-specific, not current time
                    "attributes": {
                        "aircon": True
                    }
                }
            }
        }
    ]
    
    print("🧪 Testing Constraint Checking System")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 TEST {i}: {test_case['name']}")
        print(f"📋 Request: {json.dumps(test_case['request'], indent=2)}")
        print("-" * 60)
        
        try:
            response = requests.post(
                f"{BASE_URL}/recommend",
                json=test_case['request']
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                recommendation = data.get('recommendation', '')
                
                print("✅ SUCCESS - Recommendations received:")
                print(f"📝 Response:")
                for line in recommendation.split('\n')[:5]:  # Show first 5 lines
                    if line.strip():
                        print(f"   {line}")
                
                if len(recommendation.split('\n')) > 5:
                    print(f"   ... and {len(recommendation.split('\n')) - 5} more")
                    
            else:
                print(f"❌ ERROR: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
        
        print("\n" + "=" * 60)

def test_basic_functionality():
    """Test basic endpoints to ensure everything works"""
    
    print("\n🔧 Basic Functionality Tests")
    print("=" * 50)
    
    # Test facilities endpoint
    print("📚 Testing /facilities endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/facilities")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} facilities in database")
            if data:
                facility = data[0]
                print(f"📋 Sample facility: {facility.get('name')} in {facility.get('building')}")
                print(f"   Attributes: {list(facility.get('attrs', {}).keys()) if facility.get('attrs') else 'None'}")
                print(f"   Open time: {facility.get('open_time')}")
                print(f"   Close time: {facility.get('close_time')}")
                print(f"   Open days: {facility.get('open_days')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 Constraint Checking Test Suite")
    print("=" * 80)
    print("This will test:")
    print("  • ✅ Opening hours checking (open_now constraint)")
    print("  • ✅ Building filtering")
    print("  • ✅ Attribute matching (aircon, quiet, sockets, etc.)")
    print("  • ✅ Score-based ranking")
    print("  • ✅ Detailed constraint logging")
    
    # Run tests
    test_basic_functionality()
    test_constraint_checking()
    
    print("\n" + "=" * 80)
    print("🏁 Constraint Testing Complete!")
    print("\n💡 What the code checks for user constraints:")
    print("   1. 🕐 Opening hours (open_time, close_time, open_days)")
    print("   2. 🏢 Building match")
    print("   3. 📋 Facility type")
    print("   4. 🔧 Attributes (aircon, quiet_zone, outlet, monitor, etc.)")
    print("   5. 📊 Scores facilities based on how well they match")
    print("   6. 🎯 Returns only facilities that meet ALL constraints")