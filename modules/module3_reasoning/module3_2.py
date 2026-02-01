import os
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Dict, Any, List

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_FILE = "..\module2_analysis\signals_final_output.json"
OUTPUT_FILE = "agentic_output.json"
PROCESS_INTERVAL = 10  # seconds


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
  "explanation_text": "EXACTLY 3 bullet points in format:
• Signal: [3-5 words]
• Impact: [3-5 words]
• Risk: [3-5 words]",
  "impact_assessment": {{
    "reputational_risk": "Low/Medium/High - brief reason",
    "operational_risk": "Low/Medium/High - brief reason",
    "customer_trust_impact": "Low/Medium/High - brief reason"
  }},
  "suggested_action": "Follow confidence_score rule strictly"
}}

Generate ONLY valid JSON. No markdown. No additional text."""


# ================= LLM INITIALIZATION (singleton) =================

_llm_instance = None
_chain_instance = None


def initialize_llm():
    global _llm_instance

    if _llm_instance is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        logger.info("Initializing ChatOpenAI model")
        _llm_instance = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            max_tokens=800
        )
    return _llm_instance


def create_reasoning_chain():
    global _chain_instance

    if _chain_instance is None:
        llm = initialize_llm()
        prompt = PromptTemplate(
            input_variables=["input_json", "confidence_score"],
            template=PROMPT_TEMPLATE
        )
        _chain_instance = LLMChain(llm=llm, prompt=prompt)
        logger.info("Reasoning chain initialized")

    return _chain_instance


# ================= CORE LOGIC =================

def calculate_confidence_score(signal_data: Dict[str, Any]) -> float:
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


def validate_input(signal_data: Dict[str, Any]) -> None:
    required_fields = [
        "synthetic_id", "timestamp", "raw_text",
        "source_type", "category",
        "scenario_category", "sentiment_score"
    ]

    for field in required_fields:
        if field not in signal_data:
            raise ValueError(f"Missing required field: {field}")


def parse_llm_output(output_text: str) -> Dict[str, Any]:
    return json.loads(output_text)


def append_module3_fields(signal_data: Dict[str, Any], reasoning_output: str) -> Dict[str, Any]:
    reasoning_json = parse_llm_output(reasoning_output)

    signal_data["module3_explanation"] = reasoning_json["explanation_text"]
    signal_data["module3_impact_assessment"] = reasoning_json["impact_assessment"]
    signal_data["module3_suggested_action"] = reasoning_json["suggested_action"]

    return signal_data


def process_single_signal(signal: Dict[str, Any], chain) -> Dict[str, Any]:
    validate_input(signal)

    confidence_score = calculate_confidence_score(signal)
    input_json_str = json.dumps(signal, indent=2)

    reasoning_output = chain.run(
        input_json=input_json_str,
        confidence_score=confidence_score
    )

    return append_module3_fields(signal.copy(), reasoning_output)


# ================= PROCESS CYCLE =================

def process_cycle():
    if not os.path.exists(INPUT_FILE):
        logger.warning("Input file not found, waiting...")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    signals = input_data if isinstance(input_data, list) else [input_data]

    chain = create_reasoning_chain()
    results: List[Dict[str, Any]] = []

    for signal in signals:
        try:
            processed = process_single_signal(signal, chain)
            results.append(processed)
        except Exception as e:
            logger.error(f"Skipping signal {signal.get('synthetic_id')}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Processed {len(results)} signals successfully")


# ================= CONTINUOUS RUNNER =================

def run_continuous():
    logger.info("=" * 80)
    logger.info("MODULE 3 CONTINUOUS AGENTIC REASONING ENGINE STARTED")
    logger.info(f"Input file : {INPUT_FILE}")
    logger.info(f"Output file: {OUTPUT_FILE}")
    logger.info(f"Interval   : {PROCESS_INTERVAL} seconds")
    logger.info("=" * 80)

    cycle = 0
    while True:
        cycle += 1
        logger.info(f"[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            process_cycle()
        except Exception as e:
            logger.error(f"Cycle failed: {e}")

        time.sleep(PROCESS_INTERVAL)


# ================= MAIN =================

if __name__ == "__main__":
    run_continuous()