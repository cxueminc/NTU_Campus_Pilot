from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .database import get_db, Facility
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="NTU Facilities API")

# allow your React Native app to call the API during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint to confirm API is running"""
    return {"message": "NTU Facilities API is running!", "status": "healthy"}


class Constraints(BaseModel):
    type: Optional[List[str]] = None
    building: Optional[str] = None
    open_now: bool = True
    attributes: Dict[str, Any] = {}


class RecommendRequest(BaseModel):
    query: Optional[str] = None
    constraints: Constraints = Constraints()
    top_k: int = 5


def is_facility_open_now(facility: dict) -> bool:
    """Check if facility is open now based on open_time, close_time, and open_days"""
    # Get timing data directly from facility object (not from attrs)
    open_time = facility.get("open_time")
    close_time = facility.get("close_time") 
    open_days = facility.get("open_days") or []  # Handle None values
    
    print(f"🕐 Checking if {facility.get('name')} is open:")
    print(f"   Open time: {open_time}")
    print(f"   Close time: {close_time}")
    print(f"   Open days: {open_days}")
    
    # If no time information, assume it's open
    if not open_time or not close_time:
        print(f"   ✅ No time restrictions - assuming OPEN")
        return True
    
    # Check if today is in open_days
    if open_days and isinstance(open_days, list):
        current_day = datetime.now().strftime("%A")  # e.g., "Monday"
        print(f"   📅 Today is: {current_day}")
        
        # More precise day matching
        day_found = any(day.strip().lower() == current_day.lower() for day in open_days)
        
        if not day_found:
            print(f"   ❌ CLOSED - Not open on {current_day} (Open days: {open_days})")
            return False
        print(f"   ✅ Open on {current_day}")
    elif not open_days:
        print(f"   ℹ️ No specific days listed - assuming open all week")
    
    # Check current time against open/close times
    try:
        from datetime import time
        now = datetime.now().time()
        print(f"   🕐 Current time: {now}")
        
        # Parse time strings (handle both "HH:MM:SS" and "HH:MM")
        def parse_time_string(time_str):
            if not time_str:
                return None
            # Remove timezone info if present
            clean_time = str(time_str).split("+")[0].split("-")[0]
            try:
                if clean_time.count(":") == 2:  # HH:MM:SS
                    return datetime.strptime(clean_time, "%H:%M:%S").time()
                elif clean_time.count(":") == 1:  # HH:MM
                    return datetime.strptime(clean_time, "%H:%M").time()
            except:
                return None
        
        open_t = parse_time_string(str(open_time))
        close_t = parse_time_string(str(close_time))
        
        print(f"   📍 Parsed open time: {open_t}")
        print(f"   📍 Parsed close time: {close_t}")
        
        if open_t and close_t:
            if open_t <= close_t:  # Same day (e.g., 9:00 - 17:00)
                is_open = open_t <= now <= close_t
                print(f"   {'✅ OPEN' if is_open else '❌ CLOSED'} - Same day schedule")
                return is_open
            else:  # Crosses midnight (e.g., 22:00 - 02:00)
                is_open = now >= open_t or now <= close_t
                print(f"   {'✅ OPEN' if is_open else '❌ CLOSED'} - Crosses midnight")
                return is_open
    except Exception as e:
        print(f"   ⚠️ Error parsing time: {e}")
    
    print(f"   ✅ Assuming OPEN (couldn't parse times)")
    return True  # If we can't parse, assume open


def is_facility_open_on_day(facility: dict, target_day: str) -> bool:
    """Check if facility is open on a specific day"""
    open_days = facility.get("open_days") or []  # Handle None values
    
    if not open_days or not isinstance(open_days, list):
        return True  # No restrictions or invalid data
    
    # Normalize day names for comparison
    target_day_lower = target_day.strip().lower()
    facility_days = [day.strip().lower() for day in open_days]
    
    return target_day_lower in facility_days


def extract_day_from_query(query: str) -> str:
    """Extract specific day mentioned in user query"""
    if not query:
        return None
        
    query_lower = query.lower()
    
    # Day patterns to look for
    day_patterns = {
        'monday': ['monday', 'mon'],
        'tuesday': ['tuesday', 'tue', 'tues'],
        'wednesday': ['wednesday', 'wed'],
        'thursday': ['thursday', 'thu', 'thur'],
        'friday': ['friday', 'fri'],
        'saturday': ['saturday', 'sat'],
        'sunday': ['sunday', 'sun']
    }
    
    for day, patterns in day_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            return day.capitalize()  # Return "Monday", "Tuesday", etc.
    
    return None


