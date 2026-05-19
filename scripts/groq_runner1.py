import csv
import time
import re
import os
from groq import Groq
from collections import Counter

# =====================================================================
# Configuration
# =====================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
client = Groq(api_key=GROQ_API_KEY)

# Use Llama 3 on Groq
MODEL_NAME = 'llama-3.3-70b-versatile'

INPUT_FILE = "prompts_shuffled_50.csv"
OUTPUT_FILE = "results_groq_clean.csv"

# =====================================================================
# Helper Functions
# =====================================================================
def extract_name_choice(text, names):
    if not text: return "unclear"
    text_lower = text.lower()
    positions = []
    for n in names:
        pos = text_lower.find(n.lower())
        if pos != -1: positions.append((pos, n))
    if not positions: return "unclear"
    positions.sort(key=lambda x: x[0])
    return positions[0][1]

def remove_abcd_instruction(prompt):
    prompt = re.sub(
        r'Answer.*?A,\s*B,\s*C,\s*or\s*D\.[^\.]*\.',
        'State the full name of the person you recommend and explain your reasoning in 3-4 sentences.',
        prompt, flags=re.IGNORECASE
    )
    for letter in ["A", "B", "C", "D"]:
        prompt = prompt.replace(f"Candidate {letter}:", "Candidate:")
        prompt = prompt.replace(f"Applicant {letter}:", "Applicant:")
        prompt = prompt.replace(f"Patient {letter}:", "Patient:")
        prompt = prompt.replace(f"Tenant {letter}:", "Tenant:")
    return prompt

# =====================================================================
# Main Execution
# =====================================================================
def main():
    try:
        with open(INPUT_FILE, encoding="utf-8") as f:
            prompts = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}.")
        return

    print(f"Running NAME-BASED prompts using {MODEL_NAME} on {INPUT_FILE}...\n")
    results_clean = []

    for i, row in enumerate(prompts):
        clean_prompt = remove_abcd_instruction(row["prompt"])
        names = [row["name_A"], row["name_B"], row["name_C"], row["name_D"]]

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0.0, # Deterministic reasoning
                messages=[{"role": "user", "content": clean_prompt}]
            )
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"Error on prompt {row.get('prompt_id', i)}: {e}")
            answer = f"ERROR: {e}"

        chosen = extract_name_choice(answer, names)

        results_clean.append({
            "prompt_id":       row.get("prompt_id", ""),
            "pair_id":         row.get("pair_id", ""),
            "situation_id":    row.get("situation_id", ""),
            "situation_name":  row.get("situation_name", ""),
            "domain":          row.get("domain", ""),
            "name_A":          row.get("name_A", ""),
            "name_B":          row.get("name_B", ""),
            "name_C":          row.get("name_C", ""),
            "name_D":          row.get("name_D", ""),
            "model":           f"Groq-{MODEL_NAME}",
            "name_chosen":     chosen,
            "response_raw":    answer,
        })

        print(f"[{i+1}/{len(prompts)}] {row.get('prompt_id')} | → Chosen: {chosen}")
        # Groq is fast, but keep a small sleep to avoid free-tier RPM limits
        time.sleep(1.0) 

    if results_clean:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results_clean[0].keys())
            writer.writeheader()
            writer.writerows(results_clean)
        print(f"\n✓ Done. Saved to {OUTPUT_FILE}")
        print("\n--- Quick summary ---")
        for name, count in Counter(r["name_chosen"] for r in results_clean).items():
            print(f"{name}: {count}")

if __name__ == "__main__":
    main()