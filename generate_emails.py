
import subprocess
import json
import pandas as pd
from pypdf import PdfReader
import sys
import os
import time
import re

# Configuration
MODEL = "llama3.1:8b"
YOUR_NAME = "[Your Name]"
YOUR_ROLE = "[Your Role]"  # e.g., "Aspiring Product Manager"
VALUE_PROPOSITION = "[Your Unique Value Proposition]" # e.g., "someone who bridges the gap between technical data analysis and business outcomes"
CSV_PATH = "sample.csv"

def unload_model(model):
    """Unloads the model from memory to free up resources."""
    try:
        # Sending keep_alive: 0 to unload the model immediately
        subprocess.run(
            ["curl", "http://localhost:11434/api/generate", "-d", 
             json.dumps({"model": model, "keep_alive": 0})],
            capture_output=True,
            check=False 
        )
        print(f"Unloaded {model}")
    except Exception as e:
        print(f"Failed to unload {model}: {e}")


def generate_email_content(model, company_info):
    company_name = company_info.get('Organisation Name', 'the company')
    description = company_info.get('Description', '')
    
    # Fallback if description is empty
    if pd.isna(description) or description == "":
        description = "No description available."

    prompt = f"""
You are an expert career strategist and professional copywriter specializing in high-conversion cold outreach.

GOAL: Write a highly personalized, authentic networking email to {company_name} on behalf of {YOUR_NAME}, a {YOUR_ROLE}.

CONTEXT:
- Company Name: {company_name}
- Company Description: "{description}"
- Candidate: {YOUR_NAME} ({YOUR_ROLE}).

INSTRUCTIONS:
1. ANALYZE: First, mentally analyze the Company Description to understand their industry, mission, or tech stack.
2. CONNECT: Explain why {YOUR_NAME} would be a good fit for this company based on their industry and mission.
3. DRAFTING RULES:
   - Voice: Professional yet conversational, humble but confident. Avoid "marketing speak", buzzwords, or overly formal language.
   - Subject: Make it short, punchy, and relevant to the company and highlights that a {YOUR_ROLE} is reaching out.
   - Opening: Start with a specific observation about the company (based on the description) to show he's done his research. Do NOT start with "I hope this finds you well".
   - The "Hook": Position {YOUR_NAME} not just as a "{YOUR_ROLE}" but as {VALUE_PROPOSITION}.
   - Call to Action: Ask for a brief chat to learn about their team challenges or for perspective, not a job interview directly. Keep it low pressure.
   - Length: Keep it concise (under 200 words).
   - Address the email to the Hiring Team.
   - Sign off as "Best regards, {YOUR_NAME}"
   - Do not include any other text or formatting.

Format the output strictly as XML so it can be parsed programmatically. Do not include any conversational filler before or after the XML.
<email>
<subject>Short, punchy, relevant subject line</subject>
<body>
Dear Hiring Team,

[Body content...]

Best regards,
{YOUR_NAME}
</body>
</email>

"""
    
    for attempt in range(2):
        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            if output and output.strip():
                return output
            print(f"Attempt {attempt + 1}: Generated output was empty. Retrying...")
        except subprocess.CalledProcessError as e:
            print(f"Error using model {model}: {e.stderr}")
            if attempt == 1:
                return None
        except FileNotFoundError:
            print("Error: 'ollama' command not found.")
            return None
    
    print("Failed to generate non-empty content after retries.")
    return None

def parse_email_output(output_text):
    """Parses email content using XML tags."""
    if not output_text:
        return None, None
        
    # extract subject
    subject_match = re.search(r'<subject>(.*?)</subject>', output_text, re.DOTALL | re.IGNORECASE)
    body_match = re.search(r'<body>(.*?)</body>', output_text, re.DOTALL | re.IGNORECASE)
    
    subject = subject_match.group(1).strip() if subject_match else "(No Subject Detected)"
    body = body_match.group(1).strip() if body_match else output_text.strip()
    
    # Fallback if XML parsing fails completely but some text exists (prevent total data loss)
    # If body is just the raw text because regex failed, try the old 'Subject:' method as backup or just leave it
    if subject == "(No Subject Detected)" and "<email>" not in output_text:
        # Attempt legacy parsing if model ignored XML instructions
        pass # Could implement fallback here, but let's stick to the extracted result

    return subject, body

def main():


    print(f"Loading companies from {CSV_PATH}...")
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Ensure columns exist
    for col in ['email_subject', 'email_body', 'email_raw']:
        if col not in df.columns:
            df[col] = ""
        # Force column to be of type object (string) to avoid FutureWarning
        df[col] = df[col].astype('object')
    
    # Loop through rows
    total_rows = len(df)
    print(f"Processing {total_rows} companies...")
    

    try:
        for index, row in df.iterrows():
            # Check if email already generated
            existing_subject = str(row['email_subject']) if pd.notna(row['email_subject']) else ""
            existing_body = str(row['email_body']) if pd.notna(row['email_body']) else ""
            
            if existing_subject.strip() or existing_body.strip():
                # print(f"Skipping {row['Organisation Name']} (already done)")
                continue
                
            company_name = row['Organisation Name']
            print(f"[{index+1}/{total_rows}] Generating email for: {company_name}")
            
            raw_output = generate_email_content(MODEL, row)
            
            if raw_output:
                # Save raw output first
                df.at[index, 'email_raw'] = raw_output
                
                subject, body = parse_email_output(raw_output)
                
                print(f"\n--- Generated Email for {company_name} ---")
                
                # Update DataFrame
                df.at[index, 'email_subject'] = subject
                df.at[index, 'email_body'] = body
                
                # Save progress immediately (overwriting file)
                # This ensures resumability if script crashes
                df.to_csv(CSV_PATH, index=False)
            else:
                print(f"Failed to generate for {company_name}")

            
            time.sleep(30)
                
    except KeyboardInterrupt:
        print("\nStopping by user request...")
    finally:
        print("Unloading model...")
        unload_model(MODEL)
        print("Done.")

if __name__ == "__main__":
    main()
