# NET Studio

A Streamlit practice app for CSIR NET Mathematical Sciences. Choose Mathematics or Statistics, browse subjects, and study one shuffled question at a time with difficulty colours, options, hints, worked solutions, theory, and two worked similar questions.

The project contains all **12 attached original PDFs and 1,420 available questions**. The February 2022 attachment contains questions 21–120 only; its 20 aptitude questions are missing. Every available question now has a learning pack: **1,336 scored solutions and 84 explained source issues**, with zero pending or unclassified questions. Source issues retain their derivations and are excluded from scoring. Exact per-paper counts are in data/coverage_report.json and the app's Question bank page.

The Papers page links an additional public February 2022 copy for locating the missing Part A. It has not been imported or counted as source coverage.

## Run

Use Python 3.10 or newer, open a terminal in this project directory, and create a virtual environment:

~~~bash
python -m venv .venv
~~~

Activate it with source .venv/bin/activate on macOS/Linux, or .venv\Scripts\Activate.ps1 in Windows PowerShell. Then:

~~~bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
~~~

Open the local URL printed by Streamlit, normally http://localhost:8501. Practising completed questions and downloading papers requires no API key.

If using the small source bundle instead of a repository containing the PDFs/images, first reconstruct the assets from your twelve original PDFs:

~~~bash
python tools/setup_assets.py --source-dir "/path/to/your/pdf/folder"
~~~

The setup script matches originals by SHA-256, so filenames can differ. It restores the checked image regions, including corrected crop boundaries, and preserves source metadata. A repository or full package with papers/ and assets/questions/ already populated needs no reconstruction.

## Study interface

- Mathematics and Statistics tracks, with aptitude accessible in both.
- Analysis, algebra, topology, number theory, calculus, differential equations, numerical methods, probability, inference, stochastic processes, regression, experimental design, and other subject categories.
- Topic, paper, part, difficulty, content-status, search, and bookmark filters.
- Shuffled queues with Previous, Next, and direct position navigation. Complete packs appear first.
- Typeset questions/options plus the exact original image for diagrams and source checks.
- Progressive hints, option-specific derivations, theory with hypotheses and pitfalls, and two worked transfer examples.
- Green/easy, orange/moderate, red/hard. These are editorial estimates. Unfinished questions are grey/unrated.
- Progress JSON download and restoration; imported scores are recomputed.
- Original PDF downloads and complete source/solution coverage reporting.

## Scoring and source checks

Part A questions are single correct and worth 2 marks, with a 0.5 wrong-answer penalty. Part B questions are single correct and worth 3 marks, with a 0.75 penalty. Part C permits multiple correct choices, is worth 4.75 marks, and has no negative marking; the complete answer set is required.

This is topic practice. The practice score does not enforce the full exam's per-part attempt limits.

Answers are derived independently from the attached question images. Candidate “Chosen Option” entries are never used as answer keys. Retrieved official keys are stored under data/official_keys/, matched by exact question ID.

After checking an answer or opening its solution, the app shows an official-key comparison and source link when the exact question ID is available. Unmapped and inaccessible keys are not represented as verified.

Malformed formulas, missing options, overlapping answers, or hypotheses changing the result receive a source_issue pack: full diagnosis, conditional intended answer where justified, theory, and examples. These remain unscored. Official-key disagreements are explained rather than silently correcting the printed question.

Pending questions remain accessible using the original image but lack a score or learning pack. Their OCR topic routing is provisional. Reviewed packs replace that routing with a checked subject classification.

## Content and validation

data/exam_questions.json holds the initial packs. Additional banks are in data/completed_papers/; the app loads every validated JSON there automatically. Each pack preserves its paper, question number, part, page, exact image, and answer provenance.

~~~bash
python tools/content_report.py --write --require-complete
python tools/check_official_keys.py --require-consistent
python -m unittest discover -s tests -v
~~~

To require complete coverage, or export all current learning packs:

~~~bash
python tools/content_report.py --require-complete
python tools/content_report.py --export learning_packs.json
~~~

Checks cover source coverage, original-PDF hashes, image decoding, marks and penalties, exact multiple-choice scoring, safe progress import, pack schema/provenance, and actual Streamlit widget flows when its runtime is installed. The included GitHub Actions workflow is configured to install dependencies and run these checks. A skipped Streamlit test does not establish runtime or visual correctness.

All 1,420 source images were rebuilt and decoded successfully from their saved PDF regions. The final test run passed 33 checks; four Streamlit interaction checks were skipped. Streamlit was unavailable in the authoring environment and dependency retrieval failed. Actual UI runtime verification remains pending in an environment where requirements can be installed.

## Project files and GitHub

Keep the PDFs, question PNGs, source metadata, worked JSON packs, app files, requirements, and tests together. The repository ignores local environments, secrets, progress files, caches, and transient drafts.

The repository is prepared locally and GitHub access is connected. A destination repository for NET Studio still needs to be provided; the connected repositories currently belong to other projects. No remote upload has been made. A local commit does not mean a successful GitHub upload.

## Optional draft backend

solver.py and tools/solve_bank.py can generate ungraded drafts if OPENAI_API_KEY is configured on your own server. This optional feature incurs API charges. It is not required for independently authored packs. Drafts need review and cannot replace reviewed answers. Keep a server using your API key private and never commit secrets.

UI imports stay in the browser session until exported. Server files persist according to the hosting platform; download progress before an ephemeral server resets.

NET Studio is independent and is not affiliated with Unacademy, CSIR, or NTA.
