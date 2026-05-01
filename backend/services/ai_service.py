import os
import json
import time
from google import genai
from google.genai import errors
from google.genai import types
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables for standalone testing
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def wait_for_quota(retry_state):
    """Custom tenacity wait function that parses Google's RetryInfo and handles 503s."""
    exception = retry_state.outcome.exception()
    error_str = str(exception)
    
    # Handle 429 Rate Limits
    if "429" in error_str:
        print(f"      [!] Rate limit hit (429). Waiting 35s for quota...")
        return 35
    
    # Handle 503 High Demand / Overloaded
    if "503" in error_str:
        # Increase backoff more aggressively for 503s
        wait_time = wait_exponential(multiplier=2, min=5, max=60)(retry_state)
        print(f"      [!] Model overloaded (503). Retrying in {wait_time:.1f}s...")
        return wait_time
    
    # Default exponential backoff for other errors
    return wait_exponential(multiplier=1.5, min=2, max=30)(retry_state)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_for_quota,
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def call_gemini(prompt: str) -> str:
    """Sends a prompt to Gemini using the new SDK and returns the text response."""
    # Using 3.1-flash-lite-preview based on user quota dashboard (15 RPM / 500 RPD)
    model_name = "gemini-3.1-flash-lite-preview"
    print(f"  --> Calling Gemini API (model: {model_name})...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"      !!! Gemini call failed: {e}")
        raise e

def process_email(sender_name: str, sender_email: str, subject: str, body_snippet: str) -> dict:
    """
    Orchestrates the classification and extraction of an email in a single API call.
    Returns a result dict with a 'status' key: 'skip', 'auto', or 'review'.
    """
    system_instruction = (
        "You are an expert job application assistant. Analyze the email and respond with valid JSON only. "
        "No markdown, no explanation, no backticks.\n\n"
        "1. Classify the email into one of these types:\n"
        "- confirmation: Automated acknowledgment of application\n"
        "- recruiter: Outreach from a human recruiter/hiring manager\n"
        "- interview: Invitation or scheduling for an interview\n"
        "- rejection: Rejection or decline\n"
        "- offer: Job offer\n"
        "- followup: Status check or request for more info\n"
        "- unrelated: Not related to a job application\n\n"
        "2. If it is NOT 'unrelated', extract the application details.\n\n"
        "Respond with this exact JSON structure:\n"
        "{\n"
        "  \"classification\": {\n"
        "    \"type\": \"<one of the types above>\",\n"
        "    \"company\": \"<company name or empty string>\",\n"
        "    \"role\": \"<job title or empty string>\",\n"
        "    \"confidence\": <float 0.0-1.0>,\n"
        "    \"action_needed\": <true or false>,\n"
        "    \"reasoning\": \"<one sentence explaining the classification>\"\n"
        "  },\n"
        "  \"details\": {\n"
        "    \"company\": \"<company name>\",\n"
        "    \"role\": \"<job title>\",\n"
        "    \"ats_platform\": \"<greenhouse, lever, workday, taleo, icims, linkedin, indeed, or unknown>\",\n"
        "    \"application_date\": \"<ISO date string if possible>\",\n"
        "    \"next_action\": \"<specific next step if any>\",\n"
        "    \"interview_date\": \"<ISO datetime string if scheduled>\"\n"
        "  }\n"
        "}"
    )

    user_message = (
        f"From: {sender_name} <{sender_email}>\n"
        f"Subject: {subject}\n"
        f"Body: {body_snippet}"
    )

    full_prompt = f"{system_instruction}\n\n{user_message}"

    try:
        response_text = call_gemini(full_prompt)
        clean_json = response_text.strip().strip("`").replace("json\n", "", 1)
        result = json.loads(clean_json)
        
        # Map to the expected internal structure
        classification = result["classification"]
        details = result.get("details", {})
        
        if classification["type"] == "unrelated":
            return {
                "status": "skip",
                "classification": classification
            }
        
        if classification["confidence"] >= 0.8:
            return {
                "status": "auto",
                "classification": classification,
                "details": details
            }
        
        return {
            "status": "review",
            "classification": classification
        }

    except Exception as e:
        print(f"Error processing Gemini response: {e}")
        return {
            "status": "skip",
            "classification": {
                "type": "unrelated",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
        }

def generate_cover_letter(job_description: str, company: str, role: str, resume_text: str) -> dict:
    """
    Generates a tailored cover letter and gap analysis using Gemini.
    """
    prompt = (
        "You are an expert career coach and professional writer. Write a professional 3-paragraph cover letter "
        f"for a {role} position at {company} tailored to the job description and resume provided below.\n\n"
        "Instructions:\n"
        "- Paragraph 1: Catchy hook and why I am excited about this company specifically.\n"
        "- Paragraph 2: Highlight 2-3 strongest matches between my experience and the job requirements.\n"
        "- Paragraph 3: Closing statement and call to action.\n"
        "- Tone: Professional, confident, and enthusiastic.\n\n"
        "Also identify 'key_matches' (3-5 bullet points of strongest alignment) and 'gaps' (0-3 skills/reqs in the JD not strongly represented in the resume).\n\n"
        "Respond ONLY with valid JSON in this format:\n"
        "{\n"
        "  \"cover_letter\": \"<the full text of the 3 paragraphs>\",\n"
        "  \"key_matches\": [\"match 1\", \"match 2\", ...],\n"
        "  \"gaps\": [\"gap 1\", ...]\n"
        "}\n\n"
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"RESUME:\n{resume_text}"
    )

    try:
        response_text = call_gemini(prompt)
        clean_json = response_text.strip().strip("`").replace("json\n", "", 1)
        return json.loads(clean_json)
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return {
            "cover_letter": "Error generating cover letter. Please try again.",
            "key_matches": [],
            "gaps": [str(e)]
        }

if __name__ == "__main__":
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
    else:
        # Test Data
        test_email = {
            "sender_name": "Workday",
            "sender_email": "no-reply@myworkdayjobs.com",
            "subject": "Application Received - Data Engineer at Wellmark",
            "body_snippet": "Thank you for applying to the Data Engineer position at Wellmark Blue Cross Blue Shield. We have received your application and will be in touch."
        }

        print("Testing classify_email...")
        classification = classify_email(**test_email)
        print(json.dumps(classification, indent=2))

        print("\nTesting extract_application_details...")
        extraction = extract_application_details(**test_email, classification_type=classification["type"])
        print(json.dumps(extraction, indent=2))

        print("\nTesting process_email...")
        processed = process_email(**test_email)
        print(json.dumps(processed, indent=2))
