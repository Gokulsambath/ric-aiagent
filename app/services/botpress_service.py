import httpx
from app.services.chat_strategy import ChatStrategy
from app.schema.chat_schema import ChatResponse
from app.configs.settings import settings
import logging

logger = logging.getLogger(__name__)

class BotpressService(ChatStrategy):
    def __init__(self):
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
    
    async def stream_message(self, message: str, session_id: str, metadata: dict = None, bot_id: str = None):
        """
        Stream a message to Botpress and yield text chunks.
        Botpress doesn't natively support streaming, so we fetch the full response
        and simulate streaming by yielding it character by character or word by word.
        """
        # Use passed bot_id or fallback to default
        target_bot_id = bot_id or self.bot_id
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
                
                # Build full response and collect choices
                bot_parts = []
                all_choices = []
                
                for r in responses:
                    resp_type = r.get("type", "")
                    print(f"Processing response type: {resp_type}, data: {r}", flush=True)
                    
                    
                    if resp_type == "text":
                        bot_parts.append(r.get("text", ""))
                    
                    elif resp_type == "choice" or resp_type == "single-choice":
                        choice_text = r.get("text", "")
                        if choice_text:
                            bot_parts.append(choice_text)
                        
                        choices = r.get("choices", [])
                        logger.info(f"Found {len(choices)} choices: {choices}")
                        if choices:
                            # Store choices for later
                            all_choices.extend(choices)
                    
                    elif resp_type == "carousel":
                        items = r.get("items", [])
                        if items:
                            bot_parts.append("\n**Options:**")
                            for idx, item in enumerate(items, 1):
                                title = item.get("title", f"Option {idx}")
                                bot_parts.append(f"{idx}. {title}")
                
                logger.info(f"Final bot_parts: {bot_parts}")
                logger.info(f"All choices: {all_choices}")
                
                full_text = "\n".join(bot_parts) if bot_parts else "No response from bot"
                
                # Stream text content line by line
                lines = full_text.split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        yield line
                    else:
                        yield "\n" + line
                
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
                    yield f"\n__CHOICES__{choices_json}__END_CHOICES__"
                
                # If AI Assistant was one of the options, signal provider switch capability
                if ai_assistant_selected:
                    yield f"\n__SWITCH_PROVIDER__openai__END_SWITCH__"
                
        except httpx.HTTPError as e:
            logger.error(f"Botpress API Error: {str(e)}")
            raise Exception(f"Failed to communicate with Botpress: {str(e)}")
