# Banking Social Signal Intelligence System
## Module 1: Synthetic Data & Anonymization Engine

A production-ready Python system for generating synthetic banking-related social signals with enterprise-grade PII (Personally Identifiable Information) anonymization. **Powered exclusively by OpenAI GPT-4 with optimized batch processing.**

---

## 🎯 Overview

This system continuously generates realistic synthetic banking social media data while ensuring **zero PII retention** through multi-layer anonymization. The system **exclusively uses OpenAI's GPT-4** to generate contextually accurate signals based on training data.

**🚀 KEY FEATURES**:
- **Exclusive OpenAI API**: No template fallback - pure AI generation
- **Single API Call Per Batch**: Generates 1-10 signals at once (80% cost savings!)
- **Currency Anonymization**: Automatically masks all dollar amounts
- **Current Timestamps**: Uses real-time timestamps instead of random dates
- **Category Neutralization**: All records have category set to "None"

Perfect for:
- Testing banking sentiment analysis systems
- Training machine learning models without privacy concerns
- Simulating social signal monitoring pipelines
- Compliance-friendly data generation for financial applications

---

## ✨ Features

### Core Capabilities
- ✅ **Exclusive AI Generation**: 100% OpenAI-powered, no templates
- ✅ **Optimized Batch API Calls**: Single API call generates 1-10 signals at once
- ✅ **Random Batch Sizes**: Generates 1-10 records per batch (randomized)
- ✅ **Training Data Integration**: Learns from CSV training data with 4 signal types
- ✅ **Enhanced PII Anonymization**: 
  - spaCy NER for person name detection
  - Regex patterns for emails, phone numbers, SSNs, account numbers, credit cards
  - **NEW: Currency amount anonymization** (masks all dollar values)
- ✅ **Current Timestamps**: Uses actual current time for all records
- ✅ **Category Neutralization**: All records have `category: "None"`
- ✅ **Validation Pipeline**: Ensures no PII residue in output
- ✅ **Graceful Shutdown**: Ctrl+C handling with complete batch processing
- ✅ **Real-time Statistics**: Batch-by-batch progress with API call tracking

### Data Categories (Training Only)
The training data includes four categories, but **all generated records have `category: "None"`**:
1. **Positive**: Positive customer feedback and satisfaction
2. **Negative**: Customer complaints and frustrations
3. **Neutral**: General financial observations and thoughts
4. **Gibberish**: Random, off-topic social chatter

---

## 💡 Key Improvements

### 1. Exclusive OpenAI API Usage
**No template fallback** - system requires OpenAI API key and will exit if not provided or if API fails critically.

### 2. Currency Anonymization
Automatically detects and masks:
- Dollar amounts: `$1,234.56` → `<MASKED>`
- Written amounts: `1234 dollars` → `<MASKED>`
- USD notation: `1234.56 USD` → `<MASKED>`

### 3. Current Timestamps
All records in a batch share the **same current timestamp** (when batch was generated), not random historical dates.

**Example**:
```json
"timestamp": "2026-02-01T14:23:45Z"  // Current time when batch was created
```

### 4. Category Neutralization
All records have `category: "None"` instead of signal type classification.

---

## 📋 Requirements

- Python 3.8 or higher
- pip package manager
- Internet connection (for spaCy model download and OpenAI API calls)
- **OpenAI API key** (REQUIRED - no fallback mode)

---

## 🚀 Installation

### 1. Clone or Download
```bash
# If you have the files, navigate to the directory
cd /path/to/banking-signal-generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: On first run, the spaCy English language model (`en_core_web_sm`) will be downloaded automatically.

### 3. Set Up OpenAI API Key (REQUIRED)

#### Option A: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY='your-openai-api-key-here'
```

#### Option B: Modify the Code
Edit `synthetic_data_generator.py` and replace this line in the `main()` function:
```python
openai_api_key = os.getenv('OPENAI_API_KEY')
```

with:
```python
openai_api_key = 'your-openai-api-key-here'
```

**CRITICAL**: Without an API key, the system will exit with an error message.

---

## 💻 Usage

### Basic Usage
Run the generator:

```bash
export OPENAI_API_KEY='sk-...'
python synthetic_data_generator.py
```

This will:
- Generate **1-10 random records** every 5 seconds
- Use **1 API call per batch** (not N calls!)
- Use **exclusive OpenAI generation** (no templates)
- Save to `synthetic_dataset.json` in the current directory
- Load training data from `training_data.csv`
- Set all timestamps to **current time**
- Set all categories to **"None"**
- **Anonymize currency amounts**

### Error Handling
If OpenAI API key is missing:
```
❌ ERROR: OpenAI API key is required!
   Set OPENAI_API_KEY environment variable:
   export OPENAI_API_KEY='your-api-key-here'
```

