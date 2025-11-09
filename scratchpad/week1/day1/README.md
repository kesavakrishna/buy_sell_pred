# Day 1 - Quick Implementation

This folder contains the quick-and-dirty Day 1 implementation for learning purposes.

## Files
- `day1_fear_greed.py` - Simple script to fetch Fear & Greed Index
- `requirements.txt` - Minimal dependencies needed for Day 1

## Purpose
This is a proof-of-concept to:
- Learn how the Fear & Greed API works
- Understand the data format
- Test basic functionality

## Running
```bash
# From project root
venv/Scripts/python scratchpad/day1/day1_fear_greed.py
```

## Next Steps
The production version of this code should be refactored into:
- `src/data/fear_greed_fetcher.py` - Class-based fetcher
- `src/utils/csv_storage.py` - Reusable CSV handler
- `config/api_config.py` - API configuration