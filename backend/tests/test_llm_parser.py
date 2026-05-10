"""Tests for LLM parser — classification and extraction with mocked OpenAI."""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_openai():
    with patch("src.services.llm_parser.client") as mock_client:
        yield mock_client


def _make_response(content, prompt_tokens=100, completion_tokens=20):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.prompt_tokens = prompt_tokens
    response.usage.completion_tokens = completion_tokens
    return response


class TestClassifyEmail:
    def test_seller_listing(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_response("seller_listing")
        from src.services.llm_parser import classify_email

        result = classify_email("Trucks for sale", "We have 5 Cascadias available...")
        assert result == "seller_listing"

    def test_buyer_request(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_response("buyer_request")
        from src.services.llm_parser import classify_email

        result = classify_email("Looking for trucks", "Need 2020+ Cascadia...")
        assert result == "buyer_request"

    def test_irrelevant(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_response("irrelevant")
        from src.services.llm_parser import classify_email

        result = classify_email("Newsletter", "Weekly trucking news...")
        assert result == "irrelevant"

    def test_unexpected_response_defaults_to_irrelevant(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _make_response("unknown_category")
        from src.services.llm_parser import classify_email

        result = classify_email("Test", "Test body")
        assert result == "irrelevant"

    def test_api_error_returns_parse_error(self, mock_openai):
        mock_openai.chat.completions.create.side_effect = Exception("API error")
        from src.services.llm_parser import classify_email

        result = classify_email("Test", "Test body")
        assert result == "parse_error"


class TestExtractListings:
    def test_single_listing(self, mock_openai):
        response_data = json.dumps({
            "listings": [{
                "vehicle_type": "truck",
                "make": "Freightliner",
                "model": "Cascadia",
                "year": 2022,
                "mileage": 350000,
                "price": 65000,
                "location": "Dallas, TX",
                "engine_type": "Detroit DD15",
                "condition": "Good",
                "quantity": 1,
                "seller_name": "Big Rig Sales",
                "seller_contact": "seller@test.com",
                "description": "2022 Cascadia, 350k miles",
            }]
        })
        mock_openai.chat.completions.create.return_value = _make_response(response_data)

        from src.services.llm_parser import extract_listings

        result = extract_listings("Test Subject", "Test body")
        assert len(result) == 1
        assert result[0]["make"] == "Freightliner"
        assert result[0]["price"] == 65000

    def test_multiple_listings(self, mock_openai):
        response_data = json.dumps({
            "listings": [
                {"vehicle_type": "truck", "make": "Freightliner", "model": "Cascadia",
                 "year": 2022, "mileage": 350000, "price": 65000, "location": "Dallas, TX",
                 "engine_type": "DD15", "condition": "Good", "quantity": 1,
                 "seller_name": "Test", "seller_contact": "t@t.com", "description": "Truck 1"},
                {"vehicle_type": "truck", "make": "Peterbilt", "model": "579",
                 "year": 2021, "mileage": 400000, "price": 55000, "location": "Houston, TX",
                 "engine_type": "X15", "condition": "Good", "quantity": 1,
                 "seller_name": "Test", "seller_contact": "t@t.com", "description": "Truck 2"},
            ]
        })
        mock_openai.chat.completions.create.return_value = _make_response(response_data)

        from src.services.llm_parser import extract_listings

        result = extract_listings("Multiple trucks", "Two trucks for sale")
        assert len(result) == 2

    def test_api_error_returns_empty(self, mock_openai):
        mock_openai.chat.completions.create.side_effect = Exception("API error")
        from src.services.llm_parser import extract_listings

        result = extract_listings("Test", "Test")
        assert result == []


class TestExtractBuyerRequests:
    def test_single_buyer(self, mock_openai):
        response_data = json.dumps({
            "requests": [{
                "vehicle_type": "truck",
                "make": "Freightliner",
                "model": "Cascadia",
                "year_min": 2020,
                "year_max": 2025,
                "mileage_max": 500000,
                "price_min": 40000,
                "price_max": 70000,
                "location": "Dallas, TX",
                "engine_type": None,
                "buyer_name": "Smith Logistics",
                "buyer_contact": "buyer@test.com",
                "description": "Looking for Cascadias",
            }]
        })
        mock_openai.chat.completions.create.return_value = _make_response(response_data)

        from src.services.llm_parser import extract_buyer_requests

        result = extract_buyer_requests("Looking for trucks", "Need Cascadias")
        assert len(result) == 1
        assert result[0]["make"] == "Freightliner"
        assert result[0]["price_max"] == 70000