### Stopping the Generator
Press **Ctrl+C** to gracefully stop generation. The current batch will complete before shutdown.

---

## 📂 Files

### Required Files
1. **`synthetic_data_generator.py`** - Main Python script (OpenAI exclusive!)
2. **`training_data.csv`** - Training examples (80 signals across 4 types) **REQUIRED**
3. **`requirements.txt`** - Python dependencies

### Output File
- **`synthetic_dataset.json`** - Generated synthetic signals (created automatically)

---

## 📊 Training Data Format

The `training_data.csv` file contains examples for the AI to learn from:

```csv
Number,Signals,Type
1,"why does my brain remember song lyrics...",Gibberish
21,"checked my bank app three times...",Neutral
41,"{bank_name} keeps declining transactions...",Negative
61,"{bank_name} app is smooth and reliable",Positive
```

**Key Points**:
- Use `{bank_name}` as a placeholder where bank names should appear
- The AI learns tone, style, and structure from these examples
- Types are used for training only - output records have `category: "None"`
- More training examples = better AI-generated signals

---

## 🔄 How It Works

### 1. Batch Preparation
- System randomly decides to generate N records (1-10)
- Randomly selects a signal type for each from training categories

### 2. Single Optimized API Call
Sends one prompt containing:
```
Generate 7 signals:
1. Positive
2. Negative
3. Neutral
4. Gibberish
5. Positive
6. Neutral
7. Negative

Examples for each type: [provided]
Return: JSON array with exactly 7 strings
```

### 3. Response Processing
- Receives JSON array: `["signal 1", "signal 2", ..., "signal 7"]`
- Validates count matches request
- Handles parsing errors (exits if critical)

### 4. Post-Processing
- Gets current timestamp (UTC)
- Replaces `{bank_name}` with random bank names
- Applies PII anonymization (names, emails, phone, SSN, accounts, **currency**)
- Sets `category: "None"` for all records
- Validates and saves

**Result**: All N signals generated with 1 API call, current timestamps, no categories, and anonymized currency!

---

## 📈 Output

### Output File
- **Filename**: `synthetic_dataset.json`
- **Location**: Same directory as the script
- **Format**: JSON array of records

### Record Schema
Each record contains:

```json
{
  "synthetic_id": "uuid-v4-string",
  "timestamp": "2026-02-01T14:23:45Z",  // Current time when generated
  "raw_text": "Anonymized text content",
  "source_type": "public_forum|social_media|review_site|community_board",
  "category": "None",  // Always "None"
  "generation_sequence": 0,
  "pii_scrubbed_count": 0
}
```

### Example Output
```json
[
  {
    "synthetic_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "timestamp": "2026-02-01T14:23:45Z",
    "raw_text": "Quantum Trust notifications arrive instantly and help me track my spending well",
    "source_type": "social_media",
    "category": "None",
    "generation_sequence": 0,
    "pii_scrubbed_count": 0
  },
  {
    "synthetic_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "timestamp": "2026-02-01T14:23:45Z",
    "raw_text": "Payment of <MASKED> failed without proper notification",
    "source_type": "review_site",
    "category": "None",
    "generation_sequence": 1,
    "pii_scrubbed_count": 1
  }
]
```

**Note**: The second example shows currency anonymization in action (`$850` → `<MASKED>`).

---

## 🔒 Privacy & Security

### Enhanced PII Detection

#### 1. spaCy Named Entity Recognition
- Detects person names using ML-based NER
- Replaces with `<MASKED>` token

#### 2. Regex Pattern Matching
Detects and masks:
- Email addresses
- Phone numbers (US format)
- Social Security Numbers (SSN)
- Account numbers
- Credit card numbers
- Routing numbers
- **Currency amounts** (NEW!)
  - `$1,234.56` format
  - `1234 dollars` format
  - `1234.56 USD` format

### Validation
Every batch undergoes validation to ensure:
- No PII patterns remain in output
- Schema completeness
- All categories are "None"
- Data integrity

---

## 📊 Performance

### Default Configuration
- **Records per batch**: 1-10 (random)
- **API calls per batch**: **1** (optimized!)
- **Batch interval**: 5 seconds
- **Expected throughput**: ~30-90 records/minute (variable)
- **Cost efficiency**: ~80% savings vs individual calls
- **Timestamp**: Current UTC time
- **Category**: Always "None"