def score(f: dict, c: Constraints) -> float:
    """Score facilities based on user constraints and database attributes"""
    s = 0.0

    if c.building and f["building"].lower() == c.building.lower():
        s += 0.2

    # Use correct database field names from attrs JSONB field
    facility_attrs = f.get("attrs", {}) or {}  # Handle None case
    
    # Map user request terms to database field names:
    # "quiet" -> "quiet_zone" in database
    if c.attributes.get("quiet") and facility_attrs.get("quiet_zone"):
        s += 0.4

    # "sockets" -> "outlet" in database  
    if c.attributes.get("sockets") and facility_attrs.get("outlet"):
        s += 0.2
        
    # Additional scoring for other attributes
    if c.attributes.get("aircon") and facility_attrs.get("aircon"):
        s += 0.1
        
    if c.attributes.get("monitor") and facility_attrs.get("monitor"):
        s += 0.1
        
    # IMPROVED: Score higher for study-related facilities based on type and name
    facility_type = (f.get("type") or "").lower()
    facility_name = (f.get("name") or "").lower()
    
    # High score for dedicated study facilities
    study_types = ["library", "study_area", "learning_pod", "study_room", "reading_room"]
    study_names = ["library", "study", "learning", "reading", "pod"]
    
    if facility_type in study_types:
        s += 0.5  # High bonus for dedicated study types
    elif any(study_word in facility_name for study_word in study_names):
        s += 0.3  # Medium bonus for study-related names
    elif any(study_word in facility_type for study_word in study_names):
        s += 0.3  # Medium bonus for study-related types
        
    # Penalty for food facilities in study queries (if somehow they pass filtering)
    food_types = ["food", "restaurant", "cafe", "canteen", "dining"]
    food_names = ["restaurant", "food", "cafe", "canteen", "dining"]
    
    if (facility_type in food_types or 
        any(food_word in facility_name for food_word in food_names)):
        s -= 0.3  # Penalty for food facilities in study context
        
    return min(s, 1.0)


