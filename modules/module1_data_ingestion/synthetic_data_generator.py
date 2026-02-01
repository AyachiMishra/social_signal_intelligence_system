"""
Banking Social Signal Intelligence System
Module 1: Synthetic Data & Anonymization Engine

Purpose: Generate synthetic banking-related text data with robust PII anonymization
Compliance: Zero PII retention, full audit logging
Author: Senior Financial Systems Architect

PRODUCTION MODE: Continuous generation (random 1-10 records every 5 seconds)
Enhanced with OpenAI GPT-4 for realistic signal generation based on training data
OPTIMIZED: Single API call per batch generates all N signals at once
EXCLUSIVE: OpenAI API required - no template fallback
"""
from dotenv import load_dotenv
import os

load_dotenv()  # <-- loads .env automatically

print(os.getenv("OPENAI_API_KEY"))  # sanity check
import re
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random
from pathlib import Path
import time
import signal
import sys
import spacy
import csv
from openai import OpenAI

# Global flag for graceful shutdown
STOP_GENERATION = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global STOP_GENERATION
    print("\n\n🛑 STOP SIGNAL RECEIVED - Finishing current batch...")
    STOP_GENERATION = True

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# Load spaCy model for Named Entity Recognition
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


class PIIAnonymizer:
    """
    Multi-layer PII detection and anonymization engine.
    Uses regex patterns for structured PII and spaCy for name detection.
    Now includes currency amount anonymization.
    """
    
    # Comprehensive PII detection patterns (excluding name patterns - now using spaCy)
    PII_PATTERNS = {
        'email': (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'EMAIL_ADDRESS'
        ),
        'phone': (
            r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'PHONE_NUMBER'
        ),
        'ssn': (
            r'\b\d{3}-\d{2}-\d{4}\b',
            'SSN'
        ),
        'account_number': (
            r'\b(?:account|acct)[\s#:]*([0-9]{8,16})\b',
            'ACCOUNT_NUMBER'
        ),
        'credit_card': (
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'CREDIT_CARD'
        ),
        'routing_number': (
            r'\b[0-9]{9}\b(?=.*routing)',
            'ROUTING_NUMBER'
        ),
        'currency': (
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|usd)',
            'CURRENCY_AMOUNT'
        )
    }
    
    def __init__(self):
        self.scrubbing_stats = {
            'total_scrubbed': 0,
            'by_type': {}
        }
        self.nlp = nlp  # Use the globally loaded spaCy model
    
    def _detect_names_with_spacy(self, text: str) -> Tuple[str, int]:
        """
        Use spaCy NER to detect and mask person names.
        
        Args:
            text: Text to analyze for names
            
        Returns:
            Tuple of (text_with_names_masked, count_of_names_found)
        """
        doc = self.nlp(text)
        names_found = 0
        
        # Collect all person entities with their positions
        person_entities = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                person_entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        # Sort by position (reverse order) to replace from end to start
        # This prevents position shifts during replacement
        person_entities.sort(key=lambda x: x['start'], reverse=True)
        
        # Replace names from end to start
        masked_text = text
        for entity in person_entities:
            # Replace the name
            masked_text = (
                masked_text[:entity['start']] + 
                '<MASKED>' + 
                masked_text[entity['end']:]
            )
            
            names_found += 1
            self.scrubbing_stats['by_type']['PERSON_NAME'] = \
                self.scrubbing_stats['by_type'].get('PERSON_NAME', 0) + 1
        
        return masked_text, names_found
    
    def scrub_text(self, text: str) -> Tuple[str, int]:
        """
        Scrub all PII from text using multi-pass detection.
        Now includes currency amount anonymization.
        
        Args:
            text: Raw text to be scrubbed
            
        Returns:
            Tuple of (scrubbed_text, number_of_pii_instances_found)
        """
        scrubbed_text = text
        total_scrubbed = 0
        
        # Pass 1: spaCy-based name detection (FIRST to avoid breaking regex patterns)
        scrubbed_text, names_count = self._detect_names_with_spacy(scrubbed_text)
        total_scrubbed += names_count
        
        # Pass 2: Regex-based pattern matching for structured PII (including currency)
        for pii_type, (pattern, label) in self.PII_PATTERNS.items():
            matches = list(re.finditer(pattern, scrubbed_text, re.IGNORECASE))
            
            for match in matches:
                total_scrubbed += 1
                self.scrubbing_stats['by_type'][label] = self.scrubbing_stats['by_type'].get(label, 0) + 1
            
            # Replace all matches
            scrubbed_text = re.sub(pattern, '<MASKED>', scrubbed_text, flags=re.IGNORECASE)
        
        self.scrubbing_stats['total_scrubbed'] += total_scrubbed
        
        return scrubbed_text, total_scrubbed


