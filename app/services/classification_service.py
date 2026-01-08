
import json
import logging
import ast
from typing import Optional, List
from app.services.openai_service import OpenAIService
from app.schema.classification_schema import OrganisationTypeEnum, ClassificationResult

logger = logging.getLogger(__name__)

class ClassificationService:
    CONCEPT_MAP = {
        "startup": OrganisationTypeEnum.PRIVATE_LIMITED.value,
        "pvt ltd": OrganisationTypeEnum.PRIVATE_LIMITED.value,
        "private limited": OrganisationTypeEnum.PRIVATE_LIMITED.value,
        "ltd": OrganisationTypeEnum.PUBLIC_LIMITED.value,
        "public limited": OrganisationTypeEnum.PUBLIC_LIMITED.value,
        "partnership": OrganisationTypeEnum.PARTNERSHIP.value,
        "proprietorship": OrganisationTypeEnum.SOLE_PROPRIETORSHIP.value,
        "llp": OrganisationTypeEnum.LLP.value,
        "trust": OrganisationTypeEnum.TRUST.value,
        "ngo": OrganisationTypeEnum.SOCIETY.value,
        "society": OrganisationTypeEnum.SOCIETY.value,
    }

    INDUSTRY_CONCEPT_MAP = {
        "bank": "BFSI",
        "hospital": "Healthcare",
        "clinic": "Healthcare",
        "college": "Education",
        "school": "Education",
        "university": "Education",
        "shop": "Retail",
        "store": "Retail",
        "factory": "Manufacturing",
        "logistics": "Logistics",
        "courier": "Logistics",
        "transport": "Logistics",
        "power": "Energy",
        "solar": "Energy",
        "software": "IT Services",
        "it": "IT Services",
    }

    SIZE_CONCEPT_MAP = {
        "startup": "1-10",
        "small": "1-10",
        "tiny": "1-10",
        "solo": "1-10",
        "one": "1-10",
        "single": "1-10",
        "medium": "11-50",
        "large": "1000+",
        "huge": "1000+",
        "enterprise": "1000+",
        "mnc": "1000+",
    }

    def __init__(self):
        self.openai_service = OpenAIService()

    async def classify_organization(self, text: str) -> str:
        """
        Classifies the organization type from the given text using hybrid approach (Static Map + LLM).
        """
        # ... (existing code) ...
        # 1. Static/Heuristic Check
        text_lower = text.lower().strip()
        
        # Exact/Keyword match from map
        for key, value in self.CONCEPT_MAP.items():
            if key in text_lower:
                logger.info(f"Static Map Hit: '{key}' in '{text}' -> {value}")
                return value

        # 2. LLM Fallback
        valid_options = [e.value for e in OrganisationTypeEnum]
        options_str = json.dumps(valid_options)
        
        system_prompt = f"""
        You are a smart data mapping assistant.
        Your task is to map the User Input to the Best Matching Organization Type from the list below.
        
        Valid Organization Types:
        {options_str}
        
        Output Format:
        You must return a single valid JSON object (use DOUBLE QUOTES for keys and values):
        {{
            "organisation_type": "string",
            "confidence": float
        }}
        
        Mapping Rules:
        1. "startup" OR "company" -> "Private Limited Company"
        2. "firm" -> "Partnership Firm"
        3. "trust" -> "Trust"
        4. "ngo" -> "Society" (or Section 8 if specified)
        5. "proprietorship" -> "Sole Proprietorship"
        6. Typos (e.g., "Pravte") -> Fix and map to correct type.
        7. ONLY return "Unclear" if the input is completely gibberish (e.g., "asdf").
        8. Be assertive. If it *could* be a Private Limited Company, assume it is.
        """
        
        return await self._classify_generic(text, system_prompt, ClassificationResult)

    async def classify_industry(self, text: str) -> str:
        """
        Classifies the industry type from the given text using hybrid approach (Static Map + LLM).
        """
        # ... (existing code for industry) ...
        from app.schema.classification_schema import IndustryTypeEnum, IndustryClassificationResult
        
        # 1. Static/Heuristic Check
        text_lower = text.lower().strip()
        
        # Exact/Keyword match from map
        for key, value in self.INDUSTRY_CONCEPT_MAP.items():
            if key in text_lower:
                logger.info(f"Industry Static Map Hit: '{key}' in '{text}' -> {value}")
                return value

        # 2. LLM Fallback
        valid_options = [e.value for e in IndustryTypeEnum]
        options_str = json.dumps(valid_options)
        
        system_prompt = f"""
        You are a smart data mapping assistant.
        Your task is to map the User Input to the Best Matching Industry Type from the list below.
        
        Valid Industry Types:
        {options_str}
        
        Output Format:
        You must return a single valid JSON object (use DOUBLE QUOTES for keys and values):
        {{
            "industry_type": "string",
            "confidence": float
        }}
        
        Mapping Rules:
        1. "software" OR "tech" -> "IT Services"
        2. "bank" OR "finance" -> "BFSI"
        3. "medical" OR "doctor" -> "Healthcare"
        4. "school" OR "training" -> "Education"
        5. "shop" OR "mall" -> "Retail"
        6. ONLY return "Unclear" if the input is completely gibberish.
        """
        
        result_value = await self._classify_generic(text, system_prompt, IndustryClassificationResult, key="industry_type")
        return result_value

    async def classify_employee_size(self, text: str) -> str:
        """
        Classifies the employee size from the given text using hybrid approach (Static Map + LLM).
        """
        from app.schema.classification_schema import EmployeeSizeEnum, EmployeeSizeClassificationResult
        
        # 1. Static/Heuristic Check
        text_lower = text.lower().strip()
        
        # Exact/Keyword match from map
        for key, value in self.SIZE_CONCEPT_MAP.items():
            # Use 'split' to match exact words if possible to avoid partial matches like "one" in "money"
            # But simple containment is fine for now as long as keys are distinct enough
             if key in text_lower.split(): 
                logger.info(f"Size Static Map Hit: '{key}' in '{text}' -> {value}")
                return value
             elif key in text_lower: # Fallback for multi-word keys
                 logger.info(f"Size Static Map Hit (substring): '{key}' in '{text}' -> {value}")
                 return value

        # 2. LLM Fallback
        valid_options = [e.value for e in EmployeeSizeEnum]
        options_str = json.dumps(valid_options)
        
        system_prompt = f"""
        You are a smart data mapping assistant.
        Your task is to map the User Input to the Best Matching Employee Size Range from the list below.
        
        Valid Ranges:
        {options_str}
        
        Output Format:
        You must return a single valid JSON object (use DOUBLE QUOTES for keys and values):
        {{
            "employee_size": "string",
            "confidence": float
        }}
        
        Mapping Rules:
        1. Extract numbers from text (e.g., "30 people" -> 30).
        2. Map the number to the correct range:
           - 1 to 10 -> "1-10"
           - 11 to 50 -> "11-50"
           - 51 to 200 -> "51-200"
           - 201 to 500 -> "201-500"
           - 501 to 1000 -> "501-1000"
           - > 1000 -> "1000+"
        3. Handle fuzzy terms: "small startup" -> "1-10", "mid-sized" -> "51-200".
        4. ONLY return "Unclear" if the input is purely gibberish.
        """
        
        result_value = await self._classify_generic(text, system_prompt, EmployeeSizeClassificationResult, key="employee_size")
        return result_value

    async def _classify_generic(self, text: str, system_prompt: str, result_model, key: str = "organisation_type") -> str:
        try:
            user_prompt = f'User Input: "{text}"'
            
            # Call LLM
            response = await self.openai_service.send_message(
                message=user_prompt, 
                session_id="classification-request",
                system_prompt=system_prompt
            )
            
            raw_content = response.content.strip()
            
            # Attempt to extract JSON if wrapped in markdown code blocks
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            try:
                data = json.loads(raw_content)
            except json.JSONDecodeError:
                logger.warning("JSON decode failed, trying ast.literal_eval for single-quote JSON")
                try:
                    data = ast.literal_eval(raw_content)
                except Exception as e2:
                    logger.error(f"Failed to parse LLM response via ast: {e2}")
                    raise e2

            # Normalize keys to match schema
            # For organisation_type, we handle organization_type alias in schema, 
            # here we assume data is ready for Pydantic
            
            # Validate with Pydantic
            result = result_model(**data)
            
            classified_value = getattr(result, key)
            if hasattr(classified_value, "value"):
                classified_value = classified_value.value
                
            logger.info(f"Classification Result ({key}): {classified_value} (Confidence: {result.confidence})")
            
            # Application Logic: Confidence Threshold
            if result.confidence < 0.7:
                logger.warning(f"Confidence {result.confidence} below threshold 0.7. Returning Unclear.")
                return "Unclear"
                
            return classified_value
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "Unclear"
