#!/usr/bin/env python3
"""
Load facilities from PostgreSQL to ChromaDB vector database
"""

import requests
import json

def load_facilities():
    """Call the load-facilities endpoint to refresh vector database"""
    
    print("🔄 Loading facilities from PostgreSQL to vector database...")
    print("=" * 60)
    
    try:
        # Call the load-facilities endpoint
        response = requests.post('http://127.0.0.1:8000/load-facilities', json={})
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Facilities loaded successfully!")
            print(f"📝 Message: {data.get('message', 'No message')}")
            print(f"📊 Total Facilities: {data.get('total_facilities', 'Unknown')}")
            print(f"⏱️  Processing Time: {data.get('processing_time_seconds', 'Unknown')} seconds")
            
            # Show some details if available
            if 'facilities_loaded' in data:
                facilities = data['facilities_loaded']
                print(f"🏢 Sample facilities loaded:")
                for i, facility in enumerate(facilities[:5], 1):
                    name = facility.get('name', 'Unknown')
                    building = facility.get('building', 'Unknown')
                    facility_type = facility.get('type', 'Unknown')
                    print(f"   {i}. {name} ({facility_type}) in {building}")
                
                if len(facilities) > 5:
                    print(f"   ... and {len(facilities) - 5} more facilities")
            
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"📝 Details: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed!")
        print("💡 Make sure the FastAPI server is running:")
        print("   uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    load_facilities()