"""OpenAI LLM calls for email classification and structured data extraction."""

import json
import logging
import time

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# --- Classification Prompt (GPT-4o-mini) ---

CLASSIFICATION_SYSTEM_PROMPT = """You are an email classifier for a commercial truck and trailer broker.

Classify each email into exactly one category:
- "seller_listing": The email is offering one or more trucks, trailers, or commercial vehicles for sale. This includes inventory lists, individual vehicle listings, price sheets, etc.
- "buyer_request": The email is from someone looking to buy/acquire trucks, trailers, or commercial vehicles. They describe what they want (make, model, year, budget, etc.).
- "irrelevant": The email is not about buying or selling commercial vehicles. This includes newsletters, marketing, personal emails, industry news, etc.

Respond with ONLY one of these three words: seller_listing, buyer_request, irrelevant"""

# --- Seller Extraction Prompt (GPT-4o) ---

SELLER_EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant for a commercial truck and trailer broker.

Extract structured data from the email about vehicles being offered for sale.

For EACH vehicle listed, extract:
- vehicle_type: "truck", "trailer", "tractor", or other vehicle type
- make: manufacturer (e.g., "Freightliner", "Peterbilt", "Kenworth", "Volvo")
- model: model name (e.g., "Cascadia", "579", "T680", "VNL")
- year: model year as integer, or null if not specified
- mileage: odometer reading as integer (no commas), or null
- price: asking price as number (no $ or commas). Use null for "call for pricing" or if not specified
- location: where the vehicle is located. Format as "City, ST" using two-letter state codes when possible
- engine_type: engine make/model (e.g., "Detroit DD15", "Cummins X15", "Paccar MX-13")
- condition: "Excellent", "Good", "Fair", "Poor", or null
- quantity: number of units available (default 1)
- seller_name: name of the seller/company
- seller_contact: email or phone of the seller
- description: brief description of the vehicle

If one email lists multiple vehicles, return one object per vehicle.
If a field is not mentioned, use null."""

SELLER_EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "seller_listings",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "listings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "vehicle_type": {"type": ["string", "null"]},
                            "make": {"type": ["string", "null"]},
                            "model": {"type": ["string", "null"]},
                            "year": {"type": ["integer", "null"]},
                            "mileage": {"type": ["integer", "null"]},
                            "price": {"type": ["number", "null"]},
                            "location": {"type": ["string", "null"]},
                            "engine_type": {"type": ["string", "null"]},
                            "condition": {"type": ["string", "null"]},
                            "quantity": {"type": ["integer", "null"]},
                            "seller_name": {"type": ["string", "null"]},
                            "seller_contact": {"type": ["string", "null"]},
                            "description": {"type": ["string", "null"]},
                        },
                        "required": [
                            "vehicle_type", "make", "model", "year", "mileage",
                            "price", "location", "engine_type", "condition",
                            "quantity", "seller_name", "seller_contact", "description",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["listings"],
            "additionalProperties": False,
        },
    },
}

# --- Buyer Extraction Prompt (GPT-4o) ---

BUYER_EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant for a commercial truck and trailer broker.

Extract structured data from the email about vehicles someone is looking to buy.

For EACH distinct vehicle request, extract:
- vehicle_type: "truck", "trailer", "tractor", or other vehicle type
- make: preferred manufacturer, or null if no preference
- model: preferred model, or null if no preference
- year_min: minimum acceptable model year as integer, or null
- year_max: maximum acceptable model year as integer, or null
- mileage_max: maximum acceptable mileage as integer, or null
- price_min: minimum budget as number, or null
- price_max: maximum budget as number, or null
- location: preferred location. Format as "City, ST" when possible
- engine_type: preferred engine, or null
- buyer_name: name of the buyer/company
- buyer_contact: email or phone of the buyer
- description: what they're looking for in their own words

If one email contains multiple distinct requests (e.g., "looking for a Cascadia AND a reefer trailer"), return one object per request."""

