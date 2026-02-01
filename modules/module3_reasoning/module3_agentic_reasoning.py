import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
from typing import Dict, Any

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """You are a Senior Finance Officer and Responsible AI Agent operating inside a regulated banking environment.

You receive structured signal intelligence from the Risk & Sentiment Analytics Engine.
Your role is to generate explainable, governance-compliant interpretation and response recommendations for internal banking use only.

MANDATORY CONSTRAINTS:
- Do NOT introduce new facts beyond the provided signal
- Do NOT speculate beyond the provided data
- Do NOT reference real individuals or personal data
- Do NOT recommend autonomous or public actions
- All outputs are decision-support only requiring human approval
- Maintain professional, neutral, banking-compliant language

DECISION RULES:
1. If confidence_score < 0.70: Return "No Action – Further Monitoring Required"
2. If confidence_score >= 0.70: Choose ONE from: "Internal Investigation", "Targeted Monitoring Escalation", "Prepare External Holding Statement", "Update Security or Service FAQ"

INPUT SIGNAL:
{input_json}

CONFIDENCE SCORE: {confidence_score}

REQUIRED OUTPUT (VALID JSON ONLY):
{{
  "explanation_text": "EXACTLY 3 bullet points in format:\n• Signal: [3-5 words describing what happened]\n• Impact: [3-5 words describing bank impact]\n• Risk: [3-5 words describing threat]\nExample:\n• Signal: Fraudulent OTP phone call\n• Impact: Security protocol breach\n• Risk: Customer account compromise",
  "impact_assessment": {{
    "reputational_risk": "Low/Medium/High - brief reason for reputation DAMAGE severity",
    "operational_risk": "Low/Medium/High - brief reason for operational DISRUPTION severity",
    "customer_trust_impact": "Low/Medium/High - brief reason for trust DAMAGE severity (High = severe trust damage, Low = minimal trust damage)"
  }},
  "suggested_action": "Follow confidence_score rule strictly"
}}

CRITICAL INSTRUCTION: For customer_trust_impact, rate the DAMAGE to trust. High = severe damage, Medium = moderate damage, Low = minimal damage.

Generate ONLY valid JSON. No markdown. No additional text."""


