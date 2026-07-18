"""
AI service for image classification using OpenAI Vision API.

Integrates with OpenAI's GPT-4 Vision model to classify waste images
and extract waste type, confidence score, and description.
"""

import logging
import os
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
import requests

logger = logging.getLogger(__name__)


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
