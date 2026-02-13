# Adan – AI Multi-Modal Social Signal Intelligence System for Mashreq Bank

This project was a result of the hackathon(specifically a bounty challenge) attended by our team (Team Eclipse) at the University Of Birmingham Dubai.
The bounty was set by [Mashreq Bank](https://www.mashreq.com/en/uae/neo/).

## Project Overview

- **Enterprise-grade AI system** for real-time social signal intelligence and risk detection
- **Multi-modal pipeline** combining synthetic data generation, AI analysis, and human oversight
- **Zero autonomous action** — all critical decisions require human approval (HITL)
- **Privacy-first architecture** — no PII storage or processing
- **Real-time monitoring** with intelligent risk classification and team routing
- Built for **financial institutions** requiring transparent AI governance

---

## Key Capabilities

-  **PR Agent** — Automated public response drafting with human review
-  **Advanced Analytics Dashboard** — Real-time signal visualization and trend analysis
-  **Risk Detection Management** — Critical/High/Medium/Low urgency classification
-  **Synthetic Data Generation** — Simulates social signals every 10 seconds for testing
-  **Modern UI** — Clean, professional interface with live updates
-  **Signal Summarization** — AI-powered impact assessment and reasoning logs
-  **Explanation Engine** — Transparent reasoning for Critical/Moderate/Average classifications
-  **Team Channelization** — Routes signals to relevant departments (IT Ops, Fraud, Comms)
-  **HITL Approval Workflow** — Approve/Decline actions with full audit logging
-  **No PII Storage** — Privacy-compliant architecture
-  **Confidence Score Classification** — Ambiguity detection and uncertainty quantification
-  **Executive Briefing Export** — PDF generation for leadership reporting
-  **Audit Trail** — Immutable governance logs for compliance

---

## System Architecture (4-Module Pipeline)

### **Module 1: Data Ingestion & Privacy Guardrails**
- **Responsibility:** Synthetic data generation and strict PII scrubbing
- **Technologies:** Python, spaCy NLP, OpenAI API
- **Key Functions:**
  - Generates high-quality synthetic banking commentary (positive, negative, neutral)
  - Implements "Privacy Shield" to scan incoming text
  - Removes PII (names, phone numbers, account IDs) before processing
  - Outputs structured JSON with metadata
  - Tracks `pii_scrubbed_count` for audit compliance
- **Output Format:** JSON with fields: `synthetic_id`, `timestamp`, `raw_text`, `source_type`, `category`, `pii_scrubbed_count`

### **Module 2: Risk & Sentiment Analytical Engine**
- **Responsibility:** Classification and confidence scoring
- **Technologies:** LangChain, OpenAI GPT-4, Custom NLP Models
- **Key Functions:**
  - Identifies signal category (Service Outage, Fraud Alert, Misinformation, Product Inquiry)
  - Calculates sentiment score (-1.0 to 1.0 scale)
  - Computes confidence score (0-100%) based on keyword density and model certainty
  - Assigns `scenario_category` for routing
  - Flags ambiguous signals for human review
- **Output Enhancement:** Adds `sentiment_score`, `scenario_category`, `confidence_score` to JSON

### **Module 3: Agentic Reasoning & Response Generator**
- **Responsibility:** Explainability and "Why this matters"
- **Technologies:** LangChain Agents, OpenAI GPT-4, Pydantic Validation
- **Key Functions:**
  - Builds LLM agent that generates detailed "Signal Explanation"
  - Explains potential impact on bank operations and reputation
  - Drafts suggested internal responses or external holding statements
  - Creates reasoning matrices with structured impact assessments
  - Assigns urgency levels (Critical, High, Medium, Low)
  - Generates `module3_suggested_action` for human review
- **Output Enhancement:** Adds `module3_explanation`, `module3_impact_assessment`, `module3_suggested_action`, `shadow_review_urgency` to JSON
- **File Output:** Writes enriched data to `module3_reasoning/agentic_output.json`

### **Module 4: Governance & Executive Dashboard**
- **Responsibility:** Human-in-the-loop and Executive Briefing
- **Technologies:** FastAPI, WebSockets, HTML/TailwindCSS, Chart.js
- **Key Functions:**
  - Reads `agentic_output.json` from Module 3
  - Displays aggregated signals in real-time dashboard
  - Provides "Approve/Decline" workflow for every flagged action
  - Logs all human decisions in audit database
  - Generates Executive Insight Briefing (1-page PDF report)
  - Routes approved actions to target departments
  - Implements PR Agent for public response management
- **User Interface:** Multi-page dashboard with analytics, governance logs, and PR workflow

---

## Pipeline Flow Tree

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ADAN SSIS PIPELINE ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────┘

[Synthetic Data Sources]
   │
   └─ AI-Generated Banking Signals (Every 10 seconds)
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MODULE 1: Data Ingestion & Privacy Guardrails                          │
│  ─────────────────────────────────────────────────                      │
│  • Synthetic Data Generation (OpenAI LLM)                               │
│  • PII Detection (spaCy NER)                                            │
│  • Privacy Shield Scrubbing                                             │
│  • Initial JSON Structure Creation                                      │
│                                                                          │
│  OUTPUT: base_signal.json                                               │
│  {                                                                       │
│    "synthetic_id": "SYN-2026-001",                                      │
│    "raw_text": "...",                                                   │
│    "pii_scrubbed_count": 0,                                             │
│    "source_type": "Synthetic Forum"                                     │
│  }                                                                       │
└──────────────────────────────────────────────────────────────────────────┘
   │
   │ [JSON Transfer]
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MODULE 2: Risk & Sentiment Analytical Engine                           │
│  ───────────────────────────────────────────────                        │
│  • Sentiment Analysis (-1.0 to 1.0)                                     │
│  • Scenario Classification (4 categories)                               │
│  • Confidence Scoring (0-100%)                                          │
│  • Keyword Density Analysis                                             │
│  • Ambiguity Detection                                                  │
│                                                                          │
│  OUTPUT: enriched_signal.json                                           │
│  {                                                                       │
│    ...base_signal,                                                      │
│    "sentiment_score": -0.85,                                            │
│    "scenario_category": "Service Outage",                               │
│    "confidence_score": 92                                               │
│  }                                                                       │
└──────────────────────────────────────────────────────────────────────────┘
   │
   │ [JSON Transfer]
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MODULE 3: Agentic Reasoning & Response Generator                       │
│  ──────────────────────────────────────────────────                     │
│  • LangChain Agent Initialization                                       │
│  • Impact Assessment Generation                                         │
│  • Reasoning Matrix Construction                                        │
│  • Urgency Level Assignment                                             │
│  • Suggested Action Drafting                                            │
│  • Explainability Report Creation                                       │
│                                                                          │
│  OUTPUT: module3_reasoning/agentic_output.json                          │
│  {                                                                       │
│    ...enriched_signal,                                                  │
│    "module3_explanation": {                                             │
│      "reputational_risk": "High",                                       │
│      "operational_impact": "Critical"                                   │
│    },                                                                    │
│    "module3_impact_assessment": {                                       │
│      "severity": "Severe operational risk",                             │
│      "affected_services": ["Mobile Banking", "Login"]                   │
│    },                                                                    │
│    "module3_suggested_action": "Deploy emergency bridge",               │
│    "shadow_review_urgency": "Critical",                                 │
│    "is_flagged_for_review": true                                        │
│  }                                                                       │
└──────────────────────────────────────────────────────────────────────────┘
   │
   │ [JSON File Reading]
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MODULE 4: Governance & Executive Dashboard                             │
│  ─────────────────────────────────────────────────                      │
│  ┌────────────────────────────────────────────────┐                    │
│  │  FastAPI Backend (main.py)                     │                    │
│  │  • Reads agentic_output.json                   │                    │
│  │  • Serves /api/analytics-data endpoint         │                    │
│  │  • WebSocket live updates                      │                    │
│  │  • Audit log persistence                       │                    │
│  └────────────────────────────────────────────────┘                    │
│                     │                                                    │
│                     │ [HTTP/WebSocket]                                  │
│                     ▼                                                    │
│  ┌────────────────────────────────────────────────┐                    │
│  │  Frontend UI (HTML/TailwindCSS/Chart.js)       │                    │
│  │  ┌──────────────────────────────────────────┐  │                    │
│  │  │  Dashboard (/):                          │  │                    │
│  │  │  • Real-time signal cards                │  │                    │
│  │  │  • Approve/Decline buttons               │  │                    │
│  │  │  • Live statistics                       │  │                    │
│  │  │  • Risk distribution charts              │  │                    │
│  │  └──────────────────────────────────────────┘  │                    │
│  │  ┌──────────────────────────────────────────┐  │                    │
│  │  │  Analytics (/analytics):                 │  │                    │
│  │  │  • Scatter plots                         │  │                    │
│  │  │  • Scenario distribution                 │  │                    │
│  │  │  • Gauge charts                          │  │                    │
│  │  └──────────────────────────────────────────┘  │                    │
│  │  ┌──────────────────────────────────────────┐  │                    │
│  │  │  Governance (/governance):               │  │                    │
│  │  │  • Immutable audit logs                  │  │                    │
│  │  │  • Decision history                      │  │                    │
│  │  │  • Compliance reports                    │  │                    │
│  │  └──────────────────────────────────────────┘  │                    │
│  │  ┌──────────────────────────────────────────┐  │                    │
│  │  │  PR Agent (/pr-agent):                   │  │                    │
│  │  │  • Signal simulation                     │  │                    │
│  │  │  • AI response drafting                  │  │                    │
│  │  │  • Human editing & approval              │  │                    │
│  │  │  • Public noticeboard                    │  │                    │
│  │  └──────────────────────────────────────────┘  │                    │
│  └────────────────────────────────────────────────┘                    │
│                     │                                                    │
│                     │ [User Actions]                                    │
│                     ▼                                                    │
│  ┌────────────────────────────────────────────────┐                    │
│  │  Human-in-the-Loop Decision Layer              │                    │
│  │  • Approve Signal → Route to Department        │                    │
│  │  • Decline Signal → Archive & Log              │                    │
│  │  • Edit PR Response → Update & Broadcast       │                    │
│  │  • Generate Executive Brief → Export PDF       │                    │
│  └────────────────────────────────────────────────┘                    │
│                     │                                                    │
│                     ▼                                                    │
│  [Updates agentic_output.json & audit_db]                              │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ├─────► Target Department (IT Ops, Fraud, Comms)
   ├─────► Public Relations (Approved Statements)
   └─────► Executive Leadership (PDF Briefing)
```

---

## PR Agent: Key Feature Deep Dive

### **What is the PR Agent?**
- **Intelligent public response system** for crisis communication and brand management
- **AI-powered drafting** combined with mandatory human approval
- **Context-aware response generation** based on signal category and sentiment
- **Editable workflow** allowing human refinement before publishing

### **How PR Agent Works**

#### **Step 1: Signal Detection**
- User simulates or system detects a public-facing signal
- Categories: Security Alert, Market Rumor, Product Inquiry, Privacy Concern
- Signal routed to PR Agent interface (`/pr-agent`)

#### **Step 2: Human Review & Editing**
- **Display Mode:** Shows AI-generated response with reasoning
- **Edit Mode:** Human can modify text while preserving intent
- **Approve/Reject Options:** Binary decision workflow
- **Real-time Preview:** See final message before publishing

#### **Step 3: Publication & Tracking**
- **Approved:** Posted to public noticeboard with timestamp
- **Logged:** Recorded in audit trail with decision metadata
- **Channeled:** Sent to relevant department (e.g., Security team notified)
- **Monitored:** Added to analytics dashboard for trend analysis

### **Why PR Agent is Critical**
- **Speed:** Drafts responses in seconds vs. hours
- **Consistency:** Maintains brand voice across all communications
- **Compliance:** Ensures legal review before publication
- **Transparency:** Full audit trail of AI suggestions and human edits
- **Scalability:** Handles multiple simultaneous crises
- **Learning:** Improves over time based on approved responses

---

## Technology Stack

### **Frontend**
- **HTML5** + **TailwindCSS** (CDN)
- **Chart.js** (v4.x) — Data visualization
- **html2pdf.js** (v0.10.1) — PDF export
- **WebSocket** — Real-time updates
- **Vanilla JavaScript** — No framework dependencies

### **Backend**
- **Python** 3.11+
- **FastAPI** 0.100.0+ — High-performance async API
- **Uvicorn** 0.25.0+ — ASGI server

### **AI Framework**
- **LangChain** 0.2.11 — Agent orchestration
- **LangChain-OpenAI** 0.1.17 — OpenAI integration
- **LangChain-Core** 0.1.0+ — Core abstractions
- **OpenAI API** 1.58.1+ — GPT-4 reasoning engine
- **spaCy** 3.7.2 — NLP and entity recognition
- **en_core_web_sm** 3.7.1 — English language model

### **Data & Configuration**
- **Pydantic** 2.0.0+ — Data validation
- **python-dotenv** 1.0.0+ — Environment management
- **JSON** — Data persistence and exchange format

---



## Human-in-the-Loop Compliance

- **No autonomous actions** — AI generates recommendations only
- **Mandatory human approval** for all flagged signals
- **Dual-action workflow** — Approve or Decline required
- **Full audit logging** — Every decision timestamped and recorded
- **Transparent reasoning** — AI explains all classifications
- **Override capability** — Humans can edit AI-generated content
- **Governance dashboard** — Immutable log of all actions
- **Configurable thresholds** — Adjust urgency triggers without code changes

---

## Privacy & Data Security

- **Zero PII storage** — All personal data scrubbed before processing
- **Synthetic test data** — No real user information in demos
- **Environment-based secrets** — API keys stored in `.env` (never committed)
- **Read-only AI access** — Cannot modify source data
- **Audit compliance** — ISO 27001 compatible logging architecture
- **Data minimization** — Only essential metadata retained
- **Secure API design** — No exposed credentials in frontend
- **Privacy by design** — GDPR-aligned data handling

---

## Setup & Installation Instructions

### **Prerequisites**
- Python 3.11 or higher
- OpenAI API key (GPT-4 access recommended)
- Terminal/command line access
- Git installed

### **Step 1: Clone Repository**
```bash
git clone https://github.com/your-org/adan-ssis.git
cd adan-ssis
```

### **Step 2: Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### **Step 4: Configure Environment Variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### **Step 5: Create Required Directories**
```bash
mkdir -p module3_reasoning
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Important:**
- Never commit `.env` to version control
- Use `.env.example` as template (without real keys)
- OpenAI API key is required for AI analysis modules
- Keep credentials secure and rotate regularly

---

## How to Run the Project

### **Start the Backend Server**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Access the Application**
- **Dashboard:** http://localhost:8000
- **Analytics:** http://localhost:8000/analytics
- **Governance:** http://localhost:8000/governance
- **AI Logic:** http://localhost:8000/ai-logic
- **PR Agent:** http://localhost:8000/pr-agent

### **Test Synthetic Data Generation**
- Navigate to Dashboard
- Wait 8-10 seconds for automatic signal simulation
- Or manually trigger via PR Agent simulation buttons

### **Workflow Testing**
1. Open Dashboard to view active signals
2. Review AI impact assessments and reasoning matrices
3. Click "Approve" or "Decline" on flagged items
4. Check Governance page for audit logs
5. Use PR Agent for public response drafting and approval

---

## License

This project is licensed under the **MIT License**.

See `LICENSE` file for full terms.

---

## Additional Resources

### **Pipeline Data Flow Summary**
```
Module 1 → base_signal.json
    ↓
Module 2 → enriched_signal.json
    ↓
Module 3 → agentic_output.json
    ↓
Module 4 → Reads JSON → Displays UI → Human Decision → Updates JSON & Audit Log
```

### **JSON Schema Evolution**
- **After Module 1:** `synthetic_id`, `raw_text`, `pii_scrubbed_count`, `source_type`
- **After Module 2:** + `sentiment_score`, `scenario_category`, `confidence_score`
- **After Module 3:** + `module3_explanation`, `module3_impact_assessment`, `module3_suggested_action`, `shadow_review_urgency`, `is_flagged_for_review`

---

**Built with trust for truth and accuracy — Adan AI Multi-Modal Social Signal Intelligence System**
