"""
AI service for image classification using OpenAI Vision API.

Integrates with OpenAI's GPT-4 Vision model to classify waste images
and extract waste type, confidence score, and description.
"""

import base64
import json
import logging
import os
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
import requests

logger = logging.getLogger(__name__)

VALID_WASTE_TYPES = ["bin", "dumping", "construction", "biohazard"]

ANALYZE_PROMPT = (
    "You are a municipal sanitation inspector drafting an official waste complaint "
    "from a citizen's photo. Respond ONLY with a JSON object:\n"
    "{\n"
    '  "waste_type": one of "bin" (overflowing/damaged public bin), "dumping" '
    '(illegal garbage dumping), "construction" (construction debris), '
    '"biohazard" (medical/animal/sewage hazard),\n'
    '  "severity": integer 1-5 (1=minor litter, 3=significant accumulation, '
    "5=urgent public-health hazard),\n"
    '  "severity_reasoning": one sentence justifying the severity,\n'
    '  "confidence": number 0.0-1.0 that the photo shows the stated waste_type,\n'
    '  "title": short complaint title, max 10 words,\n'
    '  "description": 2-4 sentences in formal official-report tone describing what '
    "is visible, its approximate extent, and impact on the area,\n"
    '  "hazards": array of short strings (e.g. "attracts stray animals", '
    '"blocks pedestrian path"), empty if none,\n'
    '  "is_waste_visible": boolean, false if the photo does not show waste\n'
    "}\n"
    "Do not invent details not visible in the photo."
)


def _mock_draft(reason: str) -> Dict:
    """Deterministic offline draft so the flow works without an API key."""
    logger.info(f"AI analyze falling back to mock draft ({reason})")
    return {
        "waste_type": "dumping",
        "severity": 3,
        "severity_reasoning": (
            "A noticeable accumulation of mixed waste is present but does not "
            "pose an immediate public-health emergency."
        ),
        "confidence": 0.55,
        "title": "Accumulated waste requiring municipal attention",
        "description": (
            "An accumulation of mixed household and packaging waste is visible at "
            "the reported location. The waste occupies a portion of the public "
            "space and appears to have been present for some time. Prompt "
            "collection is recommended to prevent further accumulation and "
            "nuisance to residents."
        ),
        "hazards": ["attracts stray animals", "foul odour in the vicinity"],
        "is_waste_visible": True,
        "source": "mock",
    }


