"""
OpenAI GPT-4 Powered Semantic Chat Service for NTU Facilities
Replaces Ollama with OpenAI GPT-4 for better response quality
"""

from typing import List, Dict, Any, Optional
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from .vector_db_service import FacilityVectorDB

class OpenAISemanticChatService:
    def __init__(self):
        """Initialize semantic chat service with OpenAI GPT-4 and vector database"""
        # Load environment variables
        load_dotenv()
        
        self.vector_db = FacilityVectorDB()
        
        # Initialize OpenAI client
        # Make sure to set your OPENAI_API_KEY environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it with your OpenAI API key."
            )
        
        self.openai_client = OpenAI(api_key=api_key)
        print("🤖 OpenAI GPT-4 client initialized")
        
    def process_query(self, user_query: str, max_results: int = 5, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Process user query using semantic search + OpenAI GPT-4 with conversation context"""
        
        print(f"💬 Processing query with OpenAI GPT-4: '{user_query}'")
        if conversation_history:
            print(f"📝 Conversation history: {len(conversation_history)} previous messages")
        
        # Step 1: Extract day information from enhanced query
        query_day = self._extract_day_from_query(user_query)
        
        # Step 2: Semantic search in vector database using enhanced query
        semantic_results = self.vector_db.semantic_search(
            query=user_query, 
            n_results=max_results * 3  # Get more candidates for better filtering
        )

        print(f"🔍 Retrieved {semantic_results} initial semantic search results")

        # Step 3: Generate conversational response using OpenAI GPT-4 with conversation context
        try:
            response = self._generate_openai_response_with_context(user_query, semantic_results, query_day, conversation_history) 
        except Exception as e:
            print(f"⚠️  Error generating OpenAI response: {e}")
            response = self._generate_fallback_response_with_context(user_query, semantic_results, conversation_history)

        return {
            'response': response,
            'query_processed': user_query,
            'original_query': user_query,
            'query_day': query_day,
            'llm_provider': 'openai_gpt4',
            'conversation_context': len(conversation_history) if conversation_history else 0
        }
    
    def _extract_day_from_query(self, query: str) -> str:
        """Extract day information from user query"""
        query_lower = query.lower()
        
        # Map day variations to standard format
        day_mapping = {
            'monday': 'Monday', 'mon': 'Monday',
            'tuesday': 'Tuesday', 'tue': 'Tuesday', 'tues': 'Tuesday',
            'wednesday': 'Wednesday', 'wed': 'Wednesday',
            'thursday': 'Thursday', 'thu': 'Thursday', 'thur': 'Thursday', 'thurs': 'Thursday',
            'friday': 'Friday', 'fri': 'Friday',
            'saturday': 'Saturday', 'sat': 'Saturday',
            'sunday': 'Sunday', 'sun': 'Sunday',
            'weekend': 'Weekend', 'weekends': 'Weekend',
            'weekday': 'Weekday', 'weekdays': 'Weekday'
        }
        
        # Check for day mentions in query
        for day_variant, standard_day in day_mapping.items():
            if day_variant in query_lower:
                print(f"🗓️  Detected day: {standard_day} from query")
                return standard_day
        
        return None
    
    # def _filter_relevant_results(self, results: List[Dict], query: str, query_day: str = None) -> List[Dict]:
        """Apply intelligent relevance filtering based on distance, query analysis, and day availability"""
        
        # For debugging: show all distances
        for r in results[:5]:
            print(f"Debug: {r.get('name', 'Unknown')} ({r.get('type', 'unknown')}) - Distance: {r.get('distance', 0):.3f}")
        
        # Step 1: Remove duplicates based on facility name and type
        unique_facilities = self._remove_duplicate_facilities(results, query_day)
        
        # Step 2: Apply distance-based filtering
        query_lower = query.lower()
        
        # Dynamic distance threshold based on query type
        if any(word in query_lower for word in ['study', 'quiet', 'library', 'work']):
            # For study queries, be more selective
            max_distance = 1.4
            # Prefer study areas and libraries
            study_types = ['study_area', 'study area', 'library']
            relevant = []
            for r in unique_facilities:
                if r.get('distance', float('inf')) <= max_distance:
                    facility_type = r.get('type', '').replace('_', ' ').lower()
                    # Boost study-related facilities
                    if any(st in facility_type for st in study_types):
                        relevant.append(r)
                    elif r.get('distance', float('inf')) <= 1.2:  # Only very close matches for non-study facilities
                        relevant.append(r)
        elif any(word in query_lower for word in ['eat', 'food', 'hungry', 'meal', 'lunch', 'dinner', 'breakfast']):
            # For food queries, prioritize actual food establishments over beverages,
            # incorporate healthy-food awareness and North/South Spine preference.
            max_distance = 1.6

            def is_beverage_place(name: str, ftype: str) -> bool:
                name_l = (name or '').lower()
                ftype_l = (ftype or '').lower()
                beverage_keywords = [
                    'tea', 'milk tea', 'bubble', 'boba', 'coffee', 'espresso', 'latte', 'brew', 'juice', 'smoothie',
                    'each a cup', 'chicha', 'starbucks', 'coffee bean', 'gong cha', 'koi'
                ]
                return ftype_l == 'beverage' or any(k in name_l for k in beverage_keywords)

            def is_food_place(name: str, ftype: str) -> bool:
                if is_beverage_place(name, ftype):
                    return False
                ftype_l = (ftype or '').lower()
                name_l = (name or '').lower()
                food_keywords = [
                    'food', 'restaurant', 'canteen', 'kitchen', 'cuisine', 'express', 'stall', 'noodle', 'rice',
                    'pasta', 'soup', 'union', 'grill', 'bbq', 'hawker', 'meals', 'dining', 'bistro', 'eatery'
                ]
                return ftype_l == 'food' or any(k in name_l for k in food_keywords)

            def healthy_score(name: str) -> int:
                # Higher score = healthier
                nl = (name or '').lower()
                healthy_hits = [
                    'soup', 'salad', 'grill', 'grilled', 'steam', 'steamed', 'bowl', 'grain', 'lean', 'yong tau foo',
                    'subway', 'poke', 'japanese', 'mediterranean'
                ]
                unhealthy_hits = ['fried', 'bbq', 'burger', 'bakery', 'dessert', 'cake', 'cream']
                score = 0
                if any(k in nl for k in healthy_hits):
                    score += 1
                if any(k in nl for k in unhealthy_hits):
                    score -= 1
                return score

            def spine_boost(building: str) -> int:
                bl = (building or '').lower()
                return 1 if ('north spine' in bl or 'south spine' in bl) else 0

            # Filter by distance first
            candidates = [r for r in unique_facilities if r.get('distance', float('inf')) <= max_distance]

            # Keep only food places primarily
            food_candidates = [r for r in candidates if is_food_place(r.get('name'), r.get('type'))]
            beverage_candidates = [r for r in candidates if is_beverage_place(r.get('name'), r.get('type'))]

            # Sort with custom scoring: by distance, then spine preference, then healthy if requested
            is_healthy_query = any(word in query_lower for word in ['healthy', 'clean', 'light'])
            def sort_key(r: Dict[str, Any]):
                # Lower is better; use negative boosts to improve rank
                base = r.get('distance', float('inf'))
                boost = 0
                boost -= 0.2 * spine_boost(r.get('building'))
                if is_healthy_query:
                    boost -= 0.2 * healthy_score(r.get('name'))
                return base + boost

            food_candidates.sort(key=sort_key)
            relevant = list(food_candidates)

            # Only include beverages if we have too few food choices
            if len(relevant) < 2 and beverage_candidates:
                beverage_candidates.sort(key=lambda r: r.get('distance', float('inf')))
                relevant.extend(beverage_candidates[:2])  # Limit beverage suggestions
        else:
            # For other queries, use standard threshold
            max_distance = 1.6
            relevant = [r for r in unique_facilities if r.get('distance', float('inf')) <= max_distance]
        
        # Step 3: Apply day-based filtering if a specific day was mentioned
        if query_day:
            relevant = self._filter_by_day_availability(relevant, query_day)

        # Sort by distance as a final stable sort
        relevant.sort(key=lambda x: x.get('distance', float('inf')))

        day_info = f" (filtered for {query_day})" if query_day else ""
        print(f"🎯 Filtered to {len(relevant)} relevant facilities{day_info} (max_distance: {max_distance}) for query type: {query_lower[:30]}...")
        return relevant
    
    # def _remove_duplicate_facilities(self, facilities: List[Dict], query_day: str = None) -> List[Dict]:
        """Remove duplicate facilities, keeping the best match for the query day"""
        if not facilities:
            return []
        
        # Group facilities by name and type
        facility_groups = {}
        for facility in facilities:
            key = (facility.get('name', ''), facility.get('type', ''))
            if key not in facility_groups:
                facility_groups[key] = []
            facility_groups[key].append(facility)
        
        unique_facilities = []
        
        for (name, facility_type), group in facility_groups.items():
            if len(group) == 1:
                # No duplicates, add as is
                unique_facilities.append(group[0])
            else:
                # Multiple entries - choose best one for query day
                best_facility = self._select_best_facility_for_day(group, query_day)
                if best_facility:
                    unique_facilities.append(best_facility)
                    print(f"🔄 Removed {len(group)-1} duplicates for {name}")
        
        return unique_facilities
    
    # def _select_best_facility_for_day(self, facilities: List[Dict], query_day: str = None) -> Dict:
        """Select the best facility entry from duplicates based on day availability"""
        
        if not query_day:
            # If no specific day, return the one with better distance or first one
            return min(facilities, key=lambda x: x.get('distance', float('inf')))
        
        # Check which entries are available for the query day
        available_for_day = []
        
        for facility in facilities:
            open_days = facility.get('open_days', [])
            open_time = facility.get('open_time')
            close_time = facility.get('close_time')
            
            # If no timing info, assume open all day
            if not open_days and not open_time and not close_time:
                available_for_day.append(facility)
                continue
            
            # If has timing but no open_days, assume available daily
            if not open_days and (open_time or close_time):
                available_for_day.append(facility)
                continue
            
            # Check specific day availability
            if query_day in open_days:
                available_for_day.append(facility)
        
        if available_for_day:
            # Return the best available facility (best distance)
            return min(available_for_day, key=lambda x: x.get('distance', float('inf')))
        else:
            # None available for the day, don't include any
            print(f"❌ All entries for {facilities[0].get('name', 'Unknown')} closed on {query_day}")
            return None
    
    # def _filter_by_day_availability(self, facilities: List[Dict], query_day: str) -> List[Dict]:
        """Filter facilities based on day availability"""
        if not query_day:
            return facilities
        
        available_facilities = []
        filtered_count = 0
        
        for facility in facilities:
            open_days = facility.get('open_days', [])
            open_time = facility.get('open_time')
            close_time = facility.get('close_time')
            
            # IMPORTANT: If no timing info specified, assume facility is open all day
            if not open_days and not open_time and not close_time:
                print(f"✅ {facility.get('name', 'Unknown')} - assumed open all day (no timing specified)")
                available_facilities.append(facility)
                continue
            
            # If only open_days is empty but has timing, include facility (might be open daily)
            if not open_days and (open_time or close_time):
                print(f"✅ {facility.get('name', 'Unknown')} - has timing info, assuming available on {query_day}")
                available_facilities.append(facility)
                continue
            
            # Check if facility is open on the specified day
            is_open = False
            
            if query_day == 'Weekend':
                is_open = any(day in open_days for day in ['Saturday', 'Sunday'])
            elif query_day == 'Weekday':
                is_open = any(day in open_days for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
            else:
                is_open = query_day in open_days
            
            if is_open:
                available_facilities.append(facility)
            else:
                filtered_count += 1
                print(f"🚫 Filtered out {facility.get('name', 'Unknown')} - closed on {query_day}")
        
        if filtered_count > 0:
            print(f"📅 Day filtering: {filtered_count} facilities filtered out for {query_day}")
        
        return available_facilities
    
    def _generate_openai_response_with_context(self, query: str, facilities: List[Dict], query_day: Optional[str] = None, conversation_history: List[Dict] = None) -> str:
        
        """Generate conversational response using OpenAI GPT-4 with conversation context"""

        conversation_context = ""
        
        # Build conversation context for GPT-4
        if conversation_history:
            recent_messages = conversation_history[-4:]  # Last 4 messages for context
            context_parts = []
            for msg in recent_messages:
                role = "Human" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')
                context_parts.append(f"{role}: {content}")
            
            if context_parts:
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\n"

        facility_details = []
        for facility in facilities:
            details = [
                f"Name: {facility.get('name', 'Unknown')}",
                f"Type: {facility.get('type', 'Unknown')}",
                f"Building: {facility.get('building', 'Unknown')}",
                f"Unit Number: {facility.get('unit_number', 'Unknown')}",
                f"Open Time: {facility.get('open_time', 'N/A')}",
                f"Close Time: {facility.get('close_time', 'N/A')}",
                f"Open Days: {', '.join(facility.get('open_days', [])) if facility.get('open_days') else 'N/A'}",
                f"map_url: {facility.get('map_url', 'Not Found')}"
            ]
            
            attrs = facility.get('attrs', {})
            if attrs:
                airconditioned = attrs.get('airconditioned', 'Unknown')
                details.append(f"Aircon: {airconditioned}")
                
                booking = attrs.get('booking_required', 'Unknown')
                details.append(f"Booking Required: {booking if attrs.get('booking_link') else 'No'}")
                
                monitor = attrs.get('monitor', 'No')
                details.append(f"Monitor Available: {monitor}")
               
                quiet_policy = attrs.get('quiet_policy', 'N/A')
                details.append(f"Quiet Policy: {quiet_policy}")
                
                power_outlets = attrs.get('power_outlets', 'N/A')
                details.append(f"Power Outlets: {power_outlets}")
                
                cuisine = attrs.get('cuisine', 'N/A')
                details.append(f"Cuisine: {cuisine}")
                
                dine_in = attrs.get('dine_in', 'N/A')
                details.append(f"Dine-In Available: {dine_in}")
                
                takeaway = attrs.get('takeaway_friendly', 'N/A')
                details.append(f"Takeaway Available: {takeaway}")
                
                dish_style = attrs.get('dish_style', 'N/A')
                details.append(f"Dish Style: {dish_style}")
                
                dietry_label = attrs.get('dietary_label', 'N/A')
                details.append(f"Dietary Label: {dietry_label}")    
               
                takeaway_friendly = attrs.get('takeaway_friendly', 'N/A')
                details.append(f"Takeaway Available: {takeaway_friendly}")
               
                serves_breakfast = attrs.get('serves_breakfast', 'N/A')
                details.append(f"Serve Breakfast: {serves_breakfast}")

                healthy_options_available = attrs.get('healthy_options_available', 'N/A')
                details.append(f"Healthy Option Available: {healthy_options_available}")
            
            facility_details.append(" | ".join(details))
        facilities_context = "\n".join(facility_details) if facility_details else "No specific facilities found."

        system_prompt = f"""You are an intelligent NTU Singapore campus assistant with access to comprehensive knowledge from multiple domains. Provide seamless, unified recommendations by combining database results with your general knowledge about NTU and nutrition science. Avoid claiming specific outlet names or canteen numbers unless they appear in the provided facility list.

            Context: Facilities (result from semantic search): {facilities_context} and previous conversation context: {conversation_context}

            COMPREHENSIVE INTELLIGENCE APPROACH:
            • Database results + NTU campus knowledge + General domain expertise
            • Apply your knowledge of nutrition, food science, study habits, facilities management
            • Use your understanding of what makes food healthy/unhealthy, good study environments, etc.
            • Give ONE coherent response - don't separate sources or mention where information came from
            • Prioritize QUALITY, HEALTH, and RELEVANCE over just using available data
            ENHANCED ANALYSIS WITH GENERAL KNOWLEDGE:
            1. **Food Classification & Prioritization Intelligence**:
            - FOOD vs BEVERAGE: When user asks for "food" or "eat", prioritize actual FOOD establishments over beverage shops
            - FOOD places: Restaurants, cafeterias, food courts, stalls serving meals (pasta, rice, noodles, soup, etc.)
            - BEVERAGE places: Bubble tea shops, coffee shops, juice bars
            - If user asks "where can I eat", focus on places that serve substantial meals, not just drinks
            - Apply your knowledge of healthy vs. unhealthy food types
            - Understand that "healthy food" means: salads, grilled items, soups, lean proteins, vegetables, fruits
            - Consider nutritional value, preparation methods, and ingredients
            - Use your knowledge of dietary restrictions (halal, vegetarian, gluten-free)

            2. **NTU Campus Knowledge Integration (safe usage)**:
            - North Spine and South Spine are key hubs with multiple amenities and eateries
            - Prefer options in North/South Spine when making meal recommendations if suitable
            - Use general campus knowledge (e.g., main spines often have food courts/restaurants),
            but do NOT invent or assert specific outlet names or canteen numbers unless they are in the provided list
            - Consider practical factors: walking distance, meal prices, student preferences
            - Apply your knowledge of optimal study conditions: quiet, good lighting, minimal distractions

            3. **Facility Quality Assessment**:
            - Use your knowledge of what makes facilities high-quality
            - Understand cleanliness standards, accessibility, comfort factors
            - Apply knowledge of peak hours, crowd management, facility maintenance

            4. **Day-Based Intelligence**:
            - Only suggest facilities that are actually open on the specified day
            - Completely ignore closed facilities - don't mention them at all
            - Show only operating hours relevant to the queried day

            RESPONSE REQUIREMENTS:
            • Give seamless, integrated recommendations using all your knowledge domains
            • Don't say "from database" or "from my knowledge" - just give the best expert advice
            • Only name facilities that are in the AVAILABLE FACILITIES list; if using general knowledge, speak in categories (e.g., "food court options", "study pods")
            • Apply your general knowledge to critically evaluate database suggestions
            • Lead with the most appropriate recommendations based on quality and suitability
            • Show only relevant operating hours for the queried day
            • Completely ignore inappropriate or closed facilities
            • For food queries: Prioritize actual FOOD places over beverage shops
            • Sound natural and conversational like a knowledgeable friend helping out
            • **If a facility includes a `map_url` (navigation link), include it in your response as a clickable link at the end of that facility’s description (e.g., “📍 [View on map](https://maps.ntu.edu.sg/...)”).**
            • Do not fabricate links; only include them when the `map_url` field is provided.

            Today's Context: {query_day if query_day else 'Current day'} - only show information relevant to this day."""
        
        print("System prompt: ", system_prompt)

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            return self._generate_fallback_response_with_context(query, facilities, conversation_history)
    
    def _generate_fallback_response_with_context(self, query, facilities, conversation_history):
     return "Sorry, something went wrong while generating the response. Please try again later."

    def load_facilities_from_db(self, db_facilities: List[Dict], update_mode: str = "replace"):
        """
        Load facilities from your PostgreSQL database into vector database
        
        Args:
            db_facilities: List of facility dictionaries from database
            update_mode: "replace" (clear and reload) or "add" (append only)
        """
        print(f"Loading {len(db_facilities)} facilities into vector database (mode: {update_mode})...")
        
        # If replace mode, clear existing data first
        if update_mode == "replace":
            print("Clearing existing vector database data...")
            self.vector_db.reset_database()
        
        # Transform database format if needed
        processed_facilities = []
        for facility in db_facilities:
            processed = {
                'id': facility.get('id'),
                'code': facility.get('code'),
                'name': facility.get('name'),
                'type': facility.get('type'),
                'building': facility.get('building'),
                'floor': facility.get('floor'),
                'unit_number': facility.get('unit_number'),
                'attrs': facility.get('attrs', {}),
                'open_time': str(facility.get('open_time')) if facility.get('open_time') else '',
                'close_time': str(facility.get('close_time')) if facility.get('close_time') else '',
                'open_days': facility.get('open_days', []),
                'map_url': facility.get('map_url', '')
            }
            processed_facilities.append(processed)
        
        # Add to vector database
        self.vector_db.add_facilities(processed_facilities)
        print(f"✅ Successfully loaded {len(processed_facilities)} facilities with OpenAI integration")
        
        return {
            "message": f"Loaded {len(processed_facilities)} facilities into vector database",
            "facilities_count": len(processed_facilities),
            "llm_provider": "openai_gpt4"
        }


# For backward compatibility, create an alias
SemanticChatService = OpenAISemanticChatService