def initialize_llm():
    """Initialize ChatOpenAI with production settings"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    logger.info("Initializing ChatOpenAI model")
    return ChatOpenAI(
        model="gpt-4",
        temperature=0.3,
        openai_api_key=api_key,
        max_tokens=800
    )


def create_reasoning_chain():
    """Create LangChain reasoning chain for Module 3"""
    llm = initialize_llm()
    
    prompt = PromptTemplate(
        input_variables=["input_json", "confidence_score"],
        template=PROMPT_TEMPLATE
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    logger.info("Reasoning chain created successfully")
    return chain


def calculate_confidence_score(signal_data: Dict[str, Any]) -> float:
    """Calculate confidence score based on signal characteristics"""
    score = 0.5
    
    if signal_data.get("is_flagged_for_review"):
        score += 0.15
    
    urgency = signal_data.get("shadow_review_urgency", "").lower()
    if urgency == "critical":
        score += 0.20
    elif urgency == "high":
        score += 0.10
    
    sentiment = signal_data.get("sentiment_score", 0)
    if sentiment <= -0.8:
        score += 0.15
    elif sentiment <= -0.5:
        score += 0.10
    
    return min(round(score, 2), 1.0)


def validate_input(signal_data: Dict[str, Any]) -> bool:
    """Validate input signal structure"""
    required_fields = [
        "synthetic_id", "timestamp", "raw_text", "source_type",
        "category", "scenario_category", "sentiment_score"
    ]
    
    for field in required_fields:
        if field not in signal_data:
            raise ValueError(f"Missing required field: {field}")
    
    logger.info(f"Input validation passed for {signal_data['synthetic_id']}")
    return True


def parse_llm_output(output_text: str) -> Dict[str, Any]:
    """Parse LLM output, handling both raw JSON and markdown-wrapped JSON"""
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        if "```json" in output_text:
            json_start = output_text.find("```json") + 7
            json_end = output_text.find("```", json_start)
            json_str = output_text[json_start:json_end].strip()
            return json.loads(json_str)
        elif "```" in output_text:
            json_start = output_text.find("```") + 3
            json_end = output_text.find("```", json_start)
            json_str = output_text[json_start:json_end].strip()
            return json.loads(json_str)
        else:
            raise


def append_module3_fields(signal_data: Dict[str, Any], reasoning_output: str) -> Dict[str, Any]:
    """Append Module 3 reasoning fields to original signal - minimal output"""
    try:
        reasoning_json = parse_llm_output(reasoning_output)
        
        # Only add these three fields
        signal_data["module3_explanation"] = reasoning_json["explanation_text"]
        signal_data["module3_impact_assessment"] = reasoning_json["impact_assessment"]
        signal_data["module3_suggested_action"] = reasoning_json["suggested_action"]
        
        logger.info(f"Module 3 fields appended for {signal_data['synthetic_id']}")
        return signal_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM output as JSON: {e}")
        logger.error(f"Raw output: {reasoning_output}")
        raise
    except KeyError as e:
        logger.error(f"Missing expected field in reasoning output: {e}")
        raise


def run_module3(input_signal: Dict[str, Any]) -> Dict[str, Any]:
    """Main execution function for Module 3 Agentic Reasoning"""
    try:
        logger.info("=" * 80)
        logger.info("MODULE 3: AGENTIC REASONING & RESPONSE - STARTED")
        logger.info("=" * 80)
        
        validate_input(input_signal)
        
        confidence_score = calculate_confidence_score(input_signal)
        logger.info(f"Calculated confidence score: {confidence_score:.2f}")
        
        chain = create_reasoning_chain()
        
        input_json_str = json.dumps(input_signal, indent=2)
        
        logger.info("Invoking LLM reasoning chain...")
        reasoning_output = chain.run(
            input_json=input_json_str,
            confidence_score=confidence_score
        )
        
        logger.info("LLM reasoning completed")
        
        enriched_signal = append_module3_fields(input_signal.copy(), reasoning_output)
        
        logger.info("=" * 80)
        logger.info("MODULE 3: PROCESSING COMPLETE")
        logger.info("=" * 80)
        
        return enriched_signal
        
    except Exception as e:
        logger.error(f"Module 3 processing failed: {str(e)}")
        raise


if __name__ == "__main__":
    import sys
    
    input_file = "..\module2_analysis\signals_final_output.json"
    output_file = "agentic_output.json"
    
    try:
        logger.info(f"Loading input from: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        logger.info(f"Successfully loaded input file")
        
        if isinstance(input_data, dict):
            logger.info("Processing single signal")
            result = run_module3(input_data)
        elif isinstance(input_data, list):
            logger.info(f"Processing {len(input_data)} signals")
            result = []
            for idx, signal in enumerate(input_data, 1):
                logger.info(f"Processing signal {idx}/{len(input_data)}: {signal.get('synthetic_id', 'Unknown')}")
                processed_signal = run_module3(signal)
                result.append(processed_signal)
        else:
            raise ValueError("Input JSON must be a dict or list of dicts")
        
        logger.info(f"Saving output to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("MODULE 3 PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Input file:  {input_file}")
        print(f"Output file: {output_file}")
        print(f"Signals processed: {len(result) if isinstance(result, list) else 1}")
        print("=" * 80)
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        print(f"\n❌ ERROR: Could not find '{input_file}'")
        print("Please ensure the file exists in the current directory.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        print(f"\n❌ ERROR: '{input_file}' contains invalid JSON")
        print(f"Error details: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        print(f"\n❌ ERROR: Processing failed")
        print(f"Error details: {str(e)}")
        sys.exit(1)