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
                
                # EXTRACT TRIGGER PHRASES AND PREPARE DATA
                text_responses_for_triggers = []
                for r in responses:
                    resp_type = r.get("type", "")
                    resp_text = r.get("text", "")
                    if resp_type in ["text", "single-choice", "choice"] and resp_text:
                         text_responses_for_triggers.append(resp_text)
                    elif resp_type == "carousel":
                        items = r.get("items", [])
                        for item in items:
                            if item.get("title"): text_responses_for_triggers.append(item.get("title"))

                full_bot_text = "\n".join(text_responses_for_triggers) if text_responses_for_triggers else ""

                # HEURISTIC TRIGGER CHECK (Setting Expectations)
                trigger_phrases_org = ["Please enter your organization type", "enter your organization type", "specify your organization", "custom organization"]
                trigger_phrases_industry = ["Please enter your industry type", "enter your industry type", "specify your industry", "custom industry"]
                trigger_phrases_size = ["Please enter your employee size", "enter your employee size", "specify your employee size", "custom employee size"]
                
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


                # --- PRE-FETCH DATA ---

                # 1. Acts Data
                acts_data_payload = None
                is_applicability_flow = current_flow == "applicability"
                has_compliance_data = compliance_vars and any(
                    key in compliance_vars for key in ['orgType', 'states', 'industry', 'employeeSize']
                )
                
                if is_applicability_flow and has_compliance_data:
                    try:
                        # Mapping for Botpress values to DB values
                        INDUSTRY_MAPPING = {
                            'it_ites': 'Information Technology',
                            'real_estate': 'Real Estate',
                        }
                        
                        def normalize_value(value, mapping=None):
                            if not value: return value
                            if mapping and value.lower() in mapping: return mapping[value.lower()]
                            return value.replace('_', ' ').title()
                        
                        state_val = normalize_value(compliance_vars.get('states'))
                        industry_val = normalize_value(compliance_vars.get('industry'), INDUSTRY_MAPPING)
                        org_type_val = normalize_value(compliance_vars.get('orgType'))
                        size_val = compliance_vars.get('employeeSize')
                        
                        if state_val or industry_val or size_val or org_type_val:
                            print(f"✅ Querying acts with normalized filters: {state_val}, {industry_val}, {org_type_val}, {size_val}", flush=True)
                            
                            from app.repository.acts_repo import Acts as ActsRepo
                            acts_repo = ActsRepo()
                            
                            acts_results = acts_repo.find_by_botpress_variables(
                                state=state_val,
                                industry=industry_val,
                                employee_size=size_val,
                                company_type = org_type_val,
                                limit=50
                            )
                            
                            if acts_results:
                                acts_data_payload = {
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

                # 2. Daily Updates Data
                daily_updates_data_payload = None
                trigger_phrases_daily = [
                    "RIC_DAILY_UPDATES", "latest regulatory updates", "here are the latest regulatory",
                    "regulatory update", "corporate laws", "taxation", "labour laws", "sebi", "rbi",
                    "irda", "customs", "dgft"
                ]
                has_categories = "**Corporate Laws**" in full_bot_text or "**Taxation**" in full_bot_text or "**Labour Laws**" in full_bot_text
                user_requested = "RIC_DAILY_UPDATES" in message or "RIC_DAILY_UPDATES" in message.upper()
                has_trigger = any(phrase.lower() in full_bot_text.lower() for phrase in trigger_phrases_daily)
                
                if has_trigger or has_categories or user_requested:
                    try:
                        print(f"🔔 Detected RIC_DAILY_UPDATES trigger!", flush=True)
                        from app.repository.monthly_updates_repo import MonthlyUpdates as MonthlyUpdatesRepo
                        from app.services.monthly_updates_serv import MonthlyUpdates as MonthlyUpdatesService
                        from app.services.monthly_updates_scheduler import get_monthly_updates_scheduler
                        
                        redis_svc = RedisService()
                        scheduler = get_monthly_updates_scheduler(redis_svc)
                        repo = MonthlyUpdatesRepo()
                        updates_service = MonthlyUpdatesService(repo, scheduler)
                        
                        updates = updates_service.get_daily_updates(limit=5)
                        
                        grouped = {}
                        for update in updates:
                            category = update.get('category', 'Other')
                            if category not in grouped:
                                grouped[category] = {'category': category, 'count': 0, 'updates': []}
                            grouped[category]['count'] += 1
                            grouped[category]['updates'].append(update)
                        
                        daily_updates_data_payload = {
                                'total': len(updates) if updates else 0,
                                'grouped_by_category': grouped,
                                'updates': updates if updates else []
                            }
                        print(f"✅ Fetched {len(updates)} daily updates", flush=True)
                    except Exception as e:
                        logger.error(f"Error fetching daily updates: {str(e)}")


                # --- STREAMING RESPONSE ---
                
                if not responses:
                    yield "No response from bot"
                    return # Exit if no responses

                acts_yielded = False
                daily_yielded = False
                ai_assistant_selected = False

                for idx, r in enumerate(responses):
                    resp_type = r.get("type", "")
                    content = ""
                    options = []

                    # 1. Build Content
                    if resp_type == "text":
                        content = r.get("text", "")
                    elif resp_type == "choice" or resp_type == "single-choice":
                        content = r.get("text", "")
                        options = r.get("choices", [])
                        
                        # Check for AI assistant selection in these options (for provider switching)
                        for choice in options:
                             if choice.get("value", "").upper() in ["AI_ASSISTANT", "ASK_AI", "ASK_RICA", "TALK_AI"]:
                                 ai_assistant_selected = True

                    elif resp_type == "carousel":
                        items = r.get("items", [])
                        if items:
                            carousel_parts = ["\n**Options:**"]
                            for i, item in enumerate(items, 1):
                                title = item.get("title", f"Option {i}")
                                carousel_parts.append(f"{i}. {title}")
                            content = "\n".join(carousel_parts)

                    # 2. Yield Content
                    if content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if i == 0: yield line
                            else: yield "\n" + line

                    # 3. Attach Acts Data (Optimistic attachment to 'You have selected' message)
                    if acts_data_payload and not acts_yielded:
                        # Attach if content has key phrase, OR if this is the last message and we haven't yielded yet?
                        # Better: Attach to "You have selected" if possible.
                        if "You have selected:" in content or "Organization:" in content:
                            import json as json_lib
                            acts_json = json_lib.dumps(acts_data_payload)
                            yield f"\n__ACTS_DATA__{acts_json}__END_ACTS__"
                            acts_yielded = True
                    
                    # 4. Attach Daily Updates
                    if daily_updates_data_payload and not daily_yielded:
                        # Logic to attach to relevant message? Or just attach to first finding of trigger?
                        # If trigger phrase is in THIS content:
                        if any(phrase.lower() in content.lower() for phrase in trigger_phrases_daily) or has_categories:
                             import json as json_lib
                             daily_json = json_lib.dumps(daily_updates_data_payload)
                             yield f"\n__DAILY_UPDATES__{daily_json}__END_DAILY__"
                             daily_yielded = True
                    
                    # 5. Attach Choices (Specific to this message)
                    if options:
                         import json as json_lib
                         choices_json = json_lib.dumps(options)
                         print(f"DEBUG: Yielding choices marker: {choices_json}", flush=True)
                         yield f"\n__CHOICES__{choices_json}__END_CHOICES__"

                    # 6. Separator for Next Bubble
                    if idx < len(responses) - 1:
                        yield "\n__NEXT_MESSAGE__"
                
                # Cleanup: If we have payloads that weren't triggered by specific text matches (fallback), append them to the LAST message
                if acts_data_payload and not acts_yielded:
                     import json as json_lib
                     acts_json = json_lib.dumps(acts_data_payload)
                     yield f"\n__ACTS_DATA__{acts_json}__END_ACTS__"
                
                if daily_updates_data_payload and not daily_yielded:
                     import json as json_lib
                     daily_json = json_lib.dumps(daily_updates_data_payload)
                     yield f"\n__DAILY_UPDATES__{daily_json}__END_DAILY__"

                # Switch provider check
                if ai_assistant_selected:
                    yield f"\n__SWITCH_PROVIDER__openai__END_SWITCH__"

        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