def _validate_draft(raw: Dict) -> Dict:
    """Clamp/validate model output into a safe draft dict."""
    waste_type = raw.get("waste_type")
    if waste_type not in VALID_WASTE_TYPES:
        waste_type = None
    try:
        severity = int(raw.get("severity", 3))
    except (TypeError, ValueError):
        severity = 3
    severity = max(1, min(5, severity))
    try:
        confidence = float(raw.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    hazards = raw.get("hazards")
    if not isinstance(hazards, list):
        hazards = []
    return {
        "waste_type": waste_type,
        "severity": severity,
        "severity_reasoning": str(raw.get("severity_reasoning") or ""),
        "confidence": confidence,
        "title": str(raw.get("title") or "Waste issue reported"),
        "description": str(raw.get("description") or ""),
        "hazards": [str(h) for h in hazards][:6],
        "is_waste_visible": bool(raw.get("is_waste_visible", True)),
        "source": "openai",
    }


def analyze_waste_image(image_bytes: bytes) -> Dict:
    """
    Analyze a waste photo with GPT-4o and draft a full official complaint.

    Sends the image as a base64 data URL (LocalStack/S3 URLs are not reachable
    by OpenAI's servers). Never raises — falls back to a deterministic mock
    draft when no API key is configured or on any API/parse failure, so the
    reporting flow always works.

    Returns dict: waste_type, severity, severity_reasoning, confidence, title,
    description, hazards, is_waste_visible, source ("openai" | "mock").
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _mock_draft("OPENAI_API_KEY not configured")

    try:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"},
            "max_tokens": 800,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYZE_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45,
        )
        if response.status_code != 200:
            logger.error(
                f"OpenAI analyze error: {response.status_code} - {response.text[:500]}"
            )
            return _mock_draft(f"API error {response.status_code}")

        content = (
            response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        )
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        draft = _validate_draft(json.loads(content))
        logger.info(
            f"AI draft generated: {draft['waste_type']} severity={draft['severity']} "
            f"confidence={draft['confidence']}"
        )
        return draft

    except Exception as e:
        logger.error(f"AI analyze failed: {str(e)}")
        return _mock_draft(f"exception: {e}")


def classify_image_with_openai(image_url: str) -> Dict:
    """
    Classify waste image using OpenAI Vision API.

    Sends image URL to OpenAI GPT-4 Vision model with prompt to classify
    waste type and extract confidence score and description.

    Args:
        image_url: Full S3 URL of complaint image

    Returns:
        Dictionary with keys:
        - waste_type: One of 'bin', 'dumping', 'construction', 'biohazard', or None
        - confidence: Float between 0-1 indicating classification confidence
        - description: String description of waste/classification result

    Example:
        >>> result = classify_image_with_openai("https://s3.../image.jpg")
        >>> result['waste_type']
        'bin'
        >>> result['confidence']
        0.92
    """
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not configured in environment")
            return {
                "waste_type": None,
                "confidence": 0,
                "description": "OpenAI API key not configured"
            }

        # Prepare request to OpenAI API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Classify this waste image. Provide response in JSON format with:\n"
                                "1. waste_type: One of 'bin', 'dumping', 'construction', 'biohazard'\n"
                                "2. confidence: Float between 0 and 1\n"
                                "3. description: Brief description of what you see\n"
                                "Respond ONLY with valid JSON, no markdown or code blocks."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(
                f"OpenAI API error: {response.status_code} - {response.text}"
            )
            return {
                "waste_type": None,
                "confidence": 0,
                "description": f"API error: {response.status_code}"
            }

        # Parse response
        response_data = response.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        import json
        try:
            classification = json.loads(content)
            waste_type = classification.get("waste_type")
            confidence = float(classification.get("confidence", 0))
            description = classification.get("description", "")

            # Validate waste_type
            valid_types = ["bin", "dumping", "construction", "biohazard"]
            if waste_type not in valid_types:
                waste_type = None

            # Clamp confidence between 0-1
            confidence = max(0, min(1, confidence))

            logger.info(
                f"Image classified: {waste_type} (confidence: {confidence})"
            )

            return {
                "waste_type": waste_type,
                "confidence": confidence,
                "description": description
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return {
                "waste_type": None,
                "confidence": 0,
                "description": "Failed to parse classification response"
            }

    except requests.exceptions.Timeout:
        logger.error("OpenAI API request timed out")
        return {
            "waste_type": None,
            "confidence": 0,
            "description": "API request timeout"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {str(e)}")
        return {
            "waste_type": None,
            "confidence": 0,
            "description": f"Request failed: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in classify_image_with_openai: {str(e)}")
        return {
            "waste_type": None,
            "confidence": 0,
            "description": f"Unexpected error: {str(e)}"
        }


def update_complaint_with_classification(
    db: Session,
    complaint_id: UUID,
    classification: Dict
) -> bool:
    """
    Update complaint record with AI classification results.

    Updates the complaint's ai_waste_type and ai_confidence fields
    with the classification results from OpenAI Vision API.

    Args:
        db: Database session
        complaint_id: UUID of complaint to update
        classification: Dictionary with waste_type, confidence, description

    Returns:
        True if update successful, False otherwise

    Example:
        >>> classification = {"waste_type": "bin", "confidence": 0.92, "description": "..."}
        >>> success = update_complaint_with_classification(db, complaint_id, classification)
        >>> success
        True
    """
    try:
        from backend_models import Complaint

        # Get complaint
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            logger.warning(f"Complaint {complaint_id} not found for AI update")
            return False

        # Update with classification
        complaint.ai_waste_type = classification.get("waste_type")
        complaint.ai_confidence = classification.get("confidence", 0)

        db.commit()
        db.refresh(complaint)

        logger.info(
            f"Complaint {complaint.ticket_number} updated with AI classification: "
            f"{complaint.ai_waste_type} ({complaint.ai_confidence})"
        )
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating complaint with classification: {str(e)}")
        return False
