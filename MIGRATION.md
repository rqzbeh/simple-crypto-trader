# Migration Guide: Groq to OllamaFreeAPI

## Overview
This document describes the migration from Groq to OllamaFreeAPI for LLM-powered market analysis.

## What Changed

### 1. API Provider
- **Before**: Groq (required API key, rate limits)
- **After**: OllamaFreeAPI (no API key, free forever)

### 2. Rate Limits
- **Before**: Groq free tier had varying limits
- **After**: OllamaFreeAPI free tier:
  - 100 requests/hour
  - 16k tokens per request
  - 50 tokens/second processing speed
  - Access to 7B models

### 3. Model Selection
- **Sentiment Analysis**: `llama3.1:8b` (fast, 8 billion parameters)
- **Deep Market Analysis**: `llama3.3:70b` (powerful, 70 billion parameters)

### 4. No Breaking Changes
All existing functionality is preserved. The bot will work exactly as before, but:
- No API key needed
- Free forever
- Better model availability

## For Existing Users

### If you're already using the bot:
1. Update your code: `git pull`
2. Install new dependency: `pip install -r requirements.txt`
3. Remove GROQ_API_KEY from your environment (no longer needed)
4. Run the bot as usual

### Your learning state is preserved
All your historical trading data and learned parameters are automatically migrated. The new system adds:
- Candlestick pattern success tracking
- Pattern-specific TP/SL adjustments
- Enhanced confidence scoring

## Technical Details

### API Call Changes
**Before (Groq)**:
```python
response = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    max_tokens=200
)
result = response.choices[0].message.content
```

**After (OllamaFreeAPI)**:
```python
result = llm_client.chat(
    model_name="llama3.1:8b",
    prompt=prompt,
    temperature=0.3,
    num_predict=200
)
```

### Backward Compatibility
The learning state loader now handles both old and new metric formats:
- Old states load all existing metrics
- New metrics (candlestick patterns) are added with default values
- No data loss during migration

## Benefits

1. **Cost**: Completely free, no API key required
2. **Reliability**: No API key expiration or rate limit surprises
3. **Performance**: Access to powerful 70B parameter models
4. **Simplicity**: One less API key to manage
5. **Enhanced Learning**: Better tracking for candlestick-based trading

## Support

If you encounter any issues:
1. Check that `ollamafreeapi` is installed: `pip install ollamafreeapi`
2. Verify import works: `python3 -c "from ollamafreeapi import OllamaFreeAPI"`
3. Check available models: See [OllamaFreeAPI docs](https://github.com/mfoud444/ollamafreeapi/)
