# Module 5: AI Procurement Investigation & Recommendation Agent

## Overview

The AI Procurement Agent is an intelligent system that investigates procurement questions using natural language, retrieves structured data and ML insights, and provides evidence-based recommendations.

**Key Features:**
- Natural language question processing
- Integration with PostgreSQL procurement database
- Access to Module 4 ML outputs (scores, anomalies, forecasts)
- RAG-based procurement knowledge retrieval
- Evidence-based reasoning with source tracking
- RESTful API with FastAPI
- Interactive dashboard UI

---

## Architecture

```
User Question
      ↓
AI Procurement Agent (LangChain + OpenAI)
      ↓
Tool Selection & Orchestration
      ↓
┌─────────────────────────────────────────────┐
│ Database Tools (20+ SQL queries)            │
│ ML Tools (supplier scores, anomalies, etc.) │
│ RAG Tools (policy document retrieval)       │
└─────────────────────────────────────────────┘
      ↓
Evidence Collection & Analysis
      ↓
Structured Response
      ↓
Dashboard UI / API Response
```

---

## Components

### 1. Agent Core (`agent/agent.py`)

The main `ProcurementAgent` class:
- Initializes OpenAI LLM with function calling
- Manages 17 tools across database, ML, and RAG
- Executes queries with evidence tracking
- Returns structured responses

### 2. Database Tools (`agent/tools/database_tools.py`)

Read-only SQL tools:
- `get_supplier_info()` - Supplier details
- `get_supplier_performance_metrics()` - Performance metrics
- `get_spending_by_period()` - Spending trends
- `get_price_history()` - Price analysis
- `get_delivery_performance()` - Delivery metrics
- `get_quality_metrics()` - Quality/defect data
- `get_compliance_info()` - Compliance status
- And 13+ more tools

**Security:** All queries use parameterized SQL and read-only transactions.

### 3. ML Tools (`agent/tools/ml_tools.py`)

Access to Module 4 ML outputs:
- `get_supplier_scores()` - All supplier rankings
- `get_supplier_score(supplier)` - Specific supplier score
- `get_price_anomalies()` - Detected anomalies
- `get_demand_forecast(category)` - Demand predictions
- `get_supplier_anomalies(supplier)` - Supplier-specific anomalies
- And 8+ more tools

**Note:** Tools query existing ML tables; models are NOT recalculated.

### 4. RAG System (`agent/rag/`)

Retrieval-Augmented Generation for procurement knowledge:

**Components:**
- `document_loader.py` - Loads TXT, MD, PDF, DOCX files
- `chunker.py` - Splits documents with semantic overlap
- `vector_store.py` - ChromaDB for vector storage
- `retriever.py` - Queries relevant document chunks
- `ingestion.py` - Complete pipeline: load → chunk → embed → store
- `rag_tools.py` - Agent interface for retrieval

**Usage:**
```python
from agent.rag.ingestion import ingestion_pipeline

# Ingest documents from knowledge_base/
stats = ingestion_pipeline.ingest(reset=True)
print(f"Ingested {stats['chunks_stored']} chunks")
```

### 5. API (`agent/api/app.py`)

FastAPI REST endpoints:

**Endpoints:**
- `POST /api/agent/query` - Query the agent
- `GET /api/agent/status` - Agent status
- `POST /api/agent/ingest` - Ingest documents
- `GET /api/agent/rag/status` - RAG system status
- `GET /health` - Health check

**Run API:**
```bash
cd agent/api
python app.py
# API: http://localhost:8001
# Docs: http://localhost:8001/docs
```

### 6. Dashboard UI (`dashboard/pages/page5_ai_agent.py`)

Interactive interface integrated with existing Dash dashboard:
- Natural language question input
- Sample question buttons
- Real-time agent status indicator
- Structured response display
- Processing time and metadata
- Error handling

**Access:** http://localhost:8050/ai-procurement-agent

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `openai>=1.12.0` - LLM integration
- `langchain>=0.1.0` - Agent framework
- `chromadb>=0.4.22` - Vector database
- `fastapi>=0.109.0` - API framework
- `uvicorn>=0.27.0` - ASGI server

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
DB_USER=your_db_username
DB_PASSWORD=your_db_password

# Optional
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
ENABLE_RAG=true
```

### 3. Ingest Knowledge Base (Optional)

```bash
python << 'EOF'
from agent.rag.ingestion import ingestion_pipeline
stats = ingestion_pipeline.ingest(reset=True)
print(f"Success: {stats['success']}")
print(f"Documents: {stats['documents_loaded']}")
print(f"Chunks: {stats['chunks_stored']}")
EOF
```

### 4. Start Services

**Terminal 1 - Agent API:**
```bash
python agent/api/app.py
# Runs on http://localhost:8001
```

**Terminal 2 - Dashboard:**
```bash
python dashboard/app.py
# Runs on http://localhost:8050
```

---

## Usage Examples

### Via Python API

```python
from agent.agent import agent

# Query the agent
response = agent.query("Why is Beta_Supplies performing poorly?")

print(response['answer'])
print(f"ML insights used: {response['ml_insights_used']}")
print(f"Processing time: {response['processing_time_seconds']:.2f}s")
```

### Via REST API

```bash
curl -X POST http://localhost:8001/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which supplier should we consider for Electronics?"}'
```

### Via Dashboard

1. Navigate to http://localhost:8050/ai-procurement-agent
2. Enter question or click sample question
3. Click "Investigate"
4. Review structured response with evidence

---

## Supported Question Types

### 1. Supplier Investigation
"Why is Beta_Supplies performing poorly?"
- Retrieves supplier metrics
- Gets ML performance score
- Analyzes delivery, quality, compliance
- Provides detailed explanation

### 2. Price Anomaly Detection
"Are there any abnormal procurement prices?"
- Queries ML anomaly detection results
- Identifies high-severity anomalies
- Shows affected suppliers/categories
- Recommends investigation

### 3. Supplier Recommendation
"Which supplier should we consider for Electronics?"
- Compares supplier scores for category
- Reviews historical performance
- Checks for price anomalies
- Recommends best option with trade-offs

### 4. Demand Forecasting
"What is the expected procurement demand for Electronics?"
- Retrieves ML demand forecast
- Explains prediction with confidence intervals
- Mentions forecast limitations
- Provides planning guidance

### 5. Spending Analysis
"Why did procurement spending increase?"
- Analyzes spending by period
- Identifies quantity vs price changes
- Checks for supplier changes
- Provides evidence-based explanation

### 6. Combined Investigation
"Find suppliers with poor performance and price anomalies"
- Gets poor-performing suppliers (score <50)
- Retrieves anomalies for each
- Suggests alternatives
- Uses policy knowledge if available

---

## Response Format

Agent responses follow a structured format:

```
### Finding
Brief conclusion summarizing the answer

### Evidence
Relevant database facts (orders, metrics, prices)

### ML Insights
Scores, anomalies, or forecasts from Module 4

### Policy/Knowledge
Relevant policy information (if available from RAG)

### Analysis
Explanation of what the evidence means

### Recommendation
Specific actionable guidance

### Confidence / Limitations
Uncertainties or missing data
```

---

## Testing

### Run Tests

```bash
# All agent tests
pytest agent/tests/ -v

# Specific test file
pytest agent/tests/test_tools.py -v

# With coverage
pytest agent/tests/ --cov=agent --cov-report=html
```

### Test Files

- `agent/tests/test_tools.py` - Database, ML, and RAG tool tests

---

## Security

### Read-Only Database Access

All database tools use read-only transactions:
```python
conn.set_session(readonly=True, autocommit=True)
```

### Parameterized SQL

All queries use parameterized format to prevent SQL injection:
```python
query = "SELECT * FROM table WHERE col = %s"
cursor.execute(query, (user_input,))
```

### No Arbitrary SQL Execution

The agent cannot:
- Execute user-provided SQL
- DELETE, UPDATE, or INSERT data
- DROP tables or ALTER schema
- Execute shell commands

### API Key Protection

- API keys stored in `.env` (not committed to git)
- `.gitignore` includes `.env`
- Keys not exposed in logs or responses

---

## Limitations

### Current Limitations

1. **LLM Dependency**: Requires OpenAI API key and internet access
2. **English Only**: Optimized for English language questions
3. **Knowledge Base**: RAG quality depends on ingested documents
4. **Forecast Uncertainty**: Demand forecasts have ~48% relative error
5. **No Real-Time Data**: Queries historical database (not streaming)

### Known Issues

- Long questions (>500 tokens) may truncate
- Complex multi-step reasoning may require multiple iterations
- RAG retrieval quality varies with document structure
- Processing time 5-30 seconds depending on question complexity

---

## Troubleshooting

### Agent Not Available

**Problem:** Agent status shows "not available"

**Solutions:**
1. Check `OPENAI_API_KEY` is set in `.env`
2. Verify API key is valid
3. Check internet connectivity
4. Review logs for initialization errors

### Database Connection Failed

**Problem:** Tools return connection errors

**Solutions:**
1. Verify PostgreSQL is running
2. Check `DB_USER` and `DB_PASSWORD` in `.env`
3. Confirm database name is `procurement_intelligence`
4. Test connection: `psql -U username -d procurement_intelligence`

### RAG System Empty

**Problem:** "No relevant documents found"

**Solutions:**
1. Ingest documents: `python agent/rag/ingestion.py`
2. Check documents exist in `agent/knowledge_base/`
3. Verify `ENABLE_RAG=true` in `.env`
4. Check ChromaDB directory permissions

### Slow Response Times

**Problem:** Queries take >60 seconds

**Solutions:**
1. Reduce `MAX_TOOL_CALLS` in config
2. Use more specific questions
3. Check database query performance
4. Consider caching frequent queries

---

## Advanced Configuration

### LLM Parameters

Adjust in `.env`:
```
LLM_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for speed
LLM_TEMPERATURE=0.1  # Lower = more deterministic
LLM_MAX_TOKENS=2000  # Increase for longer responses
```

### RAG Settings

```
CHUNK_SIZE=1000  # Characters per chunk
CHUNK_OVERLAP=200  # Overlap between chunks
RETRIEVAL_TOP_K=3  # Number of chunks to retrieve
```

### Agent Behavior

```
MAX_TOOL_CALLS=10  # Maximum tools per query
ENABLE_RAG=true  # Enable/disable RAG system
```

---

## Development

### Adding New Tools

1. Create tool function in appropriate module
2. Add to `agent.py` tool list:
```python
Tool(
    name="my_new_tool",
    func=lambda x: json.dumps(my_tool_function(x)),
    description="Clear description for LLM"
)
```

### Adding Knowledge Documents

1. Place documents in `agent/knowledge_base/`
2. Run ingestion pipeline
3. Documents auto-loaded on next restart

### Extending the Agent

The architecture supports:
- Additional database tools
- New ML model integrations
- Custom RAG document processors
- Alternative LLM providers

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor API logs for errors
- Check agent response quality

**Weekly:**
- Review new price anomalies
- Update supplier scores (Module 4)

**Monthly:**
- Re-ingest updated policy documents
- Review and update knowledge base
- Check forecast accuracy

**Quarterly:**
- Evaluate LLM model performance
- Consider alternative models
- Update system prompts based on feedback

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs in `logs/` directory
- Consult Module 5 implementation report
- Contact development team

---

## License

Internal company use only. Do not distribute.
