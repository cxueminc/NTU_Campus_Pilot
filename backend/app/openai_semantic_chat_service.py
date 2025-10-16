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
        
        # Step 1: Enhance query with conversation context if available
        enhanced_query = self._enhance_query_with_context(user_query, conversation_history)
        
        # Step 2: Extract day information from enhanced query
        query_day = self._extract_day_from_query(enhanced_query)
        
        # Step 3: Semantic search in vector database using enhanced query
        semantic_results = self.vector_db.semantic_search(
            query=enhanced_query, 
            n_results=max_results * 3  # Get more candidates for better filtering
        )
        
        # Step 4: Apply smarter relevance and day-based filtering
        relevant_facilities = self._filter_relevant_results(semantic_results, enhanced_query, query_day)
        
        # Step 5: Take top results
        top_facilities = relevant_facilities[:max_results]
        
        # Step 6: Generate conversational response using OpenAI GPT-4 with conversation context
        if top_facilities:
            response = self._generate_openai_response_with_context(
                user_query, top_facilities, query_day, conversation_history
            )
        else:
            response = self._generate_no_results_response_with_context(user_query, conversation_history)
        
        return {
            'response': response,
            'retrieved_facilities': top_facilities,  # Match test script expectation
            'facilities': top_facilities,  # Keep for backward compatibility
            'total_found': len(relevant_facilities),
            'query_processed': enhanced_query,
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
    
    def _filter_relevant_results(self, results: List[Dict], query: str, query_day: str = None) -> List[Dict]:
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
    
    def _remove_duplicate_facilities(self, facilities: List[Dict], query_day: str = None) -> List[Dict]:
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
    
    def _select_best_facility_for_day(self, facilities: List[Dict], query_day: str = None) -> Dict:
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
    
    def _filter_by_day_availability(self, facilities: List[Dict], query_day: str) -> List[Dict]:
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
    
    def _enhance_query_with_context(self, user_query: str, conversation_history: List[Dict] = None) -> str:
        """Enhance the current query with context from conversation history"""
        if not conversation_history:
            return user_query
        
        # Extract relevant context from recent conversation
        context_items = []
        for msg in conversation_history[-3:]:  # Look at last 3 messages for context
            if msg.get('role') == 'user':
                # Look for food mentions, location preferences, etc.
                content = msg.get('content', '').lower()
                if any(word in content for word in ['pasta', 'pizza', 'burger', 'coffee', 'tea', 'food', 'eat', 'drink', 'hungry', 'thirsty']):
                    context_items.append(f"User mentioned: {msg.get('content')}")
        
        if context_items:
            enhanced_query = f"{user_query} [Context from conversation: {'; '.join(context_items)}]"
            print(f"🔗 Enhanced query with context: '{enhanced_query}'")
            return enhanced_query
        
        return user_query
    
    def _generate_openai_response_with_context(self, query: str, facilities: List[Dict], query_day: Optional[str] = None, conversation_history: List[Dict] = None) -> str:
        """Generate conversational response using OpenAI GPT-4 with conversation context"""

        # Build conversation context for GPT-4
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-4:]  # Last 4 messages for context
            context_parts = []
            for msg in recent_messages:
                role = "Human" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')
                context_parts.append(f"{role}: {content}")
            
            if context_parts:
                conversation_context = "Previous conversation:\n" + "\n".join(context_parts) + "\n\n"

        # Create enhanced context for OpenAI GPT-4
        facility_details = []
        for facility in facilities:
            details = [
                f"**{facility.get('name', 'Unknown')}**",
                f"Type: {facility.get('type', 'Unknown')}",
                f"Building: {facility.get('building', 'Unknown')}",
                f"Location: {facility.get('location', 'Unknown')}"
            ]
            
            # Add operating hours if available
            if facility.get('operating_hours'):
                details.append(f"Hours: {facility['operating_hours']}")
            
            facility_details.append(" | ".join(details))

        facilities_text = "\n".join(facility_details) if facility_details else "No specific facilities found."

        # Enhanced system prompt with conversation awareness
        system_prompt = f"""You are a helpful NTU campus assistant with perfect knowledge of the campus. You maintain conversation context and provide personalized recommendations.

{conversation_context}Current query: "{query}"

Available facilities:
{facilities_text}

Guidelines:
- Maintain conversation continuity - reference previous topics when relevant
- If user previously mentioned food preferences (like pasta), connect current recommendations to those preferences
- Be conversational and remember what the user said before
- Provide specific, actionable information
- Include operating hours when available
- Give directions or building information when helpful
- If this seems related to previous conversation, acknowledge that connection
- Keep responses natural and friendly

Respond conversationally:"""

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

    def _generate_no_results_response_with_context(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Generate a helpful no-results response with conversation context"""
        
        conversation_context = ""
        if conversation_history:
            # Look for what user was talking about before
            for msg in conversation_history[-2:]:
                if msg.get('role') == 'user':
                    content = msg.get('content', '').lower()
                    if any(word in content for word in ['pasta', 'pizza', 'burger', 'coffee', 'tea', 'food']):
                        conversation_context = f"I know you were interested in {content.split()[-1]} earlier. "
                        break

        base_response = f"{conversation_context}I couldn't find specific facilities matching '{query}' in our NTU database. "
        
        suggestions = [
            "Try asking about 'food places near [building name]'",
            "Search for 'study areas in [specific school]'", 
            "Look for 'coffee shops' or 'restaurants'",
            "Ask about facilities in specific buildings like 'North Spine' or 'South Spine'"
        ]
        
        return base_response + "Here are some suggestions:\n• " + "\n• ".join(suggestions)

    def _generate_fallback_response_with_context(self, query: str, facilities: List[Dict], conversation_history: List[Dict] = None) -> str:
        """Generate a simple fallback response when OpenAI is unavailable, with conversation context"""
        
        conversation_context = ""
        if conversation_history:
            for msg in conversation_history[-1:]:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if any(word in content.lower() for word in ['pasta', 'pizza', 'food', 'eat']):
                        conversation_context = "Following up on your food interests, "
                        break

        if facilities:
            facility_list = []
            for f in facilities[:3]:  # Limit to top 3
                name = f.get('name', 'Unknown')
                building = f.get('building', 'Unknown building')
                facility_list.append(f"• {name} ({building})")
            
            return f"{conversation_context}Here are some NTU facilities I found:\n\n" + "\n".join(facility_list)
        else:
            return f"{conversation_context}I couldn't find specific facilities for your query, but I'm here to help you find what you need at NTU!"
    
    def _generate_openai_response(self, query: str, facilities: List[Dict], query_day: Optional[str] = None) -> str:
        """Generate conversational response using OpenAI GPT-4 with enhanced knowledge integration"""

        # Create context for OpenAI GPT-4 with day-specific information
        facilities_context: List[str] = []
        for i, facility in enumerate(facilities, 1):
            attrs = facility.get('attrs', {}) or {}
            available_features = [k for k, v in attrs.items() if v]

            # Convert distance to a more intuitive relevance score (lower distance = higher relevance)
            relevance = max(0.0, 1 - (float(facility.get('distance', 2.0)) / 2.0))

            # Create day-specific schedule information
            schedule_info = self._get_day_specific_schedule(facility, query_day)

            context = f"""
            {i}. {facility['name']}
            - Location: {facility.get('building', 'N/A')}, Floor {facility.get('floor', 'N/A')}
            - Type: {facility.get('type', 'N/A')}
            - Features: {', '.join(available_features) if available_features else 'Basic facilities'}
            - Schedule: {schedule_info}
            - Match Quality: {relevance:.2f}
            """
            facilities_context.append(context.strip())

        # Create enhanced system prompt for GPT-4 with unified knowledge approach
        system_prompt = f"""You are an intelligent NTU Singapore campus assistant with access to comprehensive knowledge from multiple domains. Provide seamless, unified recommendations by combining database results with your general knowledge about NTU and nutrition science. Avoid claiming specific outlet names or canteen numbers unless they appear in the provided facility list.

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
                        • Only name facilities that are in the AVAILABLE FACILITIES list; if using general knowledge, speak in categories (e.g., "food court options", "salad/grill stalls")
                        • Apply your general knowledge to critically evaluate database suggestions
                        • Lead with the most appropriate recommendations based on quality and suitability
                        • Show only relevant operating hours for the queried day
                        • Completely ignore inappropriate or closed facilities
                        • For food queries: Prioritize actual FOOD places over beverage shops
                        • Sound natural and conversational like a knowledgeable friend helping out

                        Today's Context: {query_day if query_day else 'Current day'} - only show information relevant to this day."""

        # Create enhanced user prompt with comprehensive analysis
        user_prompt = f"""STUDENT QUERY: "{query}"
                        Query Day: {query_day if query_day else 'No specific day mentioned'}

                        AVAILABLE FACILITIES:
                        {chr(10).join(facilities_context)}

                        COMPREHENSIVE ANALYSIS REQUIRED:
                        1. **Apply General Knowledge**: Use your expertise in nutrition, health, study science, facility management
                        2. **Quality Assessment**: Critically evaluate if these facilities actually meet the student's needs
                        3. **Health & Nutrition**: For food queries, apply your knowledge of what constitutes healthy eating
                        4. **Study Science**: For study queries, apply your knowledge of optimal learning environments
                        5. **Day-Based Filtering**: Only consider facilities open on the specified day
                        6. **Integration**: Combine database info with your broader knowledge for superior recommendations

                        SPECIFIC GUIDANCE:
                        • For "food/eat" queries: Focus on RESTAURANTS and FOOD establishments, not beverage shops
                        • For "healthy food": Look for salads, grilled items, soups, lean proteins - NOT bakeries or dessert places
                        • For "study spaces": Prioritize quiet, well-lit areas with good wifi - NOT busy food courts
                        • For cuisine types: Use your knowledge of different food cultures and typical dishes
                        • Add practical recommendations based on your NTU campus knowledge and general understanding

                        Provide expert-level recommendations using your comprehensive knowledge across all relevant domains. Be conversational and helpful like a knowledgeable friend who understands both NTU campus and general knowledge about food, health, and student needs."""

        try:
            # Call OpenAI GPT-4
            response = self._call_openai_gpt4(system_prompt, user_prompt)
            return response
        except Exception as e:
            print(f"❌ OpenAI GPT-4 generation failed: {e}")
            return self._generate_fallback_response(query, facilities)
    
    def _get_day_specific_schedule(self, facility: Dict, query_day: str = None) -> str:
        """Get schedule information specific to the queried day"""
        
        open_days = facility.get('open_days', [])
        open_time = facility.get('open_time')
        close_time = facility.get('close_time')
        
        # If no timing information, assume open all day
        if not open_days and not open_time and not close_time:
            return "Open all day"
        
        # If no query day specified, show full schedule
        if not query_day:
            if open_days and (open_time or close_time):
                days_str = ', '.join(open_days)
                time_str = f"{open_time or 'N/A'} - {close_time or 'N/A'}"
                return f"{days_str}: {time_str}"
            elif open_days:
                return ', '.join(open_days)
            elif open_time or close_time:
                return f"{open_time or 'N/A'} - {close_time or 'N/A'}"
            else:
                return "Schedule not specified"
        
        # Check if open on the specific query day
        is_open_today = False
        
        if query_day == 'Weekend':
            is_open_today = any(day in open_days for day in ['Saturday', 'Sunday'])
        elif query_day == 'Weekday':
            is_open_today = any(day in open_days for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        elif open_days:
            is_open_today = query_day in open_days
        else:
            # No open_days specified but has timing - assume open daily
            is_open_today = bool(open_time or close_time)
        
        if is_open_today:
            if open_time or close_time:
                return f"{query_day}: {open_time or 'N/A'} - {close_time or 'N/A'}"
            else:
                return f"Open on {query_day}"
        else:
            return f"Closed on {query_day}"
    
    def _call_openai_gpt4(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI GPT-4 for response generation"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for best quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,  # Limit response length
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.9,       # Focus on high probability tokens
                frequency_penalty=0.1,  # Slight penalty for repetition
                presence_penalty=0.1    # Encourage diverse vocabulary
            )
            
            # Extract the response content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    print(f"✅ OpenAI GPT-4 response generated ({len(content)} chars)")
                    return content.strip()
            
            raise Exception("No valid response content from OpenAI")
            
        except Exception as e:
            print(f"❌ OpenAI API call failed: {e}")
            raise e
    
    def _generate_fallback_response(self, query: str, facilities: List[Dict]) -> str:
        """Generate fallback response if OpenAI fails"""
        
        if not facilities:
            return "I couldn't find any facilities that match your request. Could you try rephrasing your question?"
        
        top_facility = facilities[0]
        response_parts = [
            f"Based on your search for '{query}', I found {len(facilities)} relevant options.",
            f"The best match is {top_facility['name']} in {top_facility['building']}."
        ]
        
        # Add features if available
        attrs = top_facility.get('attrs', {})
        features = [k for k, v in attrs.items() if v]
        if features:
            response_parts.append(f"It offers: {', '.join(features)}.")
        
        # Add schedule if available
        if top_facility.get('open_days'):
            days = ', '.join(top_facility['open_days'])
            times = f"{top_facility.get('open_time', '')} - {top_facility.get('close_time', '')}"
            response_parts.append(f"Open {days} from {times}.")
        
        response_parts.append("(Note: This is a fallback response - please check your OpenAI API configuration)")
        
        return " ".join(response_parts)
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate response when no relevant facilities found, using comprehensive knowledge"""
        
        try:
            system_prompt = """You are an expert NTU Singapore campus assistant with comprehensive knowledge across multiple domains. When database results are insufficient, leverage your extensive general knowledge.

                            COMPREHENSIVE KNOWLEDGE APPLICATION:
                            • Apply your knowledge of nutrition, health, study science, and facility management
                            • Use your understanding of optimal environments for different activities
                            • Apply your knowledge of food types, dietary requirements, and health considerations
                            • Use your expertise in study environments, productivity, and learning spaces

                            ENHANCED RESPONSE APPROACH:
                            1. Use your broad knowledge of what the student actually needs
                            2. Apply domain expertise (nutrition for food, environmental psychology for study spaces)
                            3. Suggest NTU facilities based on comprehensive understanding
                            4. Provide expert-level guidance using your general knowledge
                            5. Give practical, actionable recommendations

                            Don't just suggest random NTU buildings - use your expertise to understand what would truly help the student."""

            user_prompt = f"""QUERY: "{query}"

                            The database search returned no matching facilities for this query.

                            COMPREHENSIVE ANALYSIS REQUIRED:
                            1. **Domain Expertise**: Apply your knowledge from relevant fields:
                               - For food queries: nutrition science, dietary health, cuisine types
                               - For study queries: environmental psychology, learning optimization
                               - For facility queries: accessibility, comfort, functionality

                            2. **Practical Application**: Use your understanding of what the student truly needs:
                               - If seeking "healthy food": what nutrition science says is healthy
                               - If seeking "study space": what research shows about optimal learning environments
                               - If seeking "quiet areas": what acoustic science suggests

                            3. **NTU Campus Integration**: Apply this expertise to NTU-specific recommendations:
                               - Which campus areas would best meet these scientifically-informed needs
                               - How NTU facilities align with best practices in the relevant domain

                            Provide expert-level guidance that combines domain knowledge with NTU campus familiarity."""
                                        
            response = self._call_openai_gpt4(system_prompt, user_prompt)
            return response
            
        except Exception as e:
            print(f"❌ OpenAI no-results response failed: {e}")
            return f"I couldn't find specific facilities matching '{query}' in our database. Based on general NTU knowledge, you might want to check the main campus buildings, student centers, or ask at information counters for the most current information about available facilities."
    
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
                'name': facility.get('name'),
                'type': facility.get('type'),
                'building': facility.get('building'),
                'floor': facility.get('floor'),
                'unit_number': facility.get('unit_number'),
                'code': facility.get('code'),
                'attrs': facility.get('attrs', {}),
                'open_time': str(facility.get('open_time')) if facility.get('open_time') else '',
                'close_time': str(facility.get('close_time')) if facility.get('close_time') else '',
                'open_days': facility.get('open_days', [])
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