@app.post("/recommend")
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    """
    Intelligent recommendation endpoint that processes natural language queries
    and returns formatted recommendations using LLM
    """
    # ===== INCOMING REQUEST LOGGING =====
    print("=" * 60)
    print("🔥 NEW REQUEST RECEIVED")
    print("=" * 60)
    print(f"📥 Frontend Query: '{req.query}'")
    print(f"📊 Full Request Object: {req}")
    print(f"📋 Request Constraints: {req.constraints}")
    print(f"🔢 Requested Top K: {req.top_k}")
    print("=" * 60)
    
    try:
        if not req.query or not req.query.strip():
            error_response = {"detail": "Please provide a query describing what you're looking for"}
            print(f"❌ Sending Error Response: {error_response}")
            raise HTTPException(status_code=400, detail="Please provide a query describing what you're looking for")
        
        # Get all facilities from database
        print("📚 Fetching facilities from database...")
        facilities = db.query(Facility).all()
        print(f"📊 Found {len(facilities)} facilities")
        
        # Convert to a format suitable for constraint checking and LLM processing
        facilities_data = []
        for facility in facilities:
            facility_info = {
                "id": facility.id,
                "name": facility.name,
                "type": facility.type,
                "building": facility.building,
                "floor": facility.floor,
                "unit_number": facility.unit_number,
                "open_time": str(facility.open_time) if facility.open_time else None,
                "close_time": str(facility.close_time) if facility.close_time else None,
                "open_days": facility.open_days,
                "attrs": facility.attrs
            }
            facilities_data.append(facility_info)
        
        # ===== APPLY USER CONSTRAINTS =====
        print("🔍 Applying user constraints...")
        filtered_facilities = []
        
        # Detect query intent for smarter filtering
        query_lower = req.query.lower()
        study_keywords = ['study', 'quiet', 'reading', 'research', 'work', 'library']
        food_keywords = ['eat', 'food', 'lunch', 'dinner', 'meal', 'restaurant', 'cuisine']
        drink_keywords = ['drink', 'beverage', 'coffee', 'tea', 'bubble tea', 'thirsty']
        discussion_keywords = ['discuss', 'meeting', 'group', 'collaboration', 'team']
        
        is_study_query = any(word in query_lower for word in study_keywords)
        is_food_query = any(word in query_lower for word in food_keywords)
        is_drink_query = any(word in query_lower for word in drink_keywords)
        is_discussion_query = any(word in query_lower for word in discussion_keywords)
        
        # Check if user specified a particular day
        specified_day = extract_day_from_query(req.query)
        current_day = datetime.now().strftime("%A")
        
        print(f"🧠 Query intent detected - Study: {is_study_query}, Food: {is_food_query}, Drink: {is_drink_query}, Discussion: {is_discussion_query}")
        print(f"📅 Day context - Today: {current_day}, User specified: {specified_day or 'None'}")
        
        # Smart deduplication for facilities with multiple schedules
        # Group facilities by base name and location, then pick the best schedule
        facility_groups = {}
        
        for facility in facilities_data:
            # Create base identifier (without schedule-specific info)
            base_name = facility['name'].lower().strip()
            building = facility.get('building', '').lower().strip()
            floor = facility.get('floor', '')
            
            # Group key for facilities that are essentially the same place
            group_key = f"{base_name}_{building}_{floor}"
            
            if group_key not in facility_groups:
                facility_groups[group_key] = []
            
            facility_groups[group_key].append(facility)
        
        print(f"� Grouped {len(facilities_data)} facilities into {len(facility_groups)} unique locations")
        
        # Process each facility group
        for group_key, group_facilities in facility_groups.items():
            print(f"\n🏢 Processing group: {group_key} ({len(group_facilities)} schedules)")
            
            # If user specified a day, filter to facilities open on that day
            target_day = specified_day or current_day
            relevant_facilities = []
            
            for facility in group_facilities:
                if specified_day:
                    # User asked for specific day - check if facility is open on that day
                    if is_facility_open_on_day(facility, specified_day):
                        relevant_facilities.append(facility)
                        print(f"   ✅ {facility['name']} - Open on {specified_day}")
                    else:
                        print(f"   ❌ {facility['name']} - Closed on {specified_day} (Open: {facility.get('open_days', [])})")
                else:
                    # No specific day mentioned - use current day and open_now constraint
                    if req.constraints.open_now:
                        if is_facility_open_now(facility):
                            relevant_facilities.append(facility)
                            print(f"   ✅ {facility['name']} - Open now")
                        else:
                            print(f"   ❌ {facility['name']} - Closed now")
                    else:
                        # Not filtering by time - include all schedules but prefer current day
                        relevant_facilities.append(facility)
                        print(f"   ℹ️ {facility['name']} - Added (no time filtering)")
            
            if not relevant_facilities:
                print(f"   ⚠️ No schedules available for {target_day}")
                continue
            
            # Pick the best facility from this group
            # Priority: 1) Matches target day exactly, 2) Longer hours, 3) More attributes
            def schedule_priority(fac):
                open_days = fac.get('open_days') or []  # Handle None values
                target_day_exact = any(day.strip().lower() == target_day.lower() for day in open_days) if isinstance(open_days, list) else False
                
                # Calculate hours of operation
                try:
                    open_time = str(fac.get('open_time', ''))
                    close_time = str(fac.get('close_time', ''))
                    
                    if open_time and close_time and ':' in open_time and ':' in close_time:
                        open_hour = int(open_time.split(':')[0])
                        close_hour = int(close_time.split(':')[0])
                        hours = (close_hour - open_hour) % 24
                    else:
                        hours = 0
                except:
                    hours = 0
                
                # Count available attributes
                attrs_count = len(fac.get('attrs', {}) or {})
                
                return (
                    target_day_exact,  # Primary: exact day match
                    hours,            # Secondary: longer hours
                    attrs_count       # Tertiary: more features
                )
            
            # Select the best facility from this group
            best_facility = max(relevant_facilities, key=schedule_priority)
            
            print(f"   🎯 Selected: {best_facility['name']} (Open: {best_facility.get('open_days', [])})")
            
            # Now apply other constraints to the selected facility
            facility = best_facility
            meets_constraints = True
            
            # 1. ✅ Intelligent type filtering based on query intent
            facility_type = facility.get("type", "").lower()
            
            if is_study_query and facility_type not in ['study_area', 'discussion_area']:
                print(f"❌ {facility['name']} - Wrong type for study query (type: {facility_type})")
                meets_constraints = False
                continue
                
            if is_food_query and facility_type != 'food':
                print(f"❌ {facility['name']} - Wrong type for food query (type: {facility_type})")
                meets_constraints = False
                continue
                
            if is_drink_query and facility_type != 'beverage':
                print(f"❌ {facility['name']} - Wrong type for drink query (type: {facility_type})")
                meets_constraints = False
                continue
                
            if is_discussion_query and facility_type not in ['discussion_area', 'study_area']:
                print(f"❌ {facility['name']} - Wrong type for discussion query (type: {facility_type})")
                meets_constraints = False
                continue
            
            # 2. Check building constraint
            if req.constraints.building:
                if facility["building"].lower() != req.constraints.building.lower():
                    print(f"❌ {facility['name']} - Wrong building (want: {req.constraints.building}, has: {facility['building']})")
                    meets_constraints = False
                    continue
                
                print(f"✅ {facility['name']} - Correct building ({facility['building']})")
            
            # 3. Check type constraint
            if req.constraints.type:
                facility_type = facility.get("type", "").lower()
                type_match = any(t.lower() in facility_type or facility_type in t.lower() 
                               for t in req.constraints.type)
                if not type_match:
                    print(f"❌ {facility['name']} - Wrong type (want: {req.constraints.type}, has: {facility['type']})")
                    meets_constraints = False
                    continue
                
                print(f"✅ {facility['name']} - Correct type ({facility['type']})")
            
            # 4. SMART TYPE FILTERING based on user query
            query_lower = req.query.lower() if req.query else ""
            facility_type = facility.get("type", "").lower()
            facility_name = facility.get("name", "").lower()
            
            # If user asks for study-related things, filter out non-study facilities
            study_keywords = ["study", "quiet", "library", "learning", "reading", "workspace"]
            food_keywords = ["food", "eat", "restaurant", "cafe", "dining", "canteen"]
            
            is_study_query = any(keyword in query_lower for keyword in study_keywords)
            is_food_query = any(keyword in query_lower for keyword in food_keywords)
            
            # Check if facility type matches query intent
            if is_study_query and not is_food_query:
                # User wants study facilities - exclude food places
                if (facility_type in ["food", "restaurant", "cafe", "canteen"] or 
                    any(food_word in facility_name for food_word in ["restaurant", "food", "cafe", "canteen", "dining"])):
                    print(f"❌ {facility['name']} - FOOD FACILITY excluded from STUDY query")
                    meets_constraints = False
                    continue
                    
                # Prefer actual study facilities
                study_types = ["library", "study_area", "learning_pod", "study_room", "reading_room"]
                study_names = ["library", "study", "learning", "reading", "pod"]
                
                is_study_facility = (facility_type in study_types or 
                                   any(study_word in facility_name for study_word in study_names))
                
                if is_study_facility:
                    print(f"✅ {facility['name']} - STUDY FACILITY matches study query")
                else:
                    print(f"⚠️ {facility['name']} - Not a dedicated study facility, but checking attributes...")
            
            elif is_food_query and not is_study_query:
                # User wants food facilities - exclude study-only places
                if facility_type in ["library", "study_area", "learning_pod"]:
                    print(f"❌ {facility['name']} - STUDY FACILITY excluded from FOOD query")
                    meets_constraints = False
                    continue
            
            # 5. Check attribute constraints (like aircon, quiet, etc.)
            facility_attrs = facility.get("attrs", {}) or {}
            for attr_name, required_value in req.constraints.attributes.items():
                # Map user-friendly terms to database field names
                attr_mapping = {
                    "quiet": "quiet_zone",
                    "sockets": "outlet", 
                    "outlets": "outlet",
                    "aircon": "aircon",
                    "monitor": "monitor"
                }
                
                db_field = attr_mapping.get(attr_name.lower(), attr_name)
                facility_value = facility_attrs.get(db_field)
                
                print(f"🔍 Checking {facility['name']} for {attr_name} ({db_field}): user wants {required_value}, facility has {facility_value}")
                
                if required_value and not facility_value:
                    print(f"❌ {facility['name']} - Missing required attribute: {attr_name}")
                    meets_constraints = False
                    break
                elif required_value and facility_value:
                    print(f"✅ {facility['name']} - Has required attribute: {attr_name}")
            
            # If facility meets all constraints, add it to filtered list
            if meets_constraints:
                # Calculate score for this facility
                facility_score = score(facility, req.constraints)
                facility["constraint_score"] = facility_score
                filtered_facilities.append(facility)
                print(f"✅ {facility['name']} - PASSES all constraints (score: {facility_score})")
            
        print(f"📊 After filtering: {len(filtered_facilities)} facilities meet constraints")
        
        # Remove duplicates based on facility ID and name combination
        seen_ids = set()
        seen_names = set()
        unique_facilities = []
        for facility in filtered_facilities:
            # Create unique identifier combining ID and name
            unique_key = f"{facility['id']}_{facility['name'].lower().strip()}"
            
            if unique_key not in seen_ids and facility['name'].lower().strip() not in seen_names:
                seen_ids.add(unique_key)
                seen_names.add(facility['name'].lower().strip())
                unique_facilities.append(facility)
            else:
                print(f"🔄 Removing duplicate: {facility['name']} (ID: {facility['id']})")
        
        filtered_facilities = unique_facilities
        print(f"📊 After removing duplicates: {len(filtered_facilities)} unique facilities")
        
        # Sort by constraint score (highest first)
        filtered_facilities.sort(key=lambda x: x.get("constraint_score", 0), reverse=True)
        
        # Create a strict prompt that forces LLM to use ONLY database data
        facilities_json = json.dumps(filtered_facilities, indent=2)
        
        # Analyze the user query to determine intent
        query_lower = req.query.lower()
        query_intent = ""
        
        if any(word in query_lower for word in ['study', 'quiet', 'reading', 'research', 'work', 'library']):
            query_intent = "STUDY/WORK"
        elif any(word in query_lower for word in ['discuss', 'meeting', 'group', 'collaboration', 'team']):
            query_intent = "DISCUSSION/MEETING"
        elif any(word in query_lower for word in ['eat', 'food', 'lunch', 'dinner', 'meal', 'restaurant', 'cuisine']):
            query_intent = "FOOD/DINING"
        elif any(word in query_lower for word in ['drink', 'beverage', 'coffee', 'tea', 'bubble tea', 'thirsty']):
            query_intent = "BEVERAGE/DRINKS"
        elif any(word in query_lower for word in ['toilet', 'washroom', 'bathroom', 'restroom']):
            query_intent = "TOILET/RESTROOM"
        else:
            query_intent = "GENERAL"
        
        # Create a strict validation list
        valid_facility_names = [f["name"] for f in filtered_facilities]
        valid_names_str = ", ".join([f'"{name}"' for name in valid_facility_names])
        
        prompt = f"""You are a facility recommendation assistant. You MUST ONLY recommend facilities from the provided list below.

USER QUERY: "{req.query}"
DETECTED USER INTENT: {query_intent}

AVAILABLE FACILITIES (from database):
{facilities_json}

STRICT RULES:
1. You can ONLY recommend facilities that appear in the list above
2. Valid facility names are: {valid_names_str}
3. Do NOT create, invent, or suggest any facilities not in this exact list
4. If no facilities match, say "No facilities available that match your criteria"
5. Each facility can only appear ONCE in your response

TASK: From the facilities listed above, select the most relevant ones for the user's query.

FORMAT: Return ONLY a numbered list like this:
1. [Exact Facility Name], [Exact Building], Floor [Floor], Unit [Unit] (if exists)
2. [Exact Facility Name], [Exact Building], Floor [Floor], Unit [Unit] (if exists)

VALIDATION: Before responding, verify every facility name exists in the provided list.

Response:"""

        try:
            # Use the LLM to process the query and generate recommendations
            if '_ask_model' in globals():
                print(f"🤖 Calling LLM with model: llama3.1:8b")
                response = _ask_model("llama3.1:8b", prompt)
                print(f"🤖 Raw LLM Response: {repr(response)}")  # Use repr to see exact content
                print(f"🤖 LLM Response Type: {type(response)}")
                print(f"🤖 LLM Response Length: {len(response) if response else 0}")
            else:
                print("⚠️ LLM not available, using fallback")
                response = "LLM service is not available. Please try again later."
            
            # Clean the response to ensure it's just the numbered list
            cleaned_response = response.strip()
            print(f"🧹 Cleaned Response: {repr(cleaned_response)}")
            
            # ✅ VALIDATE LLM RESPONSE - Remove any facilities not in our database
            print("🔍 Validating LLM response against database...")
            valid_facility_names = {f["name"].lower() for f in filtered_facilities}
            
            # Parse LLM response and validate each line
            response_lines = cleaned_response.split('\n')
            validated_lines = []
            
            for line in response_lines:
                if not line.strip():
                    continue
                    
                # Extract facility name from numbered list (e.g., "1. Lee Wee Nam Library, ...")
                if '. ' in line:
                    try:
                        facility_part = line.split('. ', 1)[1]  # Get everything after "1. "
                        facility_name = facility_part.split(',')[0].strip()  # Get name before first comma
                        
                        if facility_name.lower() in valid_facility_names:
                            validated_lines.append(line)
                            print(f"   ✅ Valid: {facility_name}")
                        else:
                            print(f"   ❌ INVALID (not in database): {facility_name}")
                    except:
                        print(f"   ⚠️ Could not parse line: {line}")
                        
            if validated_lines:
                # Re-number the validated lines
                final_response = ""
                for i, line in enumerate(validated_lines, 1):
                    # Remove old number and add new one
                    if '. ' in line:
                        content = line.split('. ', 1)[1]
                        final_response += f"{i}. {content}\n"
                    else:
                        final_response += f"{i}. {line}\n"
                        
                final_response = final_response.strip()
                print(f"✅ Validated response with {len(validated_lines)} facilities from database")
            else:
                # No valid facilities - use fallback
                print("❌ LLM returned no valid facilities from database - using fallback")
                final_response = "No facilities available that match your criteria from our database."
            
            # Create the final result
            final_result = {"recommendation": final_response}
            
            # ===== OUTGOING RESPONSE LOGGING =====
            print("=" * 60)
            print("📤 SENDING RESPONSE TO FRONTEND")
            print("=" * 60)
            print(f"📦 Response Type: SUCCESS (LLM)")
            print(f"📝 Response Data: {final_result}")
            print(f"📏 Response Length: {len(cleaned_response)} characters")
            print(f"📋 First 200 chars: {cleaned_response[:200]}...")
            print("=" * 60)
            
            return final_result
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")  # Debug logging
            # Fallback to basic filtering if LLM fails
            print(f"LLM failed: {e}")
            
            # Use the already filtered facilities from constraint checking
            if filtered_facilities:
                # Format as numbered list using the constraint-filtered facilities
                result_lines = []
                for i, facility in enumerate(filtered_facilities[:10], 1):
                    line = f"{i}. {facility['name']}"
                    if facility['building']:
                        line += f", {facility['building']}"
                    if facility['floor']:
                        line += f", Floor {facility['floor']}"
                    if facility['unit_number']:
                        line += f", Unit {facility['unit_number']}"
                    line += f" (Score: {facility.get('constraint_score', 0)})"
                    result_lines.append(line)
                
                fallback_result = {"recommendation": "\n".join(result_lines)}
                
                # ===== OUTGOING RESPONSE LOGGING (FALLBACK) =====
                print("=" * 60)
                print("📤 SENDING RESPONSE TO FRONTEND")
                print("=" * 60)
                print(f"📦 Response Type: FALLBACK (Constraint-based)")
                print(f"📝 Response Data: {fallback_result}")
                print(f"📊 Filtered Facilities Count: {len(filtered_facilities)}")
                print("=" * 60)
                
                return fallback_result
            else:
                # No facilities meet constraints
                no_results = {"recommendation": "No facilities found that match your requirements. Please try adjusting your criteria."}
                
                print("=" * 60)
                print("📤 SENDING RESPONSE TO FRONTEND")
                print("=" * 60)
                print("📦 Response Type: NO RESULTS")
                print("❌ No facilities match the specified constraints")
                print("=" * 60)
                
                return no_results

    except Exception as e:
        error_details = f"Server error: {str(e)}"
        
        # ===== OUTGOING ERROR RESPONSE LOGGING =====
        print("=" * 60)
        print("📤 SENDING ERROR RESPONSE TO FRONTEND")
        print("=" * 60)
        print(f"📦 Response Type: ERROR (500)")
        print(f"❌ Error Details: {error_details}")
        print(f"🐛 Exception Type: {type(e).__name__}")
        print("=" * 60)
        
        raise HTTPException(status_code=500, detail=error_details)

