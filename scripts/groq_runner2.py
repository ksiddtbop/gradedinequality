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
MODEL_NAME = 'llama-3.3-70b-versatile'

INPUT_FILE = "prompts_shuffled_50.csv"
OUTPUT_FILE = "results_groq_clean.csv"

# =====================================================================
# Helper Functions
# =====================================================================
def extract_name_choice(text, names):
    """Force extraction using the explicit tag we injected into the prompt."""
    text_lower = text.lower()
    
    # 1. Look specifically for the RECOMMENDED tag first
    match = re.search(r'recommended:\s*\**\s*([a-z\s\.]+)', text_lower)
    if match:
        extracted = match.group(1).strip()
        for n in names:
            if n.lower() in extracted:
                return n
    
    # 2. Fallback: If tag fails, look for the name that appears most frequently
    # (Models often mention their chosen name repeatedly in the reasoning)
    counts = {n: text_lower.count(n.lower()) for n in names}
    best_name = max(counts, key=counts.get)
    return best_name if counts[best_name] > 0 else "unclear"

def format_prompt(row):
    """Injects a strict constraint to prevent positional bias."""
    prompt = row["prompt"]
    # Force the model to use the tag for extraction
    constraint = "\n\nCRITICAL: You must choose exactly one candidate. Start your response with exactly: '**RECOMMENDED:** [Full Name]'. Then explain your reasoning."
    
    # Remove old A/B/C/D instructions to prevent confusion
    prompt = re.sub(r'Answer on the first line.*?\.', '', prompt, flags=re.IGNORECASE)
    
    return prompt + constraint

# =====================================================================
# Main Execution
# =====================================================================
def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        prompts = list(csv.DictReader(f))

    results_clean = []
    for i, row in enumerate(prompts):
        clean_prompt = format_prompt(row)
        names = [row["name_A"], row["name_B"], row["name_C"], row["name_D"]]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.0,
            messages=[{"role": "user", "content": clean_prompt}]
        )
        answer = response.choices[0].message.content
        chosen = extract_name_choice(answer, names)

        results_clean.append({
            **row,
            "model": MODEL_NAME,
            "name_chosen": chosen,
            "response_raw": answer
        })

        print(f"[{i+1}/{len(prompts)}] {row['prompt_id']} → {chosen}")
        time.sleep(1.0) 

    # Save logic
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results_clean[0].keys())
        writer.writeheader()
        writer.writerows(results_clean)
    print("Done.")

if __name__ == "__main__":
    main()