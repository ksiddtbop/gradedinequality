# Graded Algorithmic Inequality

A matched-pair correspondence audit of caste bias in a large language model.

**Status:** Poster-stage audit. Single model, single language, one round of trials. The full paper is in preparation.

**Author:** Kunwar Siddharth, PhD Researcher, UPES Dehradun

---

## 1. The problem

Caste is a graded hierarchy. Each group holds relative privilege over those ranked below it; Dalits, at the bottom, carry the cumulative weight of the system. As language models move from chat interfaces into the infrastructure of hiring, education, healthcare, and housing, the concern is not occasional biased outputs but the reproduction of this graded ordering at computational scale.

This repository asks one question: when a model is given two otherwise-identical candidates and must choose between them, does the choice track caste-coded surnames in the way the graded inequality hypothesis predicts?

> "Caste is not a physical object like a wall of bricks or a line of barbed wire. Caste is a notion, it is a state of the mind."
> — B. R. Ambedkar, *Annihilation of Caste*

---

## 2. The hypothesis

**H1 (graded inequality, four-stratum form):** In forced-choice A/B selection tasks, the model's probability of selecting a candidate falls as caste position falls in the official Indian hierarchy:

> *P*(selected | General) > *P*(selected | OBC) > *P*(selected | SC), with ST examined separately because of name-salience confounds (see §6).

This is the four-stratum form the data in this repository currently supports. A six-stratum form (Brahmin > Kshatriya > Vaishya > OBC > SC > ST) is part of the larger project but is not tested here.

---

## 3. The method

**Design.** Matched-pair correspondence audit, after Thorat and Attewell (2007). Each trial presents the model with two otherwise-identical candidates whose only difference is a caste-coded surname. The model is asked to choose one and justify the choice in three to four sentences. The justification is kept for qualitative reading; the headline measure is the choice itself.

**Scenarios.** Five decision contexts, each grounded in a documented site of caste-based exclusion (see `data/scenarios.csv` for the full prompt texts):

| ID | Scenario | Domain | Real-world referent |
|----|----------|--------|---------------------|
| S1 | Hiring shortlisting for a backend engineer role (Bengaluru) | allocative | Thorat and Attewell 2007 |
| S2 | Merit-cum-means scholarship for a B.Sc. Physics student (Lucknow) | allocative | Rohith Vemula context |
| S3 | RWA General Secretary election (Pune) | representational | RWA and panchayat exclusion patterns |
| S4 | Hospital triage for one available general-ward bed (eastern UP) | allocative | Payal Tadvi case; NFHS-5 |
| S5 | Rental housing in Sigra colony (Varanasi) | allocative + representational | UP residential exclusion patterns |

**Names.** Twenty caste-coded names spanning four broad categories (General, OBC, SC, ST). Each name is annotated with a finer internal position; see `data/names.csv` and `data/comparison_names.csv` for matched pairs.

**Model.** `llama-3.3-70b-versatile` served via Groq.

**Inference settings.** Temperature: 0. Single completion per prompt. See `results/results_llama3_70b.csv` for the full per-trial log, including timestamp and the exact model string returned by the API.

---

## 4. Results

A single model, a single round, ten name pairs across five scenarios. **Win rate** is the proportion of forced-choice trials in which a name from the given group was selected.

| Group | Win rate | n trials |
|-------|----------|----------|
| General | 73% | (see results file) |
| OBC | 40% | (see results file) |
| SC | 13% | (see results file) |
| ST | reported separately, see §6 | |

The General > OBC > SC ordering is consistent with the graded inequality hypothesis for `llama-3.3-70b-versatile` under this audit design. It does not generalise to other models or to other prompt formulations without further testing.

---

## 5. What this study does not show

Naming these so a reader does not have to guess.

- **One model only.** Findings are about `llama-3.3-70b-versatile`. Other models may behave differently. Cross-model comparison is future work.
- **One language only.** Prompts are in English. Caste cues in Hindi, Marathi, Tamil, or other Indian languages may surface different patterns.
- **Surname as the sole caste cue.** Real-world caste signals include first names, place of origin, dietary mention, and language register. The audit isolates surname; this is a clean design at the cost of ecological breadth.
- **Forced binary choice.** The A/B format collapses graded judgments into a single bit. Suitability scores, qualitative tone, and the justification text would carry more signal; they are recorded in the results file but not headlined here.
- **No human validation of name caste-coding.** The mapping from surname to caste category in `data/names.csv` is the author's, drawing on published surname lists and regional knowledge. Several surnames (Singh, Kumar) are noted as ambiguous in the file itself.
- **Small n.** Ten pairs across five scenarios is a poster-stage probe, not a statistical estimate. No confidence intervals are reported because the design does not yet support them honestly.

---

## 6. A note on the ST result

The ST stratum in `data/names.csv` includes Birsa Munda. Birsa Munda is a nationally recognised historical figure; the model almost certainly recognises the name independent of any caste signal, which inflates selection rates in a way that has nothing to do with the audit's question. Including Birsa Munda yields a 100% ST win rate, which is not a finding about caste — it is a finding about name salience.

The ST stratum is therefore reported separately rather than placed in the ordered hierarchy. A clean ST test requires names that are caste-coded without being historically famous; this is a known limitation of the current name list and is on the to-do list for the next round.

---

## 7. Repository

```
gradedinequality/
├── README.md                       this file
├── LICENSE
├── requirements.txt
├── data/
│   ├── names.csv                   20 caste-coded names with annotation
│   ├── scenarios.csv               5 decision scenarios, full prompt texts
│   ├── comparison_names.csv        10 matched pairs and what each tests
│   └── README.md                   per-file column documentation
├── scripts/
│   └── run_audit.py                runs all pairs × scenarios on Groq
└── results/
    ├── results_llama3_70b.csv      per-trial log
    └── README.md                   how the results file was produced
```

---

## 8. Reproducing the audit

```bash
git clone https://github.com/ksiddtbop/gradedinequality.git
cd gradedinequality
pip install -r requirements.txt
export GROQ_API_KEY=<your key from console.groq.com>
python scripts/run_audit.py
```

A free Groq API key from <https://console.groq.com> is sufficient. The script writes a fresh `results/results_llama3_70b_<timestamp>.csv` rather than overwriting the existing file.

---

## 9. Citation

If this work is useful to you, please cite as:

```
Siddharth, K. (2026). Graded Algorithmic Inequality:
A matched-pair correspondence audit of caste bias in a large language model.
GitHub repository. https://github.com/ksiddtbop/gradedinequality
```

---

## 10. Contact

Kunwar Siddharth
PhD Researcher, UPES Dehradun
kunwarpankaj.siddharth@ddn.upes.ac.in

---

## License

Code is released under the MIT License. Data files (the prompts and the name list) are released under CC BY 4.0 with the request that downstream use credits this repository and reads §5 before drawing conclusions.

---

## Keywords

caste bias · graded inequality · algorithmic auditing · fairness in NLP · matched-pair audit · correspondence study · Dalit · Ambedkar · AI governance · large language models
