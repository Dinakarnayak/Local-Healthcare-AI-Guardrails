"""Learning prototype: a local healthcare information assistant.

This is not a medical device. It must not diagnose, prescribe, or replace
advice from a qualified healthcare professional.
"""

import re

import ollama


MODEL = "qwen2.5:3b"

# This prompt sets the model's intended role. It is useful guidance, but it is
# not a security boundary: the input and output checks below are separate
# guardrails because a model can ignore or misapply a prompt.
SYSTEM_PROMPT = """
You provide general, non-personalized health information only.
Do not diagnose a person, recommend a medication or dose, or claim certainty.
Do not replace a clinician, pharmacist, or emergency service.
For urgent or worsening symptoms, tell the user to seek immediate professional
help. For other health concerns, encourage the user to contact a qualified
healthcare professional. Be clear when information is general or uncertain.
""".strip()


# Deliberately simple phrase lists make this rule easy to explain and change.
# They will miss unfamiliar wording and can match harmless contexts.
URGENT_PATTERNS = (
    r"\bsevere chest pain\b",
    r"\bchest pain\b",
    r"\b(can't|cannot|unable to) breathe\b",
    r"\btrouble breathing\b",
    r"\bdifficulty breathing\b",
    r"\b(shortness of breath|breathlessness)\b",
    r"\b(signs? of a stroke|face drooping|slurred speech)\b",
    r"\b(unconscious|not responding)\b",
    r"\bsevere bleeding\b",
    r"\b(anaphylaxis|severe allergic reaction)\b",
    r"\b(overdose|taken too many (pills|tablets))\b",
    r"\b(suicidal|kill myself|end my life)\b",
)

DIAGNOSIS_PATTERNS = (
    r"\b(diagnose|diagnosis)\b",
    r"\bwhat (illness|disease|condition) do i have\b",
    r"\bwhich (illness|disease|condition) (do )?i have\b",
    r"\bwhat's wrong with me\b",
    r"\btell me exactly what i have\b",
)

MEDICATION_PATTERNS = (
    r"\b(how much|how many|what dose|dosage)\b.{0,50}\b(take|tablet|pill|medicine|medication|mg)\b",
    r"\b(can|should) i take\b.{0,50}\b(medicine|medication|tablet|pill|mg)\b",
    r"\b(recommend|prescribe)\b.{0,40}\b(medicine|medication|drug|dose)\b",
)

# These look for risky claims in model output. They are intentionally
# conservative examples, not a complete medical safety classifier.
UNSAFE_OUTPUT_PATTERNS = (
    r"\byou (definitely |probably )?have\b",
    r"\byou are diagnosed with\b",
    r"\byour diagnosis is\b",
    r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|tablets?|pills?)\b",
    r"\btake \d+(\.\d+)?\s*(mg|mcg|g|ml|tablets?|pills?)\b",
    r"\byou should take\b",
    r"\bthe correct dose for you is\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    """Match a rule list without regard to capitalization."""
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def check_input(user_text: str) -> tuple[bool, str]:
    """Return (allowed, reason) before sending anything to the model."""
    if _matches_any(user_text, URGENT_PATTERNS):
        return False, "urgent"
    if _matches_any(user_text, DIAGNOSIS_PATTERNS):
        return False, "diagnosis"
    if _matches_any(user_text, MEDICATION_PATTERNS):
        return False, "medication"
    return True, "allowed"


def check_output(response_text: str) -> tuple[bool, str]:
    """Reject generated text that matches a small set of unsafe patterns."""
    if _matches_any(response_text, UNSAFE_OUTPUT_PATTERNS):
        return False, "possible diagnosis or personalized medication advice"
    return True, "no configured unsafe pattern found"


def ask_local_model(user_text: str) -> str:
    """Send the prompt to the Ollama service on this computer."""
    result = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    return result["message"]["content"]


def refusal_message(reason: str) -> str:
    """Give a fixed response for requests we do not send to the model."""
    if reason == "urgent":
        return (
            "This may need urgent attention. Contact emergency services now "
            "(999 in the UK, or your local emergency number). Do not wait for "
            "an AI response."
        )
    if reason == "diagnosis":
        return (
            "I can't diagnose symptoms. A qualified healthcare professional "
            "can assess your situation."
        )
    if reason == "medication":
        return (
            "I can't recommend a personal medication or dose. Check the "
            "medicine's packaging and ask a pharmacist or clinician."
        )
    return "I can't safely answer that request. Please ask a qualified professional."


def main() -> None:
    print("Local Healthcare Information Assistant (learning prototype)")
    print("General information only; not for diagnosis, treatment, or emergencies.")
    print("Type 'quit' to exit. Do not enter real personal medical information.")

    while True:
        user_text = input("\nYou: ").strip()
        if user_text.lower() in {"quit", "exit"}:
            break
        if not user_text:
            print("Please enter a question.")
            continue

        allowed, reason = check_input(user_text)
        if not allowed:
            print(f"Assistant: {refusal_message(reason)}")
            continue

        try:
            answer = ask_local_model(user_text)
        except Exception as exc:
            print(
                "Could not contact local Ollama. Check that Ollama is running "
                f"and that {MODEL} is installed. Details: {exc}"
            )
            continue

        safe_to_show, reason = check_output(answer)
        if not safe_to_show:
            print(
                "Assistant: I can't safely display that generated response. "
                "Please ask a qualified healthcare professional."
            )
            # Only the validation reason is reported; the rejected model text
            # is not printed to the user.
            print(f"[Output guardrail: blocked because of {reason}.]")
            continue

        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()

