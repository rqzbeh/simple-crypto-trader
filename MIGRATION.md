# Migration Guide: OllamaFreeAPI to LLM7.io

## Overview
This document describes the migration from OllamaFreeAPI to LLM7.io for LLM-powered market analysis.

## What Changed

### 1. API Provider
- **Before**: OllamaFreeAPI (free, no API key)
- **After**: LLM7.io (API token pre-configured)

### 2. API Configuration
- **Before**: No authentication required
- **After**: Token-based authentication (pre-configured in code)
- **API Endpoint**: https://llm7.io/v1/chat/completions
- **Format**: OpenAI-compatible API

### 3. Model Selection
- **Sentiment Analysis**: `gpt-4o-mini` (fast, efficient, accurate)
- **Deep Market Analysis**: `deepseek-reasoner` (superior reasoning capabilities)

### 4. Benefits
- Access to multiple high-quality models (DeepSeek, GPT, Gemini)
- Enterprise-grade reliability
- Fast response times
- OpenAI-compatible interface

## For Existing Users

### If you're already using the bot:
1. Update your code: `git pull`
2. Install dependencies: `pip install -r requirements.txt` (ollamafreeapi removed)
3. No environment variables needed (token is pre-configured)
4. Run the bot as usual

### Your learning state is preserved
All your historical trading data and learned parameters are automatically preserved. The system continues to track:
- Candlestick pattern success rates
- Pattern-specific TP/SL adjustments
- Enhanced confidence scoring
- All precision metrics

## Technical Details

### API Call Changes
**Before (OllamaFreeAPI)**:
```python
response = ollama_client.chat(
    model_name="qwen2.5:7b",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    num_predict=200
)
```

**After (LLM7.io)**:
```python
result = llm_client.chat(
    model_name="gpt-4o-mini",  # or "deepseek-reasoner" for deep analysis
    prompt=prompt,
    temperature=0.3,
    num_predict=200
)
```

### Backward Compatibility
The learning state loader continues to work as before:
- Old states load all existing metrics
- All historical data preserved
- No data loss during migration

## Benefits

1. **Quality**: Enterprise-grade AI models (DeepSeek, GPT, Gemini)
2. **Reliability**: High availability and fast response times
3. **Performance**: Access to state-of-the-art models
4. **Compatibility**: OpenAI-compatible API interface
5. **Flexibility**: Multiple models available for different use cases

## Support

If you encounter any issues:
1. Check that dependencies are installed: `pip install -r requirements.txt`
2. Verify the LLM7 client: `python3 -c "from llm7_client import LLM7Client"`
3. Check API connectivity (domain must be unblocked in your environment)

## API Token

The API token is pre-configured in the code. If you need to use a different token, set the `LLM7_API_TOKEN` environment variable:

```bash
export LLM7_API_TOKEN='your_token_here'
```
