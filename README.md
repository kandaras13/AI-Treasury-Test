# TTB LabelVerify AI

A working proof-of-concept for the Treasury/TTB take-home project: an AI-assisted alcohol label verification app.

## What it does

- Reads label images with **local OCR** (Tesseract).
- Compares label content against application data.
- Uses human-equivalent matching for brand names, so `STONE'S THROW` and `Stone's Throw` do not become false failures.
- Validates ABV and optionally checks proof consistency.
- Checks class/type, net contents, producer/bottler, and country of origin when provided.
- Validates the prescribed **Government Health Warning** wording and uppercase header.
- Supports **single-label** and **batch** uploads.
- Returns clear **PASS / REVIEW / FAIL** decisions and a downloadable CSV.
- Reports processing time to make the stakeholder's ~5-second usability constraint visible.
- Keeps uploaded images in memory for the request and does not persist them.

## Why this architecture

The stakeholder notes say the government network may block external ML/API endpoints. For that reason, the prototype intentionally uses local OCR rather than a cloud vision API. That makes the proof-of-concept more reliable in a restricted environment and avoids sending label images to an external provider.

The project is intentionally a **decision-support tool**, not an autonomous regulatory decision maker. Low-confidence or ambiguous results are surfaced as `REVIEW`.

## Run locally

### 1. Install Tesseract

**Windows**
Install Tesseract OCR and ensure `tesseract.exe` is on PATH.

**macOS**
```bash
brew install tesseract
```

**Ubuntu/Debian**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### 2. Create a Python environment

```bash
python -m venv .venv
```

Activate it, then:

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload this project.
2. In Streamlit Community Cloud, create a new app from the repository.
3. Set the main file to `app.py`.
4. `requirements.txt` installs Python dependencies.
5. `packages.txt` requests the `tesseract-ocr` system package.
6. Deploy and test with the files in `sample_data/`.

No secrets or API keys are required.

## Test

```bash
pytest -q
```

## Core design decisions

### Local OCR instead of cloud AI
The discovery notes explicitly warn that outbound traffic may be blocked. Local OCR is predictable, low-cost, privacy-friendly, and suitable for a prototype.

### Fuzzy brand matching
Compliance agent feedback indicates that punctuation/capitalization differences can be harmless. Brand and descriptive fields therefore use normalized fuzzy matching and can route ambiguous cases to human review.

### Strict health-warning treatment
TTB requires prescribed warning wording. The prototype treats near-matches as `REVIEW`, not automatic approval.

### Batch processing
The UI accepts multiple images and produces a consolidated results table/CSV to address importer submissions containing hundreds of labels.

### Human-in-the-loop
OCR can misread glare, curvature, stylized fonts, and tiny text. An uncertain result is explicitly surfaced rather than silently converted into a pass.

## Important prototype limitation: bold detection

TTB requires `GOVERNMENT WARNING` to be in capitals and bold. OCR can reliably read words and case, but font-weight detection from arbitrary raster photographs is not dependable enough for an automatic legal determination. This prototype therefore:

1. checks the prescribed warning wording,
2. checks the uppercase header,
3. identifies ambiguous OCR as `REVIEW`, and
4. tells the agent to visually confirm bold formatting.

A production system should add a layout/vision model trained against labeled examples and validate font size/contrast/weight as part of an approved compliance pipeline.

## Assumptions

- The application values entered in the UI are the authoritative values to compare against.
- The prototype does not integrate with COLA.
- Images are not retained.
- It is intended to help agents prioritize and review labels, not replace agent judgment.
- The five-second target is tracked in the UI. Actual performance depends on image size and hosting CPU.
