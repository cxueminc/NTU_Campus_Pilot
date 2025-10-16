#!/usr/bin/env python3
"""
Quick test to verify facility type fix
"""

import requests

def test_facility_types():
    print("🧪 Testing Facility Type Display Fix")
    print("=" * 40)
    
    response = requests.post('http://127.0.0.1:8000/chat', json={'message': 'toilet'})
    
    if response.status_code == 200:
        result = response.json()
        facilities = result.get('retrieved_facilities', [])
        
        print(f"✅ Found {len(facilities)} facilities:")
        for i, facility in enumerate(facilities[:3], 1):
            name = facility.get('name', 'Unknown')
            building = facility.get('building', 'Unknown Building') 
            facility_type = facility.get('type', 'Unknown Type').replace('_', ' ')  # Replace underscores with spaces
            distance = facility.get('distance', 0)
            
            print(f"{i}. {name}")
            print(f"   Type: {facility_type}")
            print(f"   Building: {building}")
            print(f"   Distance: {distance:.3f}")
            print()
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_facility_types()