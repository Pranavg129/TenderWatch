# TenderWatch — Demo and Submission Notes

## Demo story

TenderWatch aims to help Indian MSMEs manage tender discovery and bid preparation without a dedicated tender desk.

Suggested walkthrough:
1. Open a clearly labelled sample tender.
2. Show the extracted tender details and source/reference.
3. Compare the tender requirements with a sample business profile.
4. Review the resulting eligibility explanation and missing information.
5. Show how a corrigendum or changed deadline should be highlighted, if that workflow is implemented.

Only demonstrate steps that work in the current build. If a step is mocked or uses sample data, say so explicitly.

## Before the demo

- [ ] Install backend dependencies in a clean virtual environment.
- [ ] Start the backend and confirm the health/API route responds.
- [ ] Run the test suite with `pytest`.
- [ ] Confirm the frontend points to the correct backend URL.
- [ ] Confirm sample tender data is labelled as sample/demo data.
- [ ] If using TinyFish, configure credentials locally through `.env`; never commit API keys.
- [ ] Verify any live tender details, deadlines, and corrigenda on the official source.
- [ ] Prepare a fallback demo using local sample data in case network/API access fails.

## Data and trust safeguards

- Do not invent tender listings, deadlines, buyer names, or source URLs.
- Show source links and the time of retrieval for live data when available.
- Treat extracted eligibility as decision support, not a guarantee of qualification.
- Distinguish verified source facts, extracted fields, and AI-generated summaries.
- Do not submit bids or take external actions without explicit user review.

## Current implementation status

This file is a checklist, not evidence that each capability is implemented. Update this section as the team verifies working features and tests.
