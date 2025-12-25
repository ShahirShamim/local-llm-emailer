import pandas as pd
import smtplib
import os
import time
import datetime
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import argparse
import sys



# Configuration
CSV_PATH = "sample.csv"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"

def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    # Ensure columns exist
    for col in ['sent_at']:
        if col not in df.columns:
            df[col] = ""
    return df

def save_data(df):
    df.to_csv(CSV_PATH, index=False)



def send_email(to_email, subject, body, dry_run=False):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))



    if dry_run:
        print(f"[DRY RUN] Sending to {to_email}...")
        print(f"Subject: {subject}")

        print("-" * 20)
        return True

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Send outreach emails.")
    parser.add_argument("--dry-run", action="store_true", help="Send 10 test emails to self immediately.")
    parser.add_argument("--retry-fails", action="store_true", help="Retry sending emails that previously failed.")
    args = parser.parse_args()

    df = load_data()

    if args.dry_run:
        print("Starting DRY RUN mode...")
        
        # Determine which emails to select
        if args.retry_fails:
            print("Mode: Retrying FAILED emails for dry run.")
            sent_mask = df['sent_at'].str.contains("FAILED", na=False)
        else:
            sent_mask = (df['sent_at'].isna() | (df['sent_at'] == ""))

        # Select top 10 unsent/failed with valid subjects
        mask = (df['email_subject'].notna()) & (df['email_subject'] != "") & sent_mask
        candidates = df[mask].head(10)
        
        if candidates.empty:
            print("No emails found to test in this mode.")
            return

        for idx, row in candidates.iterrows():
            print(f"Testing email for company: {row['Organisation Name']}")
            # Override recipient
            recipient = SMTP_USER 
            
            # Clean content for dry run too
            clean_subject = row['email_subject'].strip()
            clean_body = row['email_body'].strip()
            clean_body = "\n".join([line.lstrip() for line in clean_body.splitlines()])

            success = send_email(
                to_email=recipient,
                subject=f"[TEST] {clean_subject}",
                body=clean_body,
                dry_run=False # We actually WANT to send the email to the user, not just print it
            )
            
            if success:
                print("Email sent successfully to user.")
            
            time.sleep(2) # Short pause between test burst
            
        print("Dry run complete. Please check your inbox.")
        return

    # Normal Mode
    print("Starting Normal Execution...")
    if args.retry_fails:
        print("MODE: RETRYING FAILED EMAILS")
    else:
        print("MODE: SENDING NEW EMAILS")
        
    print("Sending emails sequentially with a 30-second interval. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Find next email to send
            if args.retry_fails:
                sent_mask = df['sent_at'].str.contains("FAILED", na=False)
            else:
                sent_mask = (df['sent_at'].isna() | (df['sent_at'] == ""))

            target_mask = (
                (df['email_subject'].notna()) & 
                (df['email_subject'] != "") & 
                sent_mask
            )
            
            # Get index of the first target row
            next_idx = df[target_mask].first_valid_index()
            
            if next_idx is None:
                print("All emails have been sent!")
                break
            
            # Get row data
            row = df.loc[next_idx]
            company = row['Organisation Name']
            recipient = row['Emails']
            
            # Validate/Clean Email
            if not isinstance(recipient, str) or not recipient.strip():
                 print(f"Skipping {company}: Invalid or missing email")
                 continue
            
            valid_email = recipient.strip()

            print(f"Sending email to {company} ({valid_email})...")

            # Clean the content
            clean_subject = row['email_subject'].strip()
            clean_body = row['email_body'].strip()
            clean_body = "\n".join([line.lstrip() for line in clean_body.splitlines()])
            
            success = send_email(
                to_email=valid_email,
                subject=clean_subject,
                body=clean_body
            )
            
            if success:
                print(f"SENT to {company}")
                df.at[next_idx, 'sent_at'] = datetime.datetime.now().isoformat()
                save_data(df)
                
                print("Sleeping for 30 seconds...")
                time.sleep(1)
            else:
                 print(f"Failed to send to {company}.")
                 # Mark as failed so we don't get stuck in an infinite loop on this one
                 # We update the timestamp so we know it failed again recently
                 df.at[next_idx, 'sent_at'] = f"FAILED_{datetime.datetime.now().isoformat()}"
                 save_data(df)
                 # Proceed immediately (or minimal sleep)
                 time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping by user request...")

if __name__ == "__main__":
    main()