### Sample Output
```
======================================================================
BANKING SOCIAL SIGNAL INTELLIGENCE SYSTEM
Module 1: Synthetic Data & Anonymization Engine (Production Mode)
======================================================================

⚙️  Configuration:
   - Records per batch: RANDOM (1-10)
   - API calls per batch: 1 (optimized batch generation)
   - Generation interval: 5 seconds
   - Training data: training_data.csv
   - AI Generation: EXCLUSIVE (OpenAI API required)
   - Currency anonymization: ENABLED
   - Timestamp mode: CURRENT TIME
   - Category value: None
   - Output: synthetic_dataset.json

🛑 Press Ctrl+C to stop gracefully
======================================================================

✅ Loaded 80 training examples from training_data.csv
✅ OpenAI API initialized successfully

[BATCH 1] Generating 7 records (1 API call)...
✅ Batch 1 complete:
   - Records generated: 7
   - API calls this batch: 1
   - Total API calls: 1
   - PII scrubbed: 2
   - Validation: PASSED ✓
   - Batch time: 1.84s
   - Total records: 7
   - Total runtime: 1.9s
   - Next batch in: 5s...
```

---

## 🛠️ Troubleshooting

### Missing OpenAI API Key
```
❌ ERROR: OpenAI API key is required!
```
**Solution**: Set environment variable or provide in code.

### Training File Not Found
```
FileNotFoundError: Training file 'training_data.csv' not found.
```
**Solution**: Ensure `training_data.csv` is in the same directory.

### OpenAI API Errors
The system will show specific error messages and:
- Skip problematic batches
- Continue with next batch
- Display full error details

### Rate Limiting
- OpenAI has rate limits on API calls
- Increase `interval_seconds` if hitting limits
- With batch optimization, you're already minimizing calls!

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm
```

### Permission Issues
```bash
chmod +w .
```

---

## 💰 Cost Considerations

### OpenAI API Costs (Optimized!)
- **Model**: GPT-4o-mini
- **Batch call cost**: ~$0.0003 for 10 signals (vs ~$0.0015 individual)
- **Daily estimate** (at avg 5 signals/batch, 60 batches/hour, 8 hours): ~$1.44
- **Monthly estimate** (20 working days): ~$28.80

**Cost Savings vs Non-Optimized**:
- **Individual calls**: ~$144/month
- **Batch calls**: ~$29/month
- **Savings**: **~80% reduction!**

---

## 🔧 Advanced Usage

### Programmatic Integration

```python
from synthetic_data_generator import DataPipeline

# Initialize pipeline (API key required!)
pipeline = DataPipeline(
    output_file="custom_output.json",
    training_file="my_training_data.csv",
    openai_api_key="sk-..."
)

# Generate single batch (only 1 API call for all 50 records!)
dataset, report = pipeline.execute_batch(num_records=50)

print(f"Generated {len(dataset)} records")
print(f"All timestamps: {dataset[0]['timestamp']}")  # Current time
print(f"All categories: {dataset[0]['category']}")  # "None"
print(f"API calls made: {report['api_calls_this_batch']}")  # 1
print(f"Currency masked: {report['pii_scrubbed_in_batch']}")
```

---

## 📄 License

This is enterprise banking software. Ensure compliance with your organization's data governance policies and OpenAI's usage policies.

---

## 🔄 Version History

- **v3.0**: **EXCLUSIVE OpenAI API** + currency anonymization + current timestamps + category="None"
- **v2.1**: Optimized - Single API call per batch (80% cost reduction)
- **v2.0**: AI-powered generation with OpenAI GPT-4
- **v1.0**: Initial release with template generation

---

## ⚠️ Important Notes

1. **OpenAI API Required**: System will not run without valid API key
2. **No Fallback Mode**: All generation is OpenAI-powered
3. **Currency Anonymization**: All dollar amounts are masked
4. **Current Timestamps**: All records use actual current time
5. **Category Always None**: All records have `category: "None"`
6. **Training Data Required**: Must have `training_data.csv` file
7. **Output File Growth**: The `synthetic_dataset.json` file will grow continuously
8. **API Costs**: Monitor your OpenAI dashboard regularly
9. **Internet Required**: For OpenAI API calls and spaCy model

---

## 🚀 Quick Start Checklist

- [ ] Install Python 3.8+
- [ ] Run `pip install -r requirements.txt`
- [ ] Get OpenAI API key from https://platform.openai.com/api-keys
- [ ] Set `export OPENAI_API_KEY='your-key'` (**REQUIRED**)
- [ ] Verify `training_data.csv` is present
- [ ] Run `python synthetic_data_generator.py`
- [ ] Observe "1 API call" in batch output
- [ ] Verify all categories are "None" in output
- [ ] Verify timestamps are current time
- [ ] Check currency amounts are masked
- [ ] Press Ctrl+C to stop
- [ ] Review `synthetic_dataset.json`

---

**Built with exclusive AI power, privacy, optimization, and compliance at its core. Happy generating! 🚀**

**✨ NEW: Exclusive OpenAI API + Currency Anonymization + Current Timestamps + Category="None" ✨**
