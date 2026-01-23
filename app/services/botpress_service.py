import httpx
from app.services.chat_strategy import ChatStrategy
from app.services.classification_service import ClassificationService
from app.schema.chat_schema import ChatResponse
from app.configs.settings import settings
import logging
from app.services.redis_service import redis_service, RedisService

logger = logging.getLogger(__name__)

class BotpressService(ChatStrategy):
    def __init__(self):
        # Use the full URL from settings which includes /botpress prefix
        self.base_url = settings.botpress.botpress_url
        self.bot_id = settings.botpress.bot_id
        # Webhook ID is not strictly needed for the Converse API unless verified via that channel
        
    async def send_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None) -> ChatResponse:
        """
        Sends a message to the Botpress Converse API.
        POST /api/v1/bots/{botId}/converse/{userId}
        """
        # Use passed bot_id or fallback to default
        target_bot_id = bot_id or self.bot_id
        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/converse/{session_id}"
        
        payload = {
            "type": "text",
            "text": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                
                # Botpress returns a list of responses with different types
                # Common types: text, choice (buttons), carousel, image, etc.
                responses = data.get("responses", [])
                
                bot_parts = []
                for r in responses:
                    resp_type = r.get("type", "")
                    
                    if resp_type == "text" or "text" in r:
                        bot_parts.append(r.get("text", ""))
                    
                    elif resp_type == "choice":
                        # Handle choice/button responses
                        choice_text = r.get("text", "")
                        if choice_text:
                            bot_parts.append(choice_text)
                        
                        # Format choices as markdown buttons/list
                        choices = r.get("choices", [])
                        if choices:
                            bot_parts.append("\n**Options:**")
                            for idx, choice in enumerate(choices, 1):
                                title = choice.get("title", choice.get("value", f"Option {idx}"))
                                bot_parts.append(f"{idx}. {title}")
                    
                    elif resp_type == "carousel":
                        # Handle carousel (multiple cards)
                        items = r.get("items", [])
                        if items:
                            bot_parts.append("\n**Options:**")
                            for idx, item in enumerate(items, 1):
                                title = item.get("title", f"Option {idx}")
                                bot_parts.append(f"{idx}. {title}")
                
                bot_text = "\n".join(bot_parts) if bot_parts else "No response from bot"
                
                return ChatResponse(
                    session_id=session_id,
                    role="assistant",
                    content=bot_text,
                    provider="botpress",
                    metadata={"raw_response": data}
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
    
    async def get_conversation_state(self, session_id: str, bot_id: str = None) -> dict:
        """
        Fetches the conversation state from Botpress State API.
        GET /api/v1/bots/{botId}/users/{userId}/state
        
        Returns the full conversation state including user variables.
        """
        target_bot_id = bot_id or self.bot_id
        # Try user-based state endpoint first
        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/users/{session_id}/state"
        
        print(f"🔄 ===== CALLING STATE API =====", flush=True)
        print(f"🔄 URL: {url}", flush=True)
        print(f"🔄 Session ID (User ID): {session_id}", flush=True)
        print(f"🔄 Bot ID: {target_bot_id}", flush=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                print(f"🔄 Status Code: {response.status_code}", flush=True)
                
                # Don't raise for 404 - might just mean no state yet
                if response.status_code == 404:
                    print(f"⚠️ State not found (404) - user may not have state yet", flush=True)
                    print(f"⚠️ Response: {response.text}", flush=True)
                    return {}
                
                response.raise_for_status()
                
                state_data = response.json()
                print(f"🔄 ===== BOTPRESS STATE API RESPONSE =====", flush=True)
                print(f"🔄 State keys: {list(state_data.keys())}", flush=True)
                print(f"🔄 Full state: {state_data}", flush=True)
                print(f"🔄 =========================================", flush=True)
                
                return state_data
                
        except httpx.HTTPStatusError as e:
            print(f"❌ State API HTTP Error: {e.response.status_code}", flush=True)
            print(f"❌ Response body: {e.response.text}", flush=True)
            return {}
        except Exception as e:
            print(f"❌ State API Exception: {type(e).__name__}: {str(e)}", flush=True)
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
            return {}
    
    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None, user_name: str = None, user_designation: str = None):
        """
        Stream a message to Botpress and yield text chunks.
        Botpress doesn't natively support streaming, so we fetch the full response
        and simulate streaming by yielding it character by character or word by word.
        
        For CMS bot (ric-cms), if user_name is provided, prepend it to the first message.
        """
        # Use passed bot_id or fallback to default
        target_bot_id = bot_id or self.bot_id
        
        # For CMS bot, prepend user details to the first message if provided
        # For CMS bot, prepend user details to the first message if provided
        if target_bot_id == "ric-cms" and user_name:
            print(f"DEBUG: CMS bot - replacing message with user name for initial handshake", flush=True)
            # Send JUST the user name as the message content
            message = user_name
            print(f"DEBUG: Modified message: {message}", flush=True)
        
        # --- LLM INTERCEPTION START ---
        # Heuristic Logic 1: Organization Type
        redis_key_org = f"ric:session:{session_id}:expecting_org_type"
        is_expecting_org = await redis_service.get(redis_key_org)
        
        # Heuristic Logic 2: Industry Type
        redis_key_industry = f"ric:session:{session_id}:expecting_industry_type"
        is_expecting_industry = await redis_service.get(redis_key_industry)
        
        # Heuristic Logic 3: Employee Size
        redis_key_size = f"ric:session:{session_id}:expecting_employee_size"
        is_expecting_size = await redis_service.get(redis_key_size)
        
        if not message.strip().startswith("{"):
            try:
                classification_service = ClassificationService()
                
                if is_expecting_org:
                    logger.info(f"Intercepting expected 'custom-orgtype' input: {message}")
                    normalized_message = await classification_service.classify_organization(message)
                    logger.info(f"Normalized '{message}' to '{normalized_message}'")
                    if normalized_message:
                         message = normalized_message
                    await redis_service.delete(redis_key_org)
                    
                elif is_expecting_industry:
                    logger.info(f"Intercepting expected 'custom-industry' input: {message}")
                    normalized_message = await classification_service.classify_industry(message)
                    logger.info(f"Normalized '{message}' to '{normalized_message}'")
                    if normalized_message:
                         message = normalized_message
                    await redis_service.delete(redis_key_industry)

                elif is_expecting_size:
                    logger.info(f"Intercepting expected 'custom-size' input: {message}")
                    normalized_message = await classification_service.classify_employee_size(message)
                    logger.info(f"Normalized '{message}' to '{normalized_message}'")
                    if normalized_message:
                         message = normalized_message
                    await redis_service.delete(redis_key_size)
                    
            except Exception as e:
                logger.error(f"Error in LLM interception: {e}")
        # --- LLM INTERCEPTION END ---

        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/converse/{session_id}"

        url = f"{self.base_url}/api/v1/bots/{target_bot_id}/converse/{session_id}"
        
        # Check if message is a JSON string (for choice payloads)
        payload = {}
        try:
            if message.strip().startswith("{"):
                json_payload = json.loads(message)
                # If it looks like a valid payload structure, use it directly/merged
                if isinstance(json_payload, dict):
                    payload = json_payload
        except Exception as e:
            # Not valid json, treat as text
            pass
            
        if not payload:
             payload = {
                "type": "text",
                "text": message
            }
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                responses = data.get("responses", [])
                
                # EXTRACT USER SELECTIONS FROM RESPONSE TEXT
                # Botpress includes the selections in the final "You have selected" response
                # Example: "• Organization: private_limited\n• Industry: real_estate\n• State: ANDHRA_PRADESH\n• Employee Size: 11-20"
                
                print(f"🔍 ===== EXTRACTING VARIABLES FROM TEXT =====", flush=True)
                
                compliance_vars = {}
                current_flow = None
                
                # Check all response texts for user selections
                for r in responses:
                    resp_text = r.get("text", "")
                    
                    # Look for the "You have selected:" pattern which indicates final applicability response
                    if "You have selected:" in resp_text or "Organization:" in resp_text:
                        print(f"🔍 Found selection summary in response", flush=True)
                        print(f"🔍 Text: {resp_text[:200]}...", flush=True)
                        
                        # Extract organization type
                        if "Organization:" in resp_text:
                            import re
                            org_match = re.search(r'Organization:\s*(\w+)', resp_text)
                            if org_match:
                                compliance_vars['orgType'] = org_match.group(1)
                                print(f"✓ Extracted orgType: {compliance_vars['orgType']}", flush=True)
                        
                        # Extract state
                        if "State:" in resp_text:
                            import re
                            state_match = re.search(r'State:\s*([\w_]+)', resp_text)
                            if state_match:
                                compliance_vars['states'] = state_match.group(1)
                                print(f"✓ Extracted state: {compliance_vars['states']}", flush=True)
                        
                        # Extract industry
                        if "Industry:" in resp_text:
                            import re
                            industry_match = re.search(r'Industry:\s*(\w+)', resp_text)
                            if industry_match:
                                compliance_vars['industry'] = industry_match.group(1)
                                print(f"✓ Extracted industry: {compliance_vars['industry']}", flush=True)
                        
                        # Extract employee size
                        if "Employee Size:" in resp_text:
                            import re
                            size_match = re.search(r'Employee Size:\s*([\w-]+)', resp_text)
                            if size_match:
                                compliance_vars['employeeSize'] = size_match.group(1)
                                print(f"✓ Extracted employeeSize: {compliance_vars['employeeSize']}", flush=True)
                        
                        # If we found this pattern, we're in the applicability flow results
                        if compliance_vars:
                            current_flow = "applicability"
                
                print(f"Compliance variables extracted: {compliance_vars}", flush=True)
                print(f"Current flow: {current_flow}", flush=True)
                print(f"=====================================", flush=True)
                
                # Build separate responses and collect choices
                text_responses = []
                all_choices = []
                
                for r in responses:
                    resp_type = r.get("type", "")
                    print(f"Processing response type: {resp_type}, data: {r}", flush=True)
                    print(f"DEBUG: Handling type '{resp_type}'", flush=True)
                    
                    
                    if resp_type == "text":
                        text_responses.append(r.get("text", ""))
                    
                    elif resp_type == "choice" or resp_type == "single-choice":
                        print(f"DEBUG: Entered single-choice block for type {resp_type}", flush=True)
                        choice_text = r.get("text", "")
                        if choice_text:
                            text_responses.append(choice_text)
                        
                        choices = r.get("choices", [])
                        logger.info(f"Found {len(choices)} choices: {choices}")
                        if choices:
                            # Store choices for later
                            all_choices.extend(choices)
                    
                    elif resp_type == "carousel":
                        items = r.get("items", [])
                        if items:
                            carousel_parts = ["\n**Options:**"]
                            for idx, item in enumerate(items, 1):
                                title = item.get("title", f"Option {idx}")
                                carousel_parts.append(f"{idx}. {title}")
                            text_responses.append("\n".join(carousel_parts))
                
                
                logger.info(f"Total text responses: {len(text_responses)}")
                logger.info(f"All choices: {all_choices}")
                print(f"🔍 DEBUG: text_responses length = {len(text_responses)}", flush=True)
                print(f"🔍 DEBUG: text_responses content = {text_responses}", flush=True)
                
                # HEURISTIC TRIGGER CHECK
                # 1. Check for Organization Type Trigger
                trigger_phrases_org = ["Please enter your organization type", "enter your organization type"]
                
                # 2. Check for Industry Type Trigger
                trigger_phrases_industry = ["Please enter your industry type", "enter your industry type"]
                
                # 3. Check for Employee Size Trigger
                trigger_phrases_size = ["Please enter your employee size", "enter your employee size"]
                
                # Check all responses for triggers
                full_bot_text = "\n".join(text_responses) if text_responses else ""
                
                if any(phrase in full_bot_text for phrase in trigger_phrases_org):
                    redis_key = f"ric:session:{session_id}:expecting_org_type"
                    logger.info(f"Setting Org Expectation Flag: {redis_key}")
                    await redis_service.set(redis_key, "true", ttl=600)

                if any(phrase in full_bot_text for phrase in trigger_phrases_industry):
                    redis_key = f"ric:session:{session_id}:expecting_industry_type"
                    logger.info(f"Setting Industry Expectation Flag: {redis_key}")
                    await redis_service.set(redis_key, "true", ttl=600)

                if any(phrase in full_bot_text for phrase in trigger_phrases_size):
                    redis_key = f"ric:session:{session_id}:expecting_employee_size"
                    logger.info(f"Setting Size Expectation Flag: {redis_key}")
                    await redis_service.set(redis_key, "true", ttl=600)
                
                # Stream each text response separately with separators
                if not text_responses:
                    yield "No response from bot"
                else:
                    for idx, text in enumerate(text_responses):
                        # Stream this response line by line
                        lines = text.split("\n")
                        for i, line in enumerate(lines):
                            if i == 0:
                                yield line
                            else:
                                yield "\n" + line
                        
                        # Add separator marker between responses (but not after the last one)
                        if idx < len(text_responses) - 1:
                            print(f'🔔 DEBUG: Emitting __NEXT_MESSAGE__ marker between response {idx} and {idx+1}', flush=True)
                            yield "\n__NEXT_MESSAGE__"
                
                #Check if we're in the applicability flow AND have compliance variables
                # Only query acts when inside applicability.flow.json
                acts_data = None
                is_applicability_flow = current_flow == "applicability"
                
                # Check if any compliance variables are present
                has_compliance_data = compliance_vars and any(
                    key in compliance_vars for key in ['orgType', 'states', 'industry', 'employeeSize']
                )
                
                if is_applicability_flow and has_compliance_data:
                    try:
                        # Mapping for Botpress values to DB values (for special cases)
                        INDUSTRY_MAPPING = {
                            'it_ites': 'Information Technology',
                            'real_estate': 'Real Estate',
                            # Add more mappings as needed
                        }
                        
                        # Helper function to normalize Botpress values to DB format
                        def normalize_value(value, mapping=None):
                            """Convert ANDHRA_PRADESH -> Andhra Pradesh, real_estate -> Real Estate"""
                            if not value:
                                return value
                            
                            # Check if there's a specific mapping first
                            if mapping and value.lower() in mapping:
                                return mapping[value.lower()]
                            
                            # Otherwise, replace underscores with spaces and title case
                            return value.replace('_', ' ').title()
                        
                        # Extract and normalize variables from session.compliance
                        state_val = normalize_value(compliance_vars.get('states'))  # "ANDHRA_PRADESH" -> "Andhra Pradesh"
                        industry_val = normalize_value(compliance_vars.get('industry'), INDUSTRY_MAPPING)  # "it_ites" -> "Information Technology"
                        org_type_val = normalize_value(compliance_vars.get('orgType'))  # "public_limited" -> "Public Limited"
                        size_val = compliance_vars.get('employeeSize')  # "11-20" stays as-is
                        
                        print(f"📊 Acts query parameters (normalized):", flush=True)
                        print(f"   State: {state_val}", flush=True)
                        print(f"   Industry: {industry_val}", flush=True)
                        print(f"   Org Type: {org_type_val}", flush=True)
                        print(f"   Size: {size_val}", flush=True)
                        
                        # Only query acts if we have at least one filter
                        if state_val or industry_val or size_val or org_type_val:
                            print(f"✅ Querying acts with normalized filters!", flush=True)
                            
                            from app.repository.acts_repo import Acts as ActsRepo
                            acts_repo = ActsRepo()
                            
                            acts_results = acts_repo.find_by_botpress_variables(
                                state=state_val,
                                industry=industry_val,
                                employee_size=size_val,
                                limit=50
                            )
                            
                            if acts_results:
                                acts_data = {
                                    'total': len(acts_results),
                                    'filters': {
                                        'state': state_val,
                                        'industry': industry_val,
                                        'employee_size': size_val
                                    },
                                    'acts': acts_results
                                }
                                logger.info(f"Found {len(acts_results)} acts results")
                    except Exception as e:
                        logger.error(f"Error querying acts: {str(e)}")
                
                # If we have acts data, yield it with markers
                if acts_data:
                    import json as json_lib
                    acts_json = json_lib.dumps(acts_data)
                    yield f"\n__ACTS_DATA__{acts_json}__END_ACTS__"
                
                # Check for RIC_DAILY_UPDATES workflow trigger
                daily_updates_data = None
                # Combine all text responses for trigger checking
                full_text = "\n".join(text_responses) if text_responses else ""
                
                # More flexible trigger detection to match various Botpress message formats
                trigger_phrases_daily = [
                    "RIC_DAILY_UPDATES",
                    "latest regulatory updates",
                    "here are the latest regulatory",
                    "regulatory update",
                    "corporate laws",  # Category indicator
                    "taxation",  # Category indicator
                    "labour laws"  # Category indicator
                ]
                
                # Check if message contains update categories (strong indicator it's the daily updates response)
                has_categories = "**Corporate Laws**" in full_text or "**Taxation**" in full_text or "**Labour Laws**" in full_text
                
                # Check if User Input explicitly requested updates
                user_requested = "RIC_DAILY_UPDATES" in message or "RIC_DAILY_UPDATES" in message.upper()
                
                has_trigger = any(phrase.lower() in full_text.lower() for phrase in trigger_phrases_daily)
                
                if has_trigger or has_categories or user_requested:
                    try:
                        print(f"🔔 Detected RIC_DAILY_UPDATES trigger!", flush=True)
                        
                        from app.repository.monthly_updates_repo import MonthlyUpdates as MonthlyUpdatesRepo
                        from app.services.monthly_updates_serv import MonthlyUpdates as MonthlyUpdatesService
                        from app.services.monthly_updates_scheduler import get_monthly_updates_scheduler
                        
                        # Initialize service
                        redis_svc = RedisService()
                        scheduler = get_monthly_updates_scheduler(redis_svc)
                        repo = MonthlyUpdatesRepo()
                        updates_service = MonthlyUpdatesService(repo, scheduler)
                        
                        # Fetch latest 5 updates
                        updates = updates_service.get_daily_updates(limit=5)
                        
                        # Group by category
                        grouped = {}
                        for update in updates:
                            category = update.get('category', 'Other')
                            if category not in grouped:
                                grouped[category] = {
                                    'category': category,
                                    'count': 0,
                                    'updates': []
                                }
                            grouped[category]['count'] += 1
                            grouped[category]['updates'].append(update)
                        
                        daily_updates_data = {
                                'total': len(updates) if updates else 0,
                                'grouped_by_category': grouped,
                                'updates': updates if updates else []
                            }
                            print(f"✅ Fetched {len(updates)} daily updates grouped into {len(grouped)} categories", flush=True)
                    except Exception as e:
                        logger.error(f"Error fetching daily updates: {str(e)}")
                        import traceback
                        print(f"❌ Daily updates error: {traceback.format_exc()}", flush=True)
                
                # If we have daily updates data, yield it with markers
                if daily_updates_data:
                    import json as json_lib
                    daily_json = json_lib.dumps(daily_updates_data)
                    yield f"\n__DAILY_UPDATES__{daily_json}__END_DAILY__"

                
                # Check if any choice is AI_ASSISTANT related
                ai_assistant_selected = False
                if all_choices:
                    for choice in all_choices:
                        choice_value = choice.get("value", "").upper()
                        # Check for various AI assistant choice values
                        if choice_value in ["AI_ASSISTANT", "ASK_AI", "ASK_RICA", "TALK_AI"]:
                            ai_assistant_selected = True
                            break
                
                # If we have choices, yield them as a special marker
                if all_choices:
                    import json as json_lib
                    choices_json = json_lib.dumps(all_choices)
                    print(f"DEBUG: Yielding choices marker: {choices_json}", flush=True)
                    yield f"\n__CHOICES__{choices_json}__END_CHOICES__"
                
                # If AI Assistant was one of the options, signal provider switch capability
                if ai_assistant_selected:
                    yield f"\n__SWITCH_PROVIDER__openai__END_SWITCH__"
                
        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
