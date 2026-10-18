# Local Healthcare AI Guardrails — Learning Project

This folder contains a learning implementation of the starter scaffold for the
CO7262 practical. Read `app.py` line by line, adjust the rules to reflect your
own design choices, and run the manual checks yourself. You need to understand
and be able to explain every part you demonstrate.

The prototype gives general health information. It is not a medical device and
must not diagnose, prescribe, or replace a qualified professional.

## Guardrails in `app.py`

1. **Input check before inference.** Phrase rules escalate selected emergency
   symptoms and refuse diagnosis or personalized medication requests before
   they reach the model. This reduces some predictable risks and provides a
   fixed response for those cases. It can miss unfamiliar wording and can
   wrongly match harmless questions.
2. **Output check before display.** A second phrase check blocks some direct
   diagnostic claims and medication dose instructions. If a pattern matches,
   the generated text is discarded. This does not prove that other text is
   safe; wording changes, indirect claims, and false positives remain possible.
3. **System prompt.** The prompt gives the model role boundaries, but prompts
   can be ignored. The code checks are separate layers, and they are also
   limited keyword rules rather than a complete safety system.

## Local model setup

Install Ollama, then download the model once:

```powershell
ollama pull qwen2.5:3b
```

Confirm it starts locally:

```powershell
ollama run qwen2.5:3b
```

In this project folder, create and activate a virtual environment, then install
the Python dependency:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the command line app:

```powershell
python app.py
```

Ollama serves inference locally after the model has been downloaded. Do not
enter real personal medical information. Keep a record in `TEST_PLAN.md` of
what you actually observe on your own machine; expected behaviour is not the
same as a test result.

## How to read the implementation

- `check_input` runs before `ask_local_model`, so refused requests are not sent
  to Ollama.
- `ask_local_model` sends a system message and the user's question to the
  configured local model.
- `check_output` examines the generated text before the program displays it.
- `refusal_message` provides fixed responses for the input categories.
- `main` connects those steps into the command line loop.

Try changing one rule at a time, then use `TEST_PLAN.md` to check normal,
diagnosis, medication, urgent-symptom, and deliberately unsafe-output examples.
Record actual results and note false positives or misses.

