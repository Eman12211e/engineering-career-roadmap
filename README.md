# Engineering Career Roadmap

Compare a job posting with your résumé. The app shows which skills are covered
and which are missing, explains how it decided, and helps you write accurate
bullets from your own evidence. It never invents numbers, tools, outcomes or
seniority for you.

- Live app: TODO: live link
- Screenshot: TODO: screenshot

## How coverage is scored

The score is **skill coverage**, not hiring probability. It says how much of a
posting's skill list your résumé shows. It does not predict whether anyone will
interview or hire you.

Required skills carry 80% of the weight and preferred skills 20%. Details are
in `docs/SCORING.md`.

## About the market data

The market data is a **synthetic sample of 225 postings**. It is not the real
job market, and percentages like "X% of postings in this synthetic sample
mention..." describe that sample only.

## Local setup

```
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q tests
```

## Privacy

Résumé and posting text is processed in memory and is not logged or written to
disk by the engine.
