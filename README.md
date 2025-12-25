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
    -   Create a file `sample.csv` (or use the provided one).
    -   Required columns: `Organisation Name`, `Description`, `Emails`.

## User Guide

### 1. Prepare Your Data
The system needs a list of companies to target.
1.  Navigate to the `csvs/` directory.
2.  Create or overwrite `outreach_companies.csv`.
3.  Ensure your CSV has **exactly** these headers:
    -   `Organisation Name`: Name of the company.
    -   `Description`: A sentence or two about what they do (used by AI to personalize).
    -   `Emails`: The contact email address.

    *Example in `sample.csv`*.

### 2. Customize the AI
Make the AI write like YOU.
1.  Open `generate_emails.py`.
2.  Edit the variables at the top:
    -   `YOUR_NAME`: Your full name (e.g., "Jane Doe").
    -   `YOUR_ROLE`: Your target role (e.g., "Full Stack Developer").
    -   `VALUE_PROPOSITION`: Your unique hook (e.g., "specializing in scalable Python backends").
    -   `MODEL`: The Ollama model to use (default: `llama3.1:8b`).

### 3. Generate Drafts
Run the generator to let the AI draft emails for you.
```bash
python generate_emails.py
```
-   **What happens**: The script reads your CSV, calls Ollama for each company, and writes the `email_subject` and `email_body` into new columns in the same CSV.
-   **Resumable**: If you stop the script, running it again will skip companies that already have generated drafts.

### 4. Review & Edit
**Crucial Step**: AI isn't perfect.
1.  Open `sample.csv` in Excel or Numbers.
2.  Read the `email_body` column.
3.  Make any manual edits directly in the CSV if an email sounds off.
4.  Save the CSV.

### 5. Dry Run (Safety Check)
Before sending real emails, send them to yourself to check formatting.
```bash
python send_emails.py --dry-run
```
-   This processes the first 10 companies.
-   It **REPLACES** the recipient with YOUR email (the `SMTP_USER` configured in `send_emails.py`).
-   Check your inbox to ensure the formatting looks professional.

### 6. Send Live Emails
Ready to go?
```bash
python send_emails.py
```
-   **Safety**: Sends 1 email every 30 seconds to avoid spam flags.
-   **Tracking**: Updates the `sent_at` column in your CSV.
-   **Stopping**: Press `Ctrl+C` safely at any time.

### 7. Retry Failures
If the script crashes or network fails:
```bash
python send_emails.py --retry-fails
```
-   This targets only companies marked as `FAILED` in the `sent_at` column.

## Troubleshooting

-   **"Ollama not found"**: Ensure Ollama is running in the background (`ollama serve`).
-   **"Connection Refused"**: Check your internet and SMTP credentials.
-   **"Invalid Email"**: The script automatically skips malformed email addresses and marks them in the CSV.

