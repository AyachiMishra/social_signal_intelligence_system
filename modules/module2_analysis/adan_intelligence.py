import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
# --- 1. SYSTEM CONFIGURATION & SCHEMAS ---

# ADAN Bank Standard Input Schema
class SyntheticSignal(BaseModel):
    synthetic_id: str
    timestamp: str
    raw_text: str
    source_type: str  # community_board | social_media | incident_log | other
    category: str
    generation_sequence: int
    pii_scrubbed_count: int

# ADAN Bank Strict Output Contract [cite: 49, 78]
class SignalAnalysis(BaseModel):
    synthetic_id: str = Field(description="UUID from the input signal")
    scenario_type: str = Field(description="Positive | Negative | Neutral | Ambiguous")
    sentiment_score: float = Field(description="Continuous value from -100 to 100")
    confidence: float = Field(description="Continuous value from 0.0 to 1.0 based on ADAN guidelines")
    ambiguity_score: int = Field(description="Integer from 0 to 100 where 100 is highly vague")
    uncertain: bool = Field(description="True if confidence < 0.7")
    risk_level: str = Field(description="Low | Medium | High")
    drivers: List[str] = Field(description="Short strings referencing explicit text evidence")
    explanation: str = Field(description="1-3 sentence justification for audit/regulators")

# --- 2. THE SIGNAL ANALYSIS AGENT (LANGCHAIN) ---

