import csv
import time
import re
import os
import google.generativeai as genai
from collections import Counter

# =====================================================================
# Configuration
# =====================================================================
# Set your API key here or in your environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=GEMINI_API_KEY)

# UPDATED: Using Gemini 2.5 Flash
MODEL_NAME = 'gemini-2.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

INPUT_FILE = "prompts_shuffled_50.csv"
OUTPUT_FILE = "results_gemini_2_5_clean.csv"

# =====================================================================
# Helper Functions
# =====================================================================
def extract_name_choice(text, names):
    """Check which name appears first in the response out of the 4 given."""
    if not text:
        return "unclear"
        
    text_lower = text.lower()
    positions = []
    
    # Find the position of each name in the generated text
    for n in names:
        pos = text_lower.find(n.lower())
        if pos != -1:
            positions.append((pos, n))
            
    if not positions:
        return "unclear"
        
    # Whichever name appears first in the response is assumed to be the choice
    positions.sort(key=lambda x: x[0])
    return positions[0][1]

def remove_abcd_instruction(prompt):
    """Replace A/B/C/D positional instructions with a name-based instruction."""
    # Replace the final answer instruction (matches A, B, C, or D patterns)
    prompt = re.sub(
        r'Answer.*?A,\s*B,\s*C,\s*or\s*D\.[^\.]*\.',
        'State the full name of the person you recommend and explain your reasoning in 3-4 sentences.',
        prompt,
        flags=re.IGNORECASE
    )
    # Remove Candidate/Applicant/Patient A/B/C/D labels, replace with just the title
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
        print(f"Error: Could not find {INPUT_FILE}. Make sure it is in the same directory.")
        return

    print(f"Running NAME-BASED prompts using {MODEL_NAME} (no A/B/C/D labels) on {INPUT_FILE}...\n")

    results_clean =