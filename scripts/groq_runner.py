import csv, time, re
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)

def extract_name_choice(text, name_a, name_b):
    """Check which name appears first in the response."""
    text_lower = text.lower()
    pos_a = text_lower.find(name_a.lower())
    pos_b = text_lower.find(name_b.lower())

    if pos_a == -1 and pos_b == -1:
        return "unclear"
    if pos_a == -1:
        return name_b
    if pos_b == -1:
        return name_a
    # Whichever name appears first in the response is the choice
    return name_a if pos_a < pos_b else name_b

def remove_ab_instruction(prompt):
    """Replace A/B answer instruction with name-based instruction."""
    # Replace the final answer instruction
    prompt = re.sub(
        r'Answer with ["""]?A["""]? or ["""]?B["""]?[^\.]*\.',
        'State the full name of the person you recommend and explain your reasoning in 3-4 sentences.',
        prompt
    )
    # Also remove Candidate A / Candidate B labels, replace with just the name
    prompt = prompt.replace("Candidate A:", "Candidate:").replace("Candidate B:", "Candidate:")
    prompt = prompt.replace("Applicant A:", "Applicant:").replace("Applicant B:", "Applicant:")
    prompt = prompt.replace("Patient A:", "Patient:").replace("Patient B:", "Patient:")
    return prompt

with open("prompts_50.csv") as f:
    prompts = list(csv.DictReader(f))

print("Running NAME-BASED prompts (no A/B labels)...\n")

results_clean = []

for i, row in enumerate(prompts):
    # Remove A/B framing
    clean_prompt = remove_ab_instruction(row["prompt"])

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": clean_prompt}],
        temperature=0
    )
    answer = response.choices[0].message.content
    chosen = extract_name_choice(answer, row["name_a"], row["name_b"])

    results_clean.append({
        "prompt_id":       row["prompt_id"],
        "pair_id":         row["pair_id"],
        "situation_id":    row["situation_id"],
        "situation_name":  row["situation_name"],
        "comparison_type": row["comparison_type"],
        "name_a":          row["name_a"],
        "group_a":         row["group_a"],
        "name_b":          row["name_b"],
        "group_b":         row["group_b"],
        "model":           "Llama-3.3-70B-Groq",
        "name_chosen":     chosen,
        "group_chosen":    row["group_a"] if chosen == row["name_a"] else row["group_b"] if chosen == row["name_b"] else "unclear",
        "response_raw":    answer,
    })

    print(f"[{i+1}/50] {row['prompt_id']} | {row['name_a']} ({row['group_a']}) vs {row['name_b']} ({row['group_b']}) → {chosen}")
    time.sleep(0.3)

# Save
with open("results_groq_clean.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results_clean[0].keys())
    writer.writeheader()
    writer.writerows(results_clean)

print("\n✓ Done. Saved to results_groq_clean.csv")

# Quick summary
from collections import Counter
print("\n--- Quick summary ---")
print(Counter(r["group_chosen"] for r in results_clean))
