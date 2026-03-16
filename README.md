---
title: Researcher Multi-Agent
emoji: 🔬
colorFrom: indigo
colorTo: blue
sdk: gradio
app_file: app.py
python_version: "3.10"
---

# Researcher Multi-Agent

A Hugging Face Space + local Gradio app that runs the existing manager-led multi-agent research orchestration pipeline from the browser.

## What this app does

- Accepts a high-level research/planning goal.
- Optionally accepts constraints (newline or comma-separated).
- Runs the current orchestration engine (`ChiefOfStaff` + specialist delegates + `SkepticalReviewer`).
- Shows:
  - final summary
  - timeline / major execution events
  - skeptical reviewer output
  - raw structured JSON output

## Run locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set required environment variable:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

3. Start the app:

```bash
python app.py
```

Then open the printed local Gradio URL in your browser.

## Deploy to Hugging Face Spaces

1. Create a new Space and choose **Gradio** as the SDK.
2. Push this repository contents to the Space repo.
3. (Recommended) In Space **Settings → Variables and secrets**, add:
   - Secret name: `OPENAI_API_KEY`
   - Secret value: your OpenAI API key
4. Rebuild/restart the Space.

## API key configuration

You can now provide the API key in either place:

- **Space Secret / environment variable**: `OPENAI_API_KEY`
- **Runtime UI field**: `OPENAI_API_KEY (runtime, optional)` in the app interface

If both are provided, the runtime field value is used for that app process. If neither is provided, the UI fails gracefully with a clear error message instead of crashing.
