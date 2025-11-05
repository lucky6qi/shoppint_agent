# LLM Usage in Codebase

This document highlights where and how LLM (Large Language Model) is used in the codebase.

## Overview

The project uses **Anthropic's Claude API** (specifically `claude-3-5-sonnet-20241022`) to intelligently categorize discount products into shopping buckets based on user requirements.

## LLM Usage Locations

### 1. Primary LLM Integration: `bucket_generator.py`

**File**: `bucket_generator.py`

**Class**: `BucketGenerator`

#### LLM Initialization
```python
# Line 11: Initialize Anthropic client
self.client = anthropic.Anthropic(api_key=api_key)
```

#### LLM API Call
```python
# Lines 67-74: Make LLM API call
message = self.client.messages.create(
    model="claude-3-5-sonnet-20241022",  # ← LLM Model
    max_tokens=4000,
    messages=[{
        "role": "user",
        "content": prompt  # ← LLM Prompt
    }]
)
```

#### LLM Purpose
The LLM is used to:
- **Analyze** discount products from AH.nl
- **Understand** user shopping requirements
- **Categorize** products into intelligent buckets (essentials, meat, vegetables, fruit, snacks, beverages, other)
- **Provide reasoning** for product selection

#### LLM Prompt Structure
```python
# Lines 12-23: Base prompt for LLM
self.base_prompt = """You are an intelligent shopping assistant...
..."""
```

The prompt includes:
- Instructions for bucket classification
- Available discount products list
- User shopping requirements
- Recent shopping history (optional)
- Output format specification (JSON)

### 2. LLM Configuration: `config.py`

**File**: `config.py`

```python
# Line 10: LLM API key configuration
anthropic_api_key: Optional[str] = None
```

### 3. LLM Usage in Main Program: `main.py`

**File**: `main.py`

```python
# Lines 17-20: Check for LLM API key
if not config.anthropic_api_key:
    config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not config.anthropic_api_key:
        print("⚠️ Warning: ANTHROPIC_API_KEY not set...")

# Lines 57-70: Use LLM to generate buckets
if config.anthropic_api_key:
    generator = BucketGenerator(config.anthropic_api_key)  # ← LLM initialization
    buckets = generator.generate_buckets(...)  # ← LLM call
```

### 4. LLM Usage in Examples

**Files**: `example_usage.py`, `cart_examples.py`

```python
# Example: example_usage.py, lines 47-55
api_key = os.getenv("ANTHROPIC_API_KEY")
generator = BucketGenerator(api_key)  # ← LLM initialization
buckets = generator.generate_buckets(...)  # ← LLM call
```

## LLM Flow Diagram

```
User Requirements
       ↓
BucketGenerator.generate_buckets()
       ↓
Build Prompt (products + history + requirements)
       ↓
anthropic.Anthropic().messages.create()  ← LLM API CALL
       ↓
Parse JSON Response
       ↓
Return Categorized Buckets
```

## LLM Model Details

- **Provider**: Anthropic
- **Model**: `claude-3-5-sonnet-20241022`
- **Max Tokens**: 4000
- **Purpose**: Product categorization and intelligent shopping list generation

## Fallback Behavior

If LLM call fails or API key is not set:
- Falls back to keyword-based classification (`_create_default_buckets()`)
- Uses simple keyword matching for product categorization

## Dependencies

- `anthropic` package (required for LLM functionality)
- `ANTHROPIC_API_KEY` environment variable (required)

## Code Locations Summary

| File | Lines | Description |
|------|-------|-------------|
| `bucket_generator.py` | 11 | Initialize Anthropic client |
| `bucket_generator.py` | 67-74 | LLM API call |
| `bucket_generator.py` | 12-23 | LLM prompt definition |
| `config.py` | 10 | API key configuration |
| `main.py` | 17-20, 57-70 | Check and use LLM |
| `example_usage.py` | 47-55 | Example LLM usage |
| `cart_examples.py` | 59-67 | Example LLM usage |