class FacilityCreate(BaseModel):
    code: Optional[str] = None
    name: str
    type: str
    building: Optional[str] = None
    floor: Optional[int] = None
    attrs: Optional[Dict[str, Any]] = None
    geom: Optional[str] = None
    open_time: Optional[str] = None  # Will be converted to time
    close_time: Optional[str] = None  # Will be converted to time
    open_days: Optional[List[str]] = None
    unit_number: Optional[str] = None


@app.get("/facilities")
def get_all_facilities(db: Session = Depends(get_db)):
    """Get all facilities from the database"""
    facilities = db.query(Facility).all()
    return {"facilities": [
        {
            "id": facility.id,
            "code": facility.code,
            "name": facility.name,
            "type": facility.type,
            "building": facility.building,
            "floor": facility.floor,
            "attrs": facility.attrs,
            "geom": facility.geom,
            "open_time": str(facility.open_time) if facility.open_time else None,
            "close_time": str(facility.close_time) if facility.close_time else None,
            "open_days": facility.open_days,
            "unit_number": facility.unit_number
        } for facility in facilities
    ]}

@app.get("/facilities/{facility_id}")
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    """Get a specific facility by ID"""
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    return {
        "id": facility.id,
        "code": facility.code,
        "name": facility.name,
        "type": facility.type,
        "building": facility.building,
        "floor": facility.floor,
        "attrs": facility.attrs,
        "geom": facility.geom,
        "open_time": str(facility.open_time) if facility.open_time else None,
        "close_time": str(facility.close_time) if facility.close_time else None,
        "open_days": facility.open_days,
        "unit_number": facility.unit_number
    }