BUYER_EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "buyer_requests",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "requests": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "vehicle_type": {"type": ["string", "null"]},
                            "make": {"type": ["string", "null"]},
                            "model": {"type": ["string", "null"]},
                            "year_min": {"type": ["integer", "null"]},
                            "year_max": {"type": ["integer", "null"]},
                            "mileage_max": {"type": ["integer", "null"]},
                            "price_min": {"type": ["number", "null"]},
                            "price_max": {"type": ["number", "null"]},
                            "location": {"type": ["string", "null"]},
                            "engine_type": {"type": ["string", "null"]},
                            "buyer_name": {"type": ["string", "null"]},
                            "buyer_contact": {"type": ["string", "null"]},
                            "description": {"type": ["string", "null"]},
                        },
                        "required": [
                            "vehicle_type", "make", "model", "year_min", "year_max",
                            "mileage_max", "price_min", "price_max", "location",
                            "engine_type", "buyer_name", "buyer_contact", "description",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["requests"],
            "additionalProperties": False,
        },
    },
}


def classify_email(subject: str, body: str) -> str:
    """Classify an email as seller_listing, buyer_request, or irrelevant."""
    start = time.time()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Subject: {subject}\n\nBody:\n{body}"},
            ],
            max_tokens=20,
        )

        result = response.choices[0].message.content.strip().lower()
        elapsed = time.time() - start
        tokens = response.usage
        logger.info(
            "Classification: %s (%.2fs, %d prompt tokens, %d completion tokens)",
            result, elapsed,
            tokens.prompt_tokens if tokens else 0,
            tokens.completion_tokens if tokens else 0,
        )

        if result in ("seller_listing", "buyer_request", "irrelevant"):
            return result

        logger.warning("Unexpected classification result: %s", result)
        return "irrelevant"

    except Exception:
        logger.exception("Classification failed")
        return "parse_error"


def extract_listings(subject: str, body: str) -> list[dict]:
    """Extract structured listing data from a seller email."""
    start = time.time()
    try:
        # Chunk large emails
        chunks = _chunk_text(body, max_chars=8000)
        all_listings = []

        for chunk in chunks:
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0,
                messages=[
                    {"role": "system", "content": SELLER_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Subject: {subject}\n\nBody:\n{chunk}"},
                ],
                response_format=SELLER_EXTRACTION_SCHEMA,
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            listings = data.get("listings", [])

            tokens = response.usage
            logger.info(
                "Extracted %d listings (%.2fs, %d prompt, %d completion tokens)",
                len(listings), time.time() - start,
                tokens.prompt_tokens if tokens else 0,
                tokens.completion_tokens if tokens else 0,
            )

            for listing in listings:
                # Clean up null quantities to default 1
                if listing.get("quantity") is None:
                    listing["quantity"] = 1
                all_listings.append(listing)

        return all_listings

    except Exception:
        logger.exception("Listing extraction failed")
        return []


def extract_buyer_requests(subject: str, body: str) -> list[dict]:
    """Extract structured buyer request data from a buyer email."""
    start = time.time()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "system", "content": BUYER_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Subject: {subject}\n\nBody:\n{body}"},
            ],
            response_format=BUYER_EXTRACTION_SCHEMA,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        requests = data.get("requests", [])

        elapsed = time.time() - start
        tokens = response.usage
        logger.info(
            "Extracted %d buyer requests (%.2fs, %d prompt, %d completion tokens)",
            len(requests), elapsed,
            tokens.prompt_tokens if tokens else 0,
            tokens.completion_tokens if tokens else 0,
        )

        return requests

    except Exception:
        logger.exception("Buyer extraction failed")
        return []


def extract_from_image(image_path: str, context: str = "") -> list[dict]:
    """Extract listing data from an image using GPT-4o vision."""
    import base64

    start = time.time()
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        suffix = str(image_path).rsplit(".", 1)[-1].lower()
        media_type = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(suffix, "jpeg")

        messages = [
            {"role": "system", "content": SELLER_EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Extract vehicle listing information from this image.\n\nAdditional context: {context}" if context else "Extract vehicle listing information from this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/{media_type};base64,{image_data}"}},
                ],
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=messages,
            response_format=SELLER_EXTRACTION_SCHEMA,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        listings = data.get("listings", [])

        elapsed = time.time() - start
        logger.info("Vision extraction: %d listings (%.2fs)", len(listings), elapsed)
        return listings

    except Exception:
        logger.exception("Vision extraction failed")
        return []


def _chunk_text(text: str, max_chars: int = 8000) -> list[str]:
    """Split text into chunks for processing large multi-vehicle emails."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_len = 0

    for line in lines:
        if current_len + len(line) + 1 > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks
