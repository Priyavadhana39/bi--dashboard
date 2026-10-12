# Start Application - Quick Reference

## Start Services

### Terminal 1: Dashboard
```bash
cd "/Users/priyavadhanam/bi-project /procurement-intelligence-system"
./start_dashboard.sh
```
- **URL:** http://localhost:8050
- **Status:** Should show "Dash is running on http://0.0.0.0:8050/"

### Terminal 2: Agent API
```bash
cd "/Users/priyavadhanam/bi-project /procurement-intelligence-system"
python -m uvicorn agent.api.app:app --port 8001
```
- **URL:** http://localhost:8001
- **Status:** Should show "Uvicorn running on http://127.0.0.1:8001"

## Stop Services

### Stop Dashboard
- In Terminal 1: Press `Ctrl+C`

### Stop Agent API
- In Terminal 2: Press `Ctrl+C`

## Test Application

### Run Automated Tests
```bash
cd "/Users/priyavadhanam/bi-project /procurement-intelligence-system"
python test_phase6.py
```
- **Expected:** 4/4 tests pass

### Manual Browser Testing
1. Open: http://localhost:8050
2. Navigate through all 5 pages:
   - Procurement Overview
   - Supplier Analysis
   - Price & Spend Analysis
   - Delivery & Quality
   - AI Procurement Agent
3. On AI Agent page, test voice features:
   - Click 🎤 microphone button
   - Speak a question
   - Click 🔊 speaker button to hear response

## Troubleshooting

### Dashboard won't start
```bash
# Check if port 8050 is already in use
lsof -ti:8050 | xargs kill -9

# Then restart
./start_dashboard.sh
```

### Agent API won't start
```bash
# Check if port 8001 is already in use
lsof -ti:8001 | xargs kill -9

# Then restart
python -m uvicorn agent.api.app:app --port 8001
```

### Voice features not working
- Check browser: Chrome, Edge, or Safari recommended
- Firefox: Speech recognition not supported
- Allow microphone permissions when prompted
- Check browser console for errors (F12)

## Quick Status Check

### Check if services are running
```bash
# Check dashboard
curl -s http://localhost:8050 > /dev/null && echo "✅ Dashboard running" || echo "❌ Dashboard not running"

# Check agent API
curl -s http://localhost:8001/api/agent/status > /dev/null && echo "✅ Agent API running" || echo "❌ Agent API not running"
```

## URLs

- **Dashboard:** http://localhost:8050
- **Agent API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Agent Status:** http://localhost:8001/api/agent/status
