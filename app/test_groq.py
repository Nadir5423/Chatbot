import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Make printing Urdu safe on Windows
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CANDIDATES = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
]

CONTEXT = "ادارے کا سالانہ بجٹ پچاس لاکھ روپے ہے اور اس میں سے تیس فیصد تعلیمی سرگرمیوں پر خرچ ہوتا ہے۔"
QUESTION = "Idare ka salana budget kitna hai aur taleemi activities par kitna kharch hota hai?"

ANSWER_SYSTEM = (
    "You answer questions using ONLY the provided context. "
    "The user writes in Roman Urdu (Urdu in Latin letters). "
    "Always reply in Roman Urdu using Latin letters only, never Urdu script, "
    "even if the context is in Urdu script or English. "
    "Answer the question directly in your own words; do not copy the context. "
    "If the answer is not in the context, say so."
)
REWRITE_SYSTEM = (
    "Rewrite the user's question (Roman Urdu) into 3 lines: 1) English, "
    "2) Urdu script, 3) the original. Output only those 3 lines."
)


def ask(model, system, user):
    r = client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return r.choices[0].message.content


from pathlib import Path
OUT = Path(__file__).parent / "groq_test_output.txt"

with open(OUT, "w", encoding="utf-8") as f:
    for m in CANDIDATES:
        f.write("=" * 70 + f"\nMODEL: {m}\n")
        try:
            a = ask(m, ANSWER_SYSTEM, f"Context:\n{CONTEXT}\n\nQuestion: {QUESTION}")
            f.write(f"--- ANSWER:\n{a}\n")
            r = ask(m, REWRITE_SYSTEM, QUESTION)
            f.write(f"--- REWRITE:\n{r}\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")
        f.flush()
print("Done. Open", OUT)