# ----------------------------
# Ollama / LangChain chatbot
# ----------------------------


class ChatRequest(BaseModel):
    query: str
    model: Optional[str] = "llama3.1:8b"
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


def _call_ollama_via_cli(model: str, prompt: str, timeout: int = 30) -> str:
    """Fallback: call the local `ollama` CLI. Returns model output as text."""
    import subprocess

    try:
        proc = subprocess.run(["ollama", "run", model, prompt], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise RuntimeError("`ollama` executable not found. Install Ollama and ensure it's on PATH.") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Ollama CLI timed out") from e

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ollama exited with code {proc.returncode}")

    return proc.stdout.strip()


# Prefer LangChain's Ollama wrapper if available
try:
    from langchain_ollama import OllamaLLM  # Newer, more stable package

    def _ask_ollama_with_langchain(model: str, prompt: str) -> str:
        try:
            llm = OllamaLLM(model=model)
            return llm.invoke(prompt)
        except Exception as e:
            # fallback to CLI and log the error
            import logging
            logging.getLogger(__name__).warning("LangChain Ollama call failed: %s; falling back to CLI", e)
            return _call_ollama_via_cli(model, prompt)

    _ask_model = _ask_ollama_with_langchain
except Exception as e:
    print("LangChain Ollama failed, falling back to CLI")
    print("Error:", e)
    _ask_model = _call_ollama_via_cli
    


@app.post("/recommend_llm")
def recommend_llm(req: ChatRequest):
    """Chat-like endpoint that sends `query` to an Ollama model and returns the response.

    Note: This uses LangChain's Ollama integration when available, otherwise falls back to calling
    the `ollama` CLI. The existing `/recommend` endpoint (facility recommendations) is left intact.
    """
    print(f"🤖 POST /recommend_llm received! Query: '{req.query}'")
    
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="query must be a non-empty string")

    print("chat request query: ", req.query)
    try:
        answer = _ask_model(req.model, req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    print("answer: ", answer)
    return {"answer": answer}