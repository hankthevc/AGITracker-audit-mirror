# Custom Preset Builder Guide

## Overview

The Custom Preset Builder allows you to create your own category weight configurations and see how they affect the overall AGI proximity index in real-time.

## Accessing the Builder

Navigate to `/presets/custom` or click the "Custom Presets" link in the main navigation.

## How to Use

### 1. Adjust Category Weights

Use the sliders or input fields to adjust the weight for each of the four categories:

- **Capabilities**: Progress on core AI benchmarks (SWE-bench, GPQA, etc.)
- **Agents**: Real-world deployment and reliability metrics  
- **Inputs**: Training compute, algorithmic efficiency, and infrastructure
- **Security**: Safety measures, governance, and risk mitigation

**Important**: Weights must sum to exactly 1.0 (100%). The interface will show a validation message.

### 2. Real-Time Calculation

As you adjust the sliders, the custom index recalculates automatically:

- **Overall AGI Proximity**: Weighted average based on your custom weights
- **Individual Categories**: Current progress for each category (read-only)
- **Safety Margin**: Difference between security and capabilities progress

If data is insufficient (e.g., zero progress in required categories), the overall index will show "N/A".

### 3. Comparison View

The right panel shows how your custom preset compares to standard presets:

- **Equal**: 25% weight for each category
- **Aschenbrenner**: Inputs 40%, Agents 30%, Capabilities 20%, Security 10%
- **AI-2027**: Agents 35%, Capabilities 30%, Inputs 25%, Security 10%

Color-coded badges show the difference:
- 🟢 Green: Your custom index is higher
- 🔴 Red: Your custom index is lower
- ⚪ Gray: Same value

### 4. Quick Preset Loading

Click the preset buttons to instantly load weights from standard configurations:
- "Reset to Equal" → 25/25/25/25
- "Load Aschenbrenner" → 40/30/20/10
- "Load AI-2027" → 35/35/25/10

You can then modify these as a starting point.

### 5. Save & Share

#### Download JSON
Click "Download JSON" to export your preset configuration. The file includes:
```json
{
  "name": "My Custom Preset",
  "weights": {
    "capabilities": 0.3,
    "agents": 0.3,
    "inputs": 0.2,
    "security": 0.2
  },
  "calculated": { ... },
  "created_at": "2025-10-29T12:00:00.000Z"
}
```

#### Copy Share URL
Click "Copy Share URL" to get a shareable link that preserves your weights:
```
https://agi-tracker.vercel.app/presets/custom?capabilities=0.3&agents=0.3&inputs=0.2&security=0.2&name=My+Custom+Preset
```

Anyone with this URL can see your exact configuration.

## Use Cases

### Research Scenarios

**Capability-Focused**:
```
Capabilities: 50%
Agents: 20%
Inputs: 20%
Security: 10%
```
Emphasizes benchmark performance. Useful for tracking technical progress independent of deployment.

**Safety-First**:
```
Capabilities: 20%
Agents: 20%
Inputs: 10%
Security: 50%
```
Prioritizes security measures. Useful for risk analysis and governance planning.

**Deployment-Ready**:
```
Capabilities: 25%
Agents: 45%
Inputs: 15%
Security: 15%
```
Emphasizes real-world agent reliability. Useful for tracking practical AI systems.

### Educational Use

Teachers and students can use custom presets to explore:
- How different weighting schemes change AGI proximity estimates
- The tension between capability progress and security readiness
- Why harmonic mean (for overall index) prevents cherry-picking

## API Integration

You can also calculate custom indexes programmatically:

```bash
# GET request with custom weights
curl "https://api.agi-tracker.com/v1/index/custom?capabilities=0.3&agents=0.3&inputs=0.2&security=0.2"
```

Response:
```json
{
  "as_of_date": "2025-10-29",
  "overall": 0.42,
  "capabilities": 0.55,
  "agents": 0.42,
  "inputs": 0.38,
  "security": 0.25,
  "safety_margin": -0.30,
  "weights": {
    "capabilities": 0.3,
    "agents": 0.3,
    "inputs": 0.2,
    "security": 0.2
  }
}
```

## Limitations

- Weights must be between 0.0 and 1.0
- Total must equal 1.0 (±0.01 tolerance)
- Cannot save presets to server (local storage/URL only)
- Real-time calculation uses latest snapshot data only

## Tips

1. **Start with a standard preset** and make incremental changes
2. **Compare multiple presets** side-by-side by opening tabs
3. **Document your rationale** when sharing custom presets
4. **Check the comparison view** to understand how your weights differ from established frameworks

## Troubleshooting

**"Weights must sum to 1.0" error**:
- Adjust weights until the validation message turns green
- Use the reset button to start over with valid weights

**"N/A" overall index**:
- This means insufficient data in required categories (Inputs or Security)
- Category values still visible individually

**No real-time updates**:
- Check that the API server is running
- Visit `/_debug` to verify API connectivity
- Ensure JavaScript is enabled

## Related Documentation

- [Methodology](/methodology) - How index is calculated
- [Signpost Deep-Dives](/signposts/swe-bench) - Individual metric details
- [Historical Charts](/docs/guides/historical-charts.md) - Track changes over time

