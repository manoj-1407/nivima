# Contributing to Nivima

## Setup

```bash
git clone https://github.com/manoj-1407/nivima
cd nivima
conda create -n nivima python=3.11
conda activate nivima
make dev-install
cp .env.example .env
make docker-up
make migrate
```

## Branch Strategy

```
main        — stable, deployable
dev         — integration branch
feat/*      — new features
fix/*       — bug fixes
research/*  — experimental / paper work
```

## Before Submitting a PR

```bash
make format     # auto-format
make lint       # check for issues
make test-unit  # run unit tests
```

## Adding a New Language

1. Add language code to `LANGUAGE_CODES` in `src/translation/translator.py`
2. Add TTS model in `INDIC_TTS_MODELS` in `src/tts/synthesizer.py`
3. Add phoneme coverage sentences in `scripts/collect_volunteer_dataset.py`
4. Add domain glossary entries in `src/translation/domain_adapter.py`
5. Add MFA acoustic model in `src/alignment/force_aligner.py`

## Adding a New Viseme

1. Add phoneme → viseme mapping in `src/translation/phoneme_map.py`
2. Add blendshape weights in `VISEME_TO_BLENDWEIGHTS`
3. Add test case in `tests/unit/test_phoneme_map.py`
4. Document the articulatory basis in `research/RESEARCH_NOTES.md`

## Code Style

- No comments in production code — code should be self-documenting
- No textbook formatting — write like an experienced developer
- Type hints on all function signatures
- structlog for all logging — no print statements
- Explicit error handling — no bare `except:`
