# Ollama Cold Outreach Emailer

This toolkit automates the process of generating personalized cold outreach emails using local LLMs (via Ollama) and sending them via SMTP (e.g., Gmail).

## Features

-   **AI Generation**: Uses local Ollama models (default: `llama3.1:8b`) to read company descriptions and generates highly personalized emails.
-   **Smart Parsing**: Automatically extracts subject lines and email bodies from the AI output.
-   **Automated Sending**: Sends emails sequentially with delays to respect rate limits.
-   **State Management**: Tracks which companies have been processed and sent to avoiding duplicates.

## Prerequisites

1.  **Python 3.8+**
2.  **Ollama**: Installed and running with the desired model (e.g., `llama3.1:8b`).
    -   [Download Ollama](https://ollama.com/)
    -   Run `ollama pull llama3.1:8b`
3.  **Dependencies**:
    ```bash
    pip install pandas pypdf
    ```

## Setup

1.  **Clone the repository**.
2.  **Configure Environment**:
    -   Open `send_emails.py`.
    -   Update the `SMTP_` variables with your email credentials (gmail app password recommended).
    ```python
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "your_email@gmail.com"
    SMTP_PASSWORD = "your_app_password"
    ```
3.  **Prepare Data**:
    -   Open `generate_emails.py` and set `YOUR_NAME`, `YOUR_ROLE`, and `VALUE_PROPOSITION` to customize the email generation.
    -   Create a folder named `csvs`.
    -   Create a file `csvs/outreach_companies.csv` based on the `sample.csv` format.
    -   Required columns: `Organisation Name`, `Description`, `Emails`.

## Usage

### 1. Generate Drafts

Run the generation script to create personalized email drafts for each company in your CSV.

```bash
python generate_emails.py
```

This will:
-   Read companies from `csvs/outreach_companies.csv`.
-   Generate a subject and body for each.
-   Save the drafts back to the CSV in new columns (`email_subject`, `email_body`).

### 2. Review Drafts (Optional but Recommended)

Open `csvs/outreach_companies.csv` and review the generated `email_subject` and `email_body` columns. You can manually edit them if needed.

### 3. Send Emails

Run the sending script to dispatch the emails.

```bash
python send_emails.py
```

**Options:**
-   `--dry-run`: Sends emails to YOURSELF (the sender) to test formatting and content.
    ```bash
    python send_emails.py --dry-run
    ```
-   `--retry-fails`: Retries sending to companies that previously failed.

## Notes

-   **Model Selection**: You can change the `MODEL` variable in `generate_emails.py` to use other Ollama models (e.g., `mistral`, `gemma`).
-   **Rate Limiting**: The sending script has built-in delays (30 seconds) to avoid spam filters.
