# VeriLens AI

### Multimodal Deepfake Detection & Explainable Content Verification

**Analyze digital content. Inspect the evidence. Understand the
uncertainty.**

A research-oriented web platform for examining text, images, audio, and
video for potential manipulation and cross-modal inconsistencies.

`<br/>`{=html}

![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Build-Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Tailwind
CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![Python](https://img.shields.io/badge/Backend-Python%20%2F%20FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Status](https://img.shields.io/badge/Project-Academic%20Research-243447?style=for-the-badge)
:::

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Problem Statement](#problem-statement)
-   [Objectives](#objectives)
-   [Key Features](#key-features)
-   [How It Works](#how-it-works)
-   [Application Pages](#application-pages)
-   [Technology Stack](#technology-stack)
-   [Architecture](#architecture)
-   [Getting Started](#getting-started)
    -   [Prerequisites](#prerequisites)
    -   [Frontend Setup](#frontend-setup)
    -   [Backend Setup](#backend-setup)
    -   [Connecting the Frontend and
        Backend](#connecting-the-frontend-and-backend)
-   [API Integration](#api-integration)
-   [Supported File Types](#supported-file-types)
-   [Research and Evaluation](#research-and-evaluation)
-   [Project Structure](#project-structure)
-   [Configuration](#configuration)
-   [Responsible AI, Privacy, and
    Security](#responsible-ai-privacy-and-security)
-   [Limitations](#limitations)
-   [Roadmap](#roadmap)
-   [Academic Context](#academic-context)
-   [Contributing](#contributing)
-   [License](#license)
-   [Acknowledgements and References](#acknowledgements-and-references)

------------------------------------------------------------------------

## Overview

**VeriLens AI** is a multimodal content verification project developed
around Natural Language Processing (NLP), computer vision, audio
analysis, and explainable AI. It is designed to assess digital media
using available evidence from one or more modalities rather than relying
exclusively on a single detector.

The system is intended to return one of three outcomes:

  -----------------------------------------------------------------------
  Verdict                             Meaning
  ----------------------------------- -----------------------------------
  **REAL**                            The available evidence supports the
                                      content's authenticity.

  **FAKE**                            The available evidence indicates
                                      possible manipulation or
                                      substantial inconsistency.

  **UNCERTAIN**                       Evidence is incomplete, confidence
                                      is insufficient, or modalities
                                      disagree.
  -----------------------------------------------------------------------

Where supported by the configured analysis pipeline, a report includes a
confidence score, modality-level scores, evidence descriptions, a
natural-language explanation, and additional visualizations.

The frontend is built with React and Vite. It communicates with a
backend API for asynchronous analysis jobs, report retrieval, review
submission, history, dataset statistics, and research results.

> **Important:** VeriLens AI is an AI-assisted assessment tool. A
> prediction is not definitive proof that media is authentic or
> manipulated. Model outputs, visualizations, and research metrics must
> be interpreted in context.

## Problem Statement

Deepfakes and manipulated media can combine synthetic faces, altered
speech, misleading captions, or genuine media paired with unrelated
text. A detector that examines only one modality may miss contradictions
that become apparent when different sources of evidence are considered
together.

VeriLens AI addresses the following research question:

> **Can multimodal NLP combine textual and non-textual evidence to
> improve deepfake detection over single-modality baselines while
> providing useful, evidence-grounded explanations?**

The project emphasizes cross-modal consistency, uncertainty-aware
classification, transparent evidence presentation, and experimental
evaluation.

## Objectives

-   Accept text and supported media files through a single verification
    workspace.
-   Identify the modalities present in a submission.
-   Present a structured REAL, FAKE, or UNCERTAIN result from the
    connected analysis backend.
-   Display confidence, modality scores, evidence, and explanations when
    returned by the backend.
-   Inspect potential inconsistencies between text, images, audio, and
    video.
-   Preserve access to previous analyses and support comparison between
    results.
-   Provide human-review controls and downloadable analysis artifacts.
-   Expose dataset and research information through dedicated
    application pages.
-   Evaluate multimodal approaches against single-modality baselines and
    document failure cases.

## Key Features

### Content verification

-   Drag-and-drop file uploads and file browsing.
-   Text, caption, or transcript input.
-   Automatic modality indicators for text, image, audio, and video.
-   Upload progress and processing-stage feedback.
-   Analysis reports with verdict, confidence, and explanatory evidence.
-   Error messages and retry behavior for failed requests.

### Explainability and evidence

Depending on the returned analysis data and enabled backend
capabilities, the report interface can display:

-   REAL, FAKE, and UNCERTAIN class probabilities.
-   Per-modality fake-probability scores.
-   Evidence items with severity and descriptions.
-   Highlighted text phrases and extracted entities.
-   An image error-level-analysis (ELA) heatmap.
-   Audio transcripts and video/audio segment timelines.
-   Cross-modal consistency scores.
-   Evidence contribution bars and an evidence graph.
-   Model-version information and processing time.

### Analysis management

-   Verification history with verdict filtering.
-   Side-by-side comparison of two analyses.
-   Human review with a reviewer verdict and notes.
-   PDF report access.
-   JSON export of an analysis result.
-   Deletion of an analysis through the backend API.

### Research interface

-   Research results dashboard.
-   Dataset statistics explorer.
-   Difficult-case gallery.
-   Methodology and project information pages.
-   Sanity playground for inspecting example inputs and expected
    behavior.

The availability and completeness of research results depend on the
backend and experiment artifacts supplied with the deployment.
Demonstration values must not be presented as measured model
performance.

## How It Works

The intended verification pipeline is:

``` text
Text / Image / Audio / Video
             |
             v
      Input Validation
             |
             v
     Modality Detection
             |
             v
   Modality-Specific Analysis
   (text, vision, audio, video)
             |
             v
      Evidence Extraction
             |
             v
       Multimodal Fusion
             |
             v
 Cross-Modal Consistency Checks
             |
             v
 REAL / FAKE / UNCERTAIN
             |
             v
 Confidence + Explanation
             |
             v
      Verification Report
```

1.  **Input:** A user enters text and/or uploads supported media.
2.  **Upload and job creation:** The frontend sends the submission to
    the backend and displays upload progress.
3.  **Analysis:** The frontend polls the job endpoint and reflects the
    processing stage returned by the service.
4.  **Report retrieval:** When processing finishes, the frontend opens
    the corresponding analysis report.
5.  **Evidence inspection:** The user reviews the verdict, modality
    scores, evidence, explanation, and any available visualizations.
6.  **Review or export:** The user can submit a human review or export
    the report as PDF or JSON.

The diagram describes the intended system flow. The exact models, fusion
strategy, and supported evidence types depend on the backend
implementation and configuration.

## Application Pages

  -----------------------------------------------------------------------
  Route                               Purpose
  ----------------------------------- -----------------------------------
  `/`                                 Landing page and introduction to
                                      VeriLens AI.

  `/verify`                           Upload media, enter text, and start
                                      a verification job.

  `/analysis/:id`                     Inspect an analysis report,
                                      evidence, model information, and
                                      exports.

  `/playground`                       Explore example inputs and
                                      sanity-check scenarios.

  `/history`                          Browse previous analyses and filter
                                      by verdict.

  `/compare`                          Compare two existing analysis
                                      results.

  `/research`                         View research and model evaluation
                                      results supplied by the backend.

  `/dataset`                          Explore dataset statistics.

  `/cases`                            Inspect difficult or illustrative
                                      cases.

  `/methodology`                      Review the methodology and
                                      technical approach.

  `/about`                            Read project and responsible-use
                                      information.
  -----------------------------------------------------------------------

## Technology Stack

### Frontend

  Technology         Role
  ------------------ ------------------------------------------------
  React              Component-based user interface.
  Vite               Frontend development server and build tooling.
  React Router       Client-side navigation.
  Tailwind CSS       Utility-first styling and responsive layout.
  Recharts           Charts and probability visualizations.
  JavaScript / JSX   Application logic and UI components.

### Backend and analysis service

  -----------------------------------------------------------------------
  Technology                          Role
  ----------------------------------- -----------------------------------
  Python                              Backend and model-integration
                                      language.

  FastAPI                             Recommended API framework for the
                                      inference service.

  Modality-specific models            Text, image, audio, and/or video
                                      analysis.

  Fusion and decision logic           Combines available evidence into a
                                      final assessment.

  Persistent storage                  Optional storage for analysis
                                      metadata, review data, and research
                                      results.
  -----------------------------------------------------------------------

The supplied frontend calls a REST-style API and expects asynchronous
job processing. The backend's exact model libraries, database, and
inference infrastructure should be documented according to the actual
deployment rather than assumed from the UI.

## Architecture

``` text
+---------------------------+
|       React + Vite        |
|  Upload / Reports / UI    |
+-------------+-------------+
              |
              | HTTP / FormData
              v
+---------------------------+
|        Backend API        |
|  Job creation and status  |
|  Analysis and report data |
+-------------+-------------+
              |
              v
+---------------------------+
|    Analysis Pipeline      |
| Text | Image | Audio | Video
| Evidence | Fusion | Verdict|
+-------------+-------------+
              |
              v
+---------------------------+
| Results / Metadata Store  |
| History / Reviews / Metrics|
+---------------------------+
```

For deployment, the frontend and inference service may be hosted
separately. Configure the API URL, CORS policy, file-size limits,
timeouts, and secure transport to match the deployment environment.

## Getting Started

### Prerequisites

Install the following tools:

-   **Node.js**: a current LTS release.
-   **npm**: included with Node.js.
-   **Python**: a version supported by the backend's dependency file.
-   **Git**: for cloning and version control.

A running backend service is required for content analysis and
data-driven pages. The frontend alone provides the interface but cannot
perform model inference without the API.

### Frontend Setup

1.  Clone the repository:

    ``` bash
    git clone <YOUR_REPOSITORY_URL>
    cd <YOUR_REPOSITORY_DIRECTORY>
    ```

2.  Install frontend dependencies:

    ``` bash
    npm install
    ```

3.  Create a local environment file named `.env` in the frontend project
    root:

    ``` env
    VITE_API_URL=http://127.0.0.1:8000
    ```

    The frontend API helper uses `VITE_API_URL` when provided and
    otherwise falls back to `/api`.

4.  Start the development server:

    ``` bash
    npm run dev
    ```

5.  Open the local URL printed by Vite, commonly
    `http://localhost:5173`.

6.  For a production build:

    ``` bash
    npm run build
    ```

    To preview the built frontend locally:

    ``` bash
    npm run preview
    ```

> These commands assume the repository root contains the frontend's
> `package.json`. If the frontend is inside a subdirectory, run the
> commands from that directory.

### Backend Setup

The supplied frontend source does not include the backend implementation
or its dependency manifest. The commands below are a typical setup for a
FastAPI backend; adjust the entry-point module and dependency filename
to match the repository.

1.  Navigate to the backend directory:

    ``` bash
    cd backend
    ```

2.  Create and activate a virtual environment:

    **Windows PowerShell**

    ``` powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    **macOS / Linux**

    ``` bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  Install the backend's declared dependencies. If the repository
    contains `requirements.txt`:

    ``` bash
    pip install -r requirements.txt
    ```

4.  Start the API using the actual FastAPI module. For example, if the
    entry point is `main.py` and the app object is named `app`:

    ``` bash
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
    ```

5.  Check the backend's health endpoint, if implemented:

    ``` text
    http://127.0.0.1:8000/health
    ```

Do not use the example module name unless it matches the actual backend
files.

### Connecting the Frontend and Backend

-   Set `VITE_API_URL` to the backend's reachable base URL.
-   Ensure the backend accepts requests from the frontend's local
    origin.
-   Confirm that the backend implements the job, analysis, history,
    review, report, research, dataset, and case routes expected by the
    frontend.
-   Restart Vite after changing `.env` values.
-   Never place private API keys or server-side secrets in `VITE_*`
    variables. Vite exposes these variables to client-side code.

## API Integration

The frontend API helper uses the following endpoints. The backend must
implement compatible request and response schemas.

  -----------------------------------------------------------------------------
  Method                  Endpoint                      Purpose
  ----------------------- ----------------------------- -----------------------
  `POST`                  `/jobs`                       Upload text/files and
                                                        create an asynchronous
                                                        analysis job.

  `GET`                   `/jobs/{job_id}`              Retrieve job status and
                                                        processing stage.

  `GET`                   `/analysis/{id}`              Retrieve the completed
                                                        analysis report.

  `POST`                  `/analysis/{id}/review`       Submit a reviewer
                                                        verdict and notes.

  `DELETE`                `/analysis/{id}`              Delete an analysis.

  `GET`                   `/history?verdict=`           Retrieve history,
                                                        optionally filtered by
                                                        verdict.

  `GET`                   `/research/results`           Retrieve research
                                                        results.

  `GET`                   `/dataset/statistics`         Retrieve dataset
                                                        statistics.

  `GET`                   `/cases`                      Retrieve difficult or
                                                        illustrative cases.

  `GET`                   `/analysis/{id}/report.pdf`   Download the PDF
                                                        report.
  -----------------------------------------------------------------------------

The frontend also defines a direct `POST /analyze` helper for
synchronous analysis. The current verification workflow uses the
asynchronous `/jobs` flow.

### Expected analysis response

The report UI expects a response containing fields broadly similar to
the following. This is a schema illustration, not a claim that every
field is always populated.

``` json
{
  "id": "analysis-id",
  "prediction": "UNCERTAIN",
  "confidence": 0.78,
  "probabilities": {
    "REAL": 0.16,
    "FAKE": 0.22,
    "UNCERTAIN": 0.62
  },
  "modalities": {
    "text": 0.34,
    "image": 0.71,
    "audio": null,
    "video": null
  },
  "evidence": [
    {
      "type": "semantic_mismatch",
      "severity": "medium",
      "description": "The text and visual evidence may be inconsistent."
    }
  ],
  "explanation": "The available evidence is mixed, so the result requires further review.",
  "timestamp": 1791540000,
  "processing_ms": 2400
}
```

The API's real response schema is authoritative. Update the frontend and
this documentation if the backend uses different field names or data
types.

## Supported File Types

The verification interface advertises the following media formats:

  Modality   Formats
  ---------- -----------------------------------------------
  Text       Text entered in the caption/transcript field.
  Images     JPG, JPEG, PNG, WEBP.
  Audio      MP3, WAV, M4A.
  Video      MP4, MOV, WEBM.

Frontend file selection is not a substitute for server-side validation.
The backend should validate file extensions, MIME types, file sizes,
content, and processing limits.

## Research and Evaluation

VeriLens AI is intended to support experimental analysis, not just a
prediction interface. The academic brief identifies the following
research tasks.

  -----------------------------------------------------------------------
  Experiment                          Purpose
  ----------------------------------- -----------------------------------
  Single-modality baseline            Test whether combining modalities
  vs. multimodal model                improves performance.

  Fusion strategy or architecture     Compare at least two multimodal
  comparison                          approaches.

  Generalization experiment           Test across a different
                                      manipulation type, data source,
                                      language, or modality combination.

  Modality ablation                   Remove one modality at a time to
                                      estimate its contribution.

  Difficult-case analysis             Analyze at least 15 challenging or
                                      incorrectly classified examples.

  Explanation evaluation              Assess whether highlighted evidence
                                      is relevant to the prediction.
  -----------------------------------------------------------------------

Recommended metrics include accuracy, precision, recall, F1-score,
ROC-AUC and/or PR-AUC where appropriate, confusion matrices, class-wise
scores, and cross-dataset or cross-manipulation results where feasible.

Potential datasets named in the course brief include:

-   [FaceForensics++](https://github.com/ondyari/FaceForensics)
-   [Deepfake Detection Challenge
    (DFDC)](https://ai.meta.com/datasets/dfdc/)
-   [FakeAVCeleb](https://github.com/DASH-Lab/FakeAVCeleb)
-   [Fakeddit](https://github.com/entitize/Fakeddit)

Review each dataset's license, access conditions, permitted use,
provenance, and consent requirements before using or redistributing
data.

**Research integrity:** Populate the dashboard with measured results
from reproducible experiments. Clearly label mock, sample, or
illustrative values; do not report them as real model performance.

## Project Structure

The exact repository layout may vary. Based on the supplied frontend
files, the key application files include:

``` text
VeriLens-AI/
├── src/                         # If the frontend uses a src directory
│   ├── App.jsx                  # Routes, pages, and application UI
│   ├── api.js                   # API requests and backend URL configuration
│   ├── index.css                # Tailwind directives and global styles
│   └── main.jsx                 # React entry point
├── backend/                     # Backend service, if included in the repository
│   ├── main.py                  # Example only; actual entry point may differ
│   └── requirements.txt         # Example only; use the real dependency manifest
├── public/                      # Static frontend assets, if present
├── .env                         # Local environment variables; do not commit secrets
├── package.json                 # Frontend scripts and dependencies
└── README.md
```

The files supplied for this README include `App.jsx`, `api.js`,
`index.css`, and `main.jsx`. Use the repository's actual paths as the
source of truth; do not create duplicate folders solely to match this
illustration.

## Configuration

### Frontend environment variables

  -------------------------------------------------------------------------
  Variable                Purpose                 Example
  ----------------------- ----------------------- -------------------------
  `VITE_API_URL`          Base URL for the        `http://127.0.0.1:8000`
                          backend API.            

  -------------------------------------------------------------------------

When deployed, set the variable through the hosting provider's
environment settings. The frontend falls back to `/api` if
`VITE_API_URL` is not set, so configure the hosting platform's proxy or
rewrite rules accordingly.

### Backend configuration

Backend settings depend on the models and infrastructure actually used.
A production setup should document:

-   Model names and versions.
-   Model and dataset locations.
-   Maximum upload size and accepted media types.
-   Temporary upload storage and cleanup behavior.
-   Database connection settings, if a database is used.
-   CORS origins and API rate limits.
-   Logging, timeouts, and health checks.
-   Any credentials required by external services, stored only on the
    server.

## Responsible AI, Privacy, and Security

Deepfake detection can affect reputation, trust, and access to
information. Use the system responsibly.

-   Treat predictions as indicators for further assessment, not
    conclusive proof.
-   Preserve the UNCERTAIN outcome when evidence is insufficient or
    conflicting.
-   Do not upload private or sensitive media without appropriate
    permission.
-   Document dataset sources, licenses, consent conditions, and known
    biases.
-   Validate uploaded files and impose file-size and processing limits
    on the server.
-   Sanitize filenames and input data.
-   Use HTTPS for deployed services and restrict access to stored
    reports.
-   Avoid retaining original media longer than necessary; define
    retention and deletion rules.
-   Do not expose API keys, credentials, or internal infrastructure
    details in frontend code.
-   Evaluate performance across relevant classes, sources, and
    manipulation types to identify failure patterns.

## Limitations

-   Detection quality depends on the models, data, preprocessing, and
    fusion strategy configured in the backend.
-   A frontend visualization does not itself establish that the
    underlying model supports a particular analysis method.
-   Some capabilities, such as synthetic-speech detection, lip-sync
    analysis, cross-modal embeddings, or localized heatmaps, require
    corresponding backend/model support.
-   A modality score is meaningful only in the context of the model and
    score definition that produced it.
-   Confidence is not necessarily a calibrated probability of truth.
-   Performance can degrade under compression, low resolution, noisy
    audio, unfamiliar manipulation methods, domain shifts, or unseen
    languages.
-   The research dashboard is only as reliable as the experiments and
    metrics supplied to it.

## Roadmap

Potential next steps for the project include:

-   [ ] Complete and document all backend inference routes.
-   [ ] Validate upload security and temporary-file cleanup.
-   [ ] Connect text, image, audio, and video analysis to documented
    models.
-   [ ] Implement and evaluate multimodal fusion strategies.
-   [ ] Calibrate uncertainty and document the decision thresholds.
-   [ ] Run baseline, fusion, generalization, and modality-ablation
    experiments.
-   [ ] Document at least 15 difficult cases and their failure modes.
-   [ ] Evaluate explanation relevance and faithfulness.
-   [ ] Ensure dataset and research pages display reproducible results.
-   [ ] Add deployment instructions, health checks, and monitoring.
-   [ ] Document accessibility, privacy, and data-retention behavior.

## Academic Context

This project is aligned with the **CSET 346: Natural Language
Processing** course project, *Multimodal NLP for Deepfake Detection and
Explainable Content Verification*.

The project explores:

-   Natural Language Processing and semantic consistency.
-   Multimodal representation and fusion.
-   Deepfake and manipulated-content detection.
-   Explainability and evidence presentation.
-   Uncertainty estimation and human review.
-   Experimental evaluation and error analysis.

## Contributing

Contributions should improve correctness, reproducibility, usability, or
responsible handling of media.

1.  Fork the repository.
2.  Create a focused branch: `git checkout -b feature/your-change`.
3.  Make and test your changes.
4.  Document new environment variables, endpoints, models, and
    limitations.
5.  Open a pull request describing the change and how it was tested.

Avoid committing datasets, uploaded media, model weights, credentials,
local environment files, or generated reports unless their inclusion is
permitted and intentional.

## License

No license information was included in the supplied project files. Until
a license is added to the repository, do not assume that the source code
or associated assets are available for unrestricted reuse.

If the project is released publicly, add a `LICENSE` file and document
any separate licenses that apply to datasets, model weights, and
third-party assets.

## Acknowledgements and References

The project scope is informed by the supplied CSET 346 Natural Language
Processing brief and its suggested background resources:

1.  Rössler, A. et al. (2019). *FaceForensics++: Learning to Detect
    Manipulated Facial Images*. IEEE/CVF International Conference on
    Computer Vision.
2.  Dolhansky, B. et al. (2020). *The DeepFake Detection Challenge
    Dataset*. arXiv:2006.07397.
3.  Khalil, M. et al. (2021). *FakeAVCeleb: A Novel Audio-Video
    Multimodal Deepfake Dataset*. arXiv:2108.05080.
4.  Sharma, K. et al. (2020). *Combating Fake News: A Survey on
    Identification and Mitigation Techniques*. ACM Computing Surveys.

------------------------------------------------------------------------

::: {align="center"}
**VeriLens AI**\
*Multimodal evidence. Explainable verification. Responsible AI.*
:::