class AdanSignalAgent:
    def __init__(self, api_key: str=None):
        # Initializing the reasoning engine with zero temperature for deterministic output
        self.llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0, 
            openai_api_key=api_key
        )
        self.parser = JsonOutputParser(pydantic_object=SignalAnalysis)
        
        # Integrating ADAN Bank Guidelines directly into the Prompt [cite: 45, 46, 78]
        self.template = """
        You are a Senior Financial Systems Architect for ADAN Bank. Analyze the following synthetic signal.
        ADAN BANK COMPLIANCE WEIGHTING (Total 100):
        1. Regulatory Alignment (30): AML/KYC & legal compliance. 
        2. Market Conduct Risk (20): Fair disclosure, truthful claims. 
        3. Privacy & Data Safety (20): Protection of PII. 
        4. Reputation & Accuracy (15): Brand representation. 
        5. Source Credibility (15): Trustworthiness of origin. 
        CRITICAL FAIL CONDITIONS (Assign Confidence < 0.5):
        - Promotes evasion of AML/KYC or fake documents for ADAN accounts. [cite: 19, 20, 25, 78]
        - Discloses PII or internal ADAN confidential data. [cite: 33, 37, 78]
        - Falsely attributes endorsements or partnerships to ADAN Bank. [cite: 40, 43, 78]
        - Unverified financial claims regarding ADAN performance. [cite: 28, 31, 78]
        AMBIGUITY PENALTY RULES:
        - ambiguity_score: Return an INTEGER between 0 and 100 (0 = clear, 100 = highly vague/speculative).
        - If ambiguity_score > 50: You MUST decrease the sentiment_score toward 0 (Neutralize it).
        - If ambiguity_score > 50: You MUST lower the confidence score by at least 0.20.
        - High ambiguity in financial claims is a RED FLAG for misinformation.
        SCORING LOGIC:
        - Confidence >= 0.7: Accept (Compliant). 
        - Confidence 0.5 - 0.69: Review Recommended (Uncertain = true). 
        - Confidence < 0.5: Flag / Low Confidence (Uncertain = true). [cite: 49, 64]
        SCORING RULES :
        -sentiment_score: Return an INTEGER between -100 and 100.
        - -100: Extremely negative/critical risk
        - 0: Neutral/No sentiment
        - 100: Extremely positive/safe
        - The integer that is returned MUST be of a discrete quantity, do not return any multiples of 10
        TARGETED SENTIMENT RULES:
        1. ONLY score negative sentiment if the text is directed at ADAN Bank, its staff, or its specific products.
        2. Generalized complaints about the world (e.g., "scams are everywhere," "inflation is high") should be rated as NEUTRAL (Sentiment Score: 0) unless they explicitly blame the bank.
        3. AMBIGUITY PENALTY: 
        - If the statement is vague or lacks a clear target, set ambiguity_score > 70.
        - For high ambiguity, you MUST pull the sentiment_score toward 0 and lower the confidence below 0.5.
        INPUT SIGNAL:
        {input_json}
        {format_instructions}
        """
        
        self.prompt = PromptTemplate(
            template=self.template,
            input_variables=["input_json"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def process_signal(self, signal: dict) -> dict:
        """Processes a single synthetic signal and returns structured intelligence."""
        try:
            # Ensure the response is for ADAN/ADAN Bank specifically
            response = self.chain.invoke({"input_json": json.dumps(signal)})
            
            # Post-processing for HITL Escalation Logic
            if response['confidence'] < 0.7:
                response['uncertain'] = True
            
            return response
        except Exception as e:
            return {"error": str(e), "status": "Failed to parse signal"}

# --- 3. EXECUTION & TEST HARNESS ---

# --- 3. EXECUTION & BATCH PROCESSING ---

# --- 3. UPDATED EXECUTION & BATCH PROCESSING ---

# --- 3. UPDATED EXECUTION & BATCH PROCESSING ---

if __name__ == "__main__":
    load_dotenv() # Load your .env file
    api_key = os.getenv("OPENAI_API_KEY")[:]
    
    # Validation: Check if the key exists in the environment
    if not os.getenv("OPENAI_API_KEY"):
        print("CRITICAL ERROR: OPENAI_API_KEY not found in .env file or environment.")
        exit(1)

    agent = AdanSignalAgent(api_key=api_key) # Now this safely pulls from the environment

    # List to store final formatted results
    formatted_results = []

    try:
        # Load your input signals
        with open('..\module1_data_ingestion\synthetic_dataset.json', 'r') as f:
            signals_list = json.load(f)
        
        print(f"--- PROCESSING {len(signals_list)} SIGNALS ---")

        for signal in signals_list:
            # Process through AI agent
            report = agent.process_signal(signal)
            
           # Updated logic to handle Ambiguity vs. Urgency
            ambiguity = report.get("ambiguity_score", 0)
            confidence = report.get("confidence", 1.0)
            sentiment = report.get("sentiment_score", 0)

            # RULE: If it's highly ambiguous (>70) AND sentiment is neutral, it's just "Noise"
            if ambiguity > 70 and abs(sentiment) < 10:
                urgency = "Low"
                flagged = False
            else:
                # Standard ADAN Thresholds
                urgency = "Critical" if confidence < 0.5 else "Standard"
                flagged = confidence < 0.7

            mapped_output = {
                "synthetic_id": signal.get("synthetic_id"),
                "timestamp": signal.get("timestamp"),
                "raw_text": signal.get("raw_text"),
                "source_type": signal.get("source_type"),
                "category": signal.get("category"),
                "generation_sequence": signal.get("generation_sequence"),
                "pii_scrubbed_count": signal.get("pii_scrubbed_count"),
                "scenario_category": report.get("scenario_type", "Unknown"),
                "sentiment_score": sentiment,
                "shadow_review_urgency": urgency, # Now dynamically adjusted
                "is_flagged_for_review": flagged   # Now ignores ambiguous noise
            }
            
            formatted_results.append(mapped_output)
            print(f"Processed ID: {signal.get('synthetic_id')} | Flagged: {mapped_output['is_flagged_for_review']}")

        # Write the results to the output file
        with open('signals_output.json', 'w') as out_file:
            json.dump(formatted_results, out_file, indent=4)
        
        print(f"--- SUCCESS: Results saved to signals_output.json ---")

        # --- 4. WIPE INPUT SIGNALS ---
        # Reset the input file to an empty list to keep it as valid JSON
        with open('..\module1_data_ingestion\synthetic_dataset.json', 'w') as wipe_file:
            json.dump([], wipe_file)

    except FileNotFoundError:
        print("Error: 'signals.json' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")