class TrainingDataLoader:
    """
    Load and manage training data from CSV file for AI-powered signal generation.
    """
    
    def __init__(self, training_file: str = "training_data.csv"):
        self.training_file = Path(training_file)
        self.training_data = self._load_training_data()
        self.signals_by_type = self._organize_by_type()
    
    def _load_training_data(self) -> List[Dict]:
        """Load training data from CSV file."""
        if not self.training_file.exists():
            raise FileNotFoundError(
                f"Training file '{self.training_file}' not found. "
                "OpenAI API generation requires training data."
            )
        
        training_data = []
        try:
            with open(self.training_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    training_data.append({
                        'signal': row.get('Signals', '').strip(),
                        'type': row.get('Type', '').strip()
                    })
            print(f"✅ Loaded {len(training_data)} training examples from {self.training_file}")
        except Exception as e:
            raise RuntimeError(f"Error loading training data: {e}")
        
        if not training_data:
            raise ValueError("Training data file is empty. Cannot proceed with AI generation.")
        
        return training_data
    
    def _organize_by_type(self) -> Dict[str, List[str]]:
        """Organize training signals by type for easier sampling."""
        organized = {
            'Positive': [],
            'Negative': [],
            'Neutral': [],
            'Gibberish': []
        }
        
        for item in self.training_data:
            signal_type = item['type']
            signal_text = item['signal']
            
            if signal_type in organized and signal_text:
                organized[signal_type].append(signal_text)
        
        return organized
    
    def get_examples_by_type(self, signal_type: str, count: int = 3) -> List[str]:
        """Get random examples of a specific signal type."""
        examples = self.signals_by_type.get(signal_type, [])
        if not examples:
            return []
        
        sample_size = min(count, len(examples))
        return random.sample(examples, sample_size)


class AISignalGenerator:
    """
    Generate realistic banking signals using OpenAI GPT-4 based on training data.
    EXCLUSIVE: Only uses OpenAI API - no template fallback.
    OPTIMIZED: Makes single API call per batch to generate multiple signals.
    """
    
    def __init__(self, training_loader: TrainingDataLoader, api_key: str):
        self.training_loader = training_loader
        
        # OpenAI API key is REQUIRED
        if not api_key:
            raise ValueError(
                "OpenAI API key is required for signal generation. "
                "Set OPENAI_API_KEY environment variable or provide api_key parameter."
            )
        
        try:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI API initialized successfully")
        except Exception as e:
            raise RuntimeError(f"OpenAI API initialization failed: {e}")
    
    def generate_batch_signals(self, signal_requests: List[str]) -> List[str]:
        """
        Generate multiple signals in a single API call.
        EXCLUSIVE: Only uses OpenAI API - will raise exception if API fails.
        
        Args:
            signal_requests: List of signal types to generate (e.g., ['Positive', 'Negative', 'Neutral'])
            
        Returns:
            List of generated signal texts (same length as signal_requests)
        """
        return self._generate_batch_with_ai(signal_requests)
    
    def _generate_batch_with_ai(self, signal_requests: List[str]) -> List[str]:
        """
        Generate all signals in a single OpenAI API call.
        This is much more efficient than making N separate calls.
        """
        # Build comprehensive prompt with examples for each type
        examples_by_type = {}
        for signal_type in set(signal_requests):
            examples = self.training_loader.get_examples_by_type(signal_type, count=3)
            if examples:
                examples_by_type[signal_type] = examples
        
        # If no examples found for any type, raise error
        if not examples_by_type:
            raise ValueError(
                f"No training examples found for requested signal types: {set(signal_requests)}"
            )
        
        # Build the examples section
        examples_text = ""
        for signal_type, examples in examples_by_type.items():
            examples_text += f"\n{signal_type} signals:\n"
            for ex in examples:
                examples_text += f"  - {ex}\n"
        
        # Build the requests section
        requests_text = ""
        for i, signal_type in enumerate(signal_requests, 1):
            requests_text += f"{i}. {signal_type}\n"
        
        prompt = f"""You are generating synthetic banking social signals for testing purposes.

TRAINING EXAMPLES:
{examples_text}

TASK: Generate {len(signal_requests)} new, original signals based on the following types:
{requests_text}

REQUIREMENTS for each signal:
- Match the style and tone of the corresponding type examples
- Be realistic and natural-sounding
- Be a single sentence or short phrase
- Use {{bank_name}} as a placeholder where a bank name would appear
- DO NOT copy the examples directly - be inspired by their style
- Each signal should be unique and varied
- Keep signals concise (under 100 words each)

OUTPUT FORMAT:
Return ONLY a JSON array with exactly {len(signal_requests)} strings, one for each requested signal type, in order.
Example format: ["signal 1 text here", "signal 2 text here", "signal 3 text here"]

Generate the JSON array now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a synthetic data generator for banking social signals. Generate realistic, varied signals.Avoid any proper nouns. Always respond with valid JSON arrays only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.9
            )
            
            generated_text = response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            generated_text = re.sub(r'```json\s*|\s*```', '', generated_text)
            generated_signals = json.loads(generated_text)
            
            # Validate we got the right number of signals
            if not isinstance(generated_signals, list):
                raise ValueError("Response is not a list")
            
            if len(generated_signals) != len(signal_requests):
                raise ValueError(
                    f"Expected {len(signal_requests)} signals, got {len(generated_signals)}. "
                    f"Response: {generated_text[:200]}"
                )
            
            # Clean up each signal
            generated_signals = [str(s).strip().strip('"\'') for s in generated_signals]
            
            # Validate all signals are non-empty
            if any(not s for s in generated_signals):
                raise ValueError("One or more generated signals are empty")
            
            return generated_signals
            
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(
                f"Failed to parse AI response: {e}\n"
                f"Response was: {generated_text[:300]}..."
            )


class SyntheticDataGenerator:
    """
    Generate realistic synthetic banking social signals.
    EXCLUSIVE: Uses AI-powered batch generation - no templates.
    """
    
    SIGNAL_TYPES = ['Positive', 'Negative', 'Neutral', 'Gibberish']
    
    BANK_NAMES = [
        'ADAN Bank', 'Pineapple Savings', 'Feynman Bank',
        'Zebra Capital', 'Nebula Bank', 'Quantum Trust'
    ]
    
    SOURCE_TYPES = ['public_forum', 'social_media', 'review_site', 'community_board']
    
    def __init__(self, ai_generator: AISignalGenerator):
        self.generation_count = 0
        self.ai_generator = ai_generator
    
    def _fill_bank_name(self, text: str) -> str:
        """Replace {bank_name} placeholder with random bank name."""
        return text.replace('{bank_name}', random.choice(self.BANK_NAMES))
    
    def generate_dataset(self, total_records: int = 100) -> List[Dict]:
        """
        Generate dataset with all records in a single AI API call.
        Uses current timestamp for all records.
        
        Args:
            total_records: Total number of records to generate
            
        Returns:
            List of synthetic data records
        """
        dataset = []
        
        # Step 1: Randomly determine signal types for all records
        signal_types = [random.choice(self.SIGNAL_TYPES) for _ in range(total_records)]
        
        # Step 2: Generate ALL signal texts in one API call
        signal_texts = self.ai_generator.generate_batch_signals(signal_types)
        
        # Get current timestamp (will be same for all records in this batch)
        current_timestamp = datetime.utcnow()
        
        # Step 3: Create full records with metadata
        for i in range(total_records):
            # Fill in bank name placeholder
            raw_text = self._fill_bank_name(signal_texts[i])
            
            record = {
                'synthetic_id': str(uuid.uuid4()),
                'timestamp': current_timestamp.isoformat() + 'Z',
                'raw_text': raw_text,
                'source_type': random.choice(self.SOURCE_TYPES),
                'category': 'None',  # Always set to "None" as requested
                'generation_sequence': self.generation_count
            }
            
            self.generation_count += 1
            dataset.append(record)
        
        return dataset


class DataPipeline:
    """
    Orchestrates the complete data generation and anonymization pipeline.
    Ensures governance and auditability at every step.
    EXCLUSIVE: Requires OpenAI API - no fallback mode.
    """
    
    def __init__(self, output_file: str = "synthetic_dataset.json", 
                 training_file: str = "training_data.csv",
                 openai_api_key: str = None):
        self.output_file = Path(output_file)
        
        # Validate API key is provided
        if not openai_api_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Set OPENAI_API_KEY environment variable or provide openai_api_key parameter."
            )
        
        # Initialize training data loader
        self.training_loader = TrainingDataLoader(training_file)
        
        # Initialize AI generator (REQUIRED)
        self.ai_generator = AISignalGenerator(self.training_loader, openai_api_key)
        
        # Initialize components
        self.anonymizer = PIIAnonymizer()
        self.generator = SyntheticDataGenerator(self.ai_generator)
        
        self.pipeline_id = str(uuid.uuid4())
        self.total_records_generated = 0
        self.total_batches = 0
        self.total_api_calls = 0
    
    def execute_batch(self, num_records: int = 100) -> Tuple[List[Dict], Dict]:
        """
        Execute single batch: Generate -> Scrub -> Validate -> Save
        Makes only ONE API call regardless of num_records.
        
        Args:
            num_records: Number of synthetic records to generate
            
        Returns:
            Tuple of (processed_dataset, batch_report)
        """
        start_time = datetime.utcnow()
        
        # Stage 1: Generate synthetic data (SINGLE API CALL for all records)
        raw_dataset = self.generator.generate_dataset(num_records)
        
        # Track API calls (always 1 per batch)
        self.total_api_calls += 1
        
        # Stage 2: Anonymize all records (including currency amounts)
        anonymized_dataset = []
        total_pii_found = 0
        
        for record in raw_dataset:
            scrubbed_text, pii_count = self.anonymizer.scrub_text(record['raw_text'])
            
            anonymized_record = record.copy()
            anonymized_record['raw_text'] = scrubbed_text
            anonymized_record['pii_scrubbed_count'] = pii_count
            anonymized_dataset.append(anonymized_record)
            total_pii_found += pii_count
        
        # Stage 3: Validation
        validation_results = self._validate_dataset(anonymized_dataset)
        
        # Stage 4: Persist to disk
        self._save_dataset(anonymized_dataset)
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Update counters
        self.total_records_generated += len(anonymized_dataset)
        self.total_batches += 1
        
        # Generate batch report
        report = {
            'batch_number': self.total_batches,
            'execution_time_seconds': execution_time,
            'records_in_batch': len(anonymized_dataset),
            'total_records_so_far': self.total_records_generated,
            'pii_scrubbed_in_batch': total_pii_found,
            'validation_passed': validation_results['passed'],
            'api_calls_this_batch': 1,
            'total_api_calls': self.total_api_calls
        }
        
        return anonymized_dataset, report
    
    def _validate_dataset(self, dataset: List[Dict]) -> Dict:
        """Validate dataset meets quality and privacy requirements."""
        validation = {
            'passed': True,
            'checks': []
        }
        
        # Check 1: No PII patterns remain (regex patterns only, names are handled by spaCy)
        pii_check = {'name': 'PII_Residual_Check', 'passed': True, 'issues': []}
        for record in dataset:
            for pattern_name, (pattern, _) in PIIAnonymizer.PII_PATTERNS.items():
                if re.search(pattern, record['raw_text'], re.IGNORECASE):
                    pii_check['passed'] = False
                    pii_check['issues'].append(f"Found {pattern_name} in {record['synthetic_id']}")
        
        validation['checks'].append(pii_check)
        if not pii_check['passed']:
            validation['passed'] = False
        
        # Check 2: Schema completeness
        required_fields = ['synthetic_id', 'timestamp', 'raw_text', 'source_type', 'category']
        schema_check = {'name': 'Schema_Completeness', 'passed': True, 'issues': []}
        
        for record in dataset:
            for field in required_fields:
                if field not in record:
                    schema_check['passed'] = False
                    schema_check['issues'].append(f"Missing {field} in {record.get('synthetic_id', 'unknown')}")
            
            # Verify category is "None"
            if record.get('category') != 'None':
                schema_check['passed'] = False
                schema_check['issues'].append(f"Category is not 'None' in {record.get('synthetic_id', 'unknown')}")
        
        validation['checks'].append(schema_check)
        if not schema_check['passed']:
            validation['passed'] = False
        
        return validation
    
    def _save_dataset(self, dataset: List[Dict]) -> None:
        """Append anonymized dataset to single JSON file."""
        # Read existing data if file exists, otherwise start with empty list
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Append new dataset
        existing_data.extend(dataset)
        
        # Write back
        with open(self.output_file, 'w') as f:
            json.dump(existing_data, f, indent=2)


def continuous_generation(interval_seconds: int = 5, 
                         training_file: str = "training_data.csv",
                         openai_api_key: str = None):
    """
    Continuously generate data batches until stopped.
    Each batch generates a random number of records (1-10).
    EXCLUSIVE: Requires OpenAI API key - will exit if not provided.
    OPTIMIZED: Only 1 API call per batch regardless of number of records.
    
    Args:
        interval_seconds: Seconds to wait between batches
        training_file: Path to CSV training data file
        openai_api_key: OpenAI API key for AI-powered generation (REQUIRED)
    """
    global STOP_GENERATION
    
    print("\n" + "="*70)
    print("BANKING SOCIAL SIGNAL INTELLIGENCE SYSTEM")
    print("Module 1: Synthetic Data & Anonymization Engine (Production Mode)")
    print("="*70)
    print(f"\n⚙️  Configuration:")
    print(f"   - Records per batch: RANDOM (1-10)")
    print(f"   - API calls per batch: 1 (optimized batch generation)")
    print(f"   - Generation interval: {interval_seconds} seconds")
    print(f"   - Training data: {training_file}")
    print(f"   - AI Generation: EXCLUSIVE (OpenAI API required)")
    print(f"   - Currency anonymization: ENABLED")
    print(f"   - Timestamp mode: CURRENT TIME")
    print(f"   - Category value: None")
    print(f"   - Output: synthetic_dataset.json")
    print(f"\n🛑 Press Ctrl+C to stop gracefully")
    print("="*70 + "\n")
    
    # Validate API key
    if not openai_api_key:
        print("❌ ERROR: OpenAI API key is required!")
        print("   Set OPENAI_API_KEY environment variable:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Initialize pipeline
    try:
        pipeline = DataPipeline(
            training_file=training_file,
            openai_api_key=openai_api_key
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Track start time
    start_time = time.time()
    
    try:
        while not STOP_GENERATION:
            batch_start = time.time()
            
            # Generate random number of records (1-10 inclusive)
            records_per_batch = random.randint(1, 3)
            
            # Execute batch
            print(f"[BATCH {pipeline.total_batches + 1}] Generating {records_per_batch} records (1 API call)...")
            
            try:
                dataset, report = pipeline.execute_batch(num_records=records_per_batch)
            except Exception as e:
                print(f"❌ ERROR in batch generation: {e}")
                print("   Skipping this batch and continuing...")
                time.sleep(interval_seconds)
                continue
            
            batch_time = time.time() - batch_start
            total_time = time.time() - start_time
            
            # Display batch summary
            print(f"✅ Batch {report['batch_number']} complete:")
            print(f"   - Records generated: {report['records_in_batch']}")
            print(f"   - API calls this batch: {report['api_calls_this_batch']}")
            print(f"   - Total API calls: {report['total_api_calls']}")
            print(f"   - PII scrubbed: {report['pii_scrubbed_in_batch']}")
            print(f"   - Validation: {'PASSED ✓' if report['validation_passed'] else 'FAILED ✗'}")
            print(f"   - Batch time: {batch_time:.2f}s")
            print(f"   - Total records: {report['total_records_so_far']}")
            print(f"   - Total runtime: {total_time:.1f}s")
            print(f"   - Next batch in: {interval_seconds}s...\n")
            
            # Wait for next batch (check STOP_GENERATION every second)
            for i in range(interval_seconds):
                if STOP_GENERATION:
                    break
                time.sleep(1)
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Final summary
        total_runtime = time.time() - start_time
        print("\n" + "="*70)
        print("GENERATION STOPPED")
        print("="*70)
        print(f"📊 Final Statistics:")
        print(f"   - Total batches: {pipeline.total_batches}")
        print(f"   - Total records: {pipeline.total_records_generated}")
        print(f"   - Total API calls: {pipeline.total_api_calls}")
        if pipeline.total_api_calls > 0:
            print(f"   - Avg records per API call: {pipeline.total_records_generated / pipeline.total_api_calls:.1f}")
        print(f"   - Total runtime: {total_runtime:.1f}s ({total_runtime/60:.1f} minutes)")
        if total_runtime > 0:
            print(f"   - Average records/second: {pipeline.total_records_generated/total_runtime:.2f}")
        print(f"   - Output file: synthetic_dataset.json")
        print(f"\n✅ All data saved successfully!")
        print("="*70 + "\n")


def main():
    """
    Main execution function for Module 1.
    Runs continuous generation with graceful shutdown.
    
    REQUIRED: Set your OpenAI API key as environment variable:
    export OPENAI_API_KEY='your-api-key-here'
    """
    import os
    
    # Get OpenAI API key from environment variable
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    continuous_generation(
        interval_seconds=20,
        training_file="training_data.csv",
        openai_api_key=openai_api_key
    )


if __name__ == "__main__":
    main()
