#!/bin/bash
echo "🧪 Testing FIXED API..."
echo ""
echo "Events count:"
curl -s "https://agitracker-production-6efa.up.railway.app/v1/events" | jq ".total"
echo ""
echo "Sample event titles:"
curl -s "https://agitracker-production-6efa.up.railway.app/v1/events?limit=3" | jq ".items[].title"
echo ""
echo "Index values:"
curl -s "https://agitracker-production-6efa.up.railway.app/v1/index" | jq "{overall, capabilities, agents}"
echo ""
echo "✅ If total > 0, Sprint 7 is COMPLETE!"

