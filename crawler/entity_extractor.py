"""
Entity Extractor with Delorme Scoring

Extracts entities from text using Google NLP API and calculates
Delorme salience scores (salience × mentions) for SEO analysis.

Usage:
    from crawler.entity_extractor import EntityExtractor

    extractor = EntityExtractor(api_key="YOUR_GOOGLE_NLP_API_KEY")
    entities = extractor.extract(text_content)

    # Returns list of entities sorted by Delorme score:
    # [
    #     {"entity": "PYTHON", "type": "OTHER", "salience": 0.45, "mentions": 12,
    #      "delorme_score": 5.4, "delorme_percent": 35.2},
    #     ...
    # ]
"""

import re
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Entity:
    """Represents an extracted entity with Delorme scoring."""
    entity: str
    type: str
    salience: float
    mentions: int
    delorme_score: float
    delorme_percent: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EntityExtractor:
    """
    Extract entities from text using Google NLP API with Delorme scoring.

    Delorme Score = salience × mentions
    This weights entities by both their semantic importance (salience)
    and their frequency (mentions) in the content.
    """

    GOOGLE_NLP_URL = "https://language.googleapis.com/v1/documents:analyzeEntities"

    # Entity types returned by Google NLP API
    ENTITY_TYPES = {
        "UNKNOWN", "PERSON", "LOCATION", "ORGANIZATION", "EVENT",
        "WORK_OF_ART", "CONSUMER_GOOD", "OTHER", "PHONE_NUMBER",
        "ADDRESS", "DATE", "NUMBER", "PRICE"
    }

    def __init__(self, api_key: str):
        """
        Initialize the entity extractor.

        Args:
            api_key: Google Cloud NLP API key
        """
        if not api_key:
            raise ValueError("Google NLP API key is required")
        self.api_key = api_key

    def extract(
        self,
        content: str,
        top_n: Optional[int] = None,
        min_salience: float = 0.0,
        clean_content: bool = True
    ) -> List[Entity]:
        """
        Extract entities from text content.

        Args:
            content: Text content to analyze
            top_n: Return only top N entities (None = all)
            min_salience: Minimum salience threshold (0.0 - 1.0)
            clean_content: Whether to clean URLs and artifacts from content

        Returns:
            List of Entity objects sorted by Delorme score (descending)
        """
        if not content or not content.strip():
            return []

        # Clean content if requested
        if clean_content:
            content = self._clean_content(content)

        # Call Google NLP API
        try:
            raw_entities = self._call_nlp_api(content)
        except Exception as e:
            raise EntityExtractionError(f"Google NLP API error: {e}")

        if not raw_entities:
            return []

        # Aggregate and score entities
        entities = self._aggregate_entities(raw_entities)

        # Filter by minimum salience
        if min_salience > 0:
            entities = [e for e in entities if e.salience >= min_salience]

        # Sort by Delorme score (descending)
        entities.sort(key=lambda e: e.delorme_score, reverse=True)

        # Limit to top N if specified
        if top_n is not None and top_n > 0:
            entities = entities[:top_n]

        return entities

    def extract_as_dict(
        self,
        content: str,
        top_n: Optional[int] = None,
        min_salience: float = 0.0,
        clean_content: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract entities and return as list of dictionaries.

        Convenience method for JSON serialization.
        """
        entities = self.extract(content, top_n, min_salience, clean_content)
        return [e.to_dict() for e in entities]

    def _clean_content(self, content: str) -> str:
        """
        Clean content to remove URLs and artifacts that may be misidentified.

        Removes:
        - HTTP/HTTPS URLs
        - Markdown links (converts [text](url) to just text)
        - Image references
        - Data URIs
        - Blob references
        """
        # Remove URLs
        content = re.sub(r'https?://[^\s\)]+', '', content)

        # Convert markdown links [text](url) to just text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        # Remove markdown images ![alt](url)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # Remove data URIs
        content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', content)

        # Remove blob references
        content = re.sub(r'blob:[^\s]+', '', content)

        # Clean up multiple spaces
        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def _call_nlp_api(self, content: str) -> List[Dict]:
        """Call Google NLP API to analyze entities."""
        url = f"{self.GOOGLE_NLP_URL}?key={self.api_key}"

        headers = {'Content-Type': 'application/json'}
        payload = {
            'document': {
                'type': 'PLAIN_TEXT',
                'content': content,
            },
            'encodingType': 'UTF8',
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            error_detail = response.text[:500] if response.text else "No details"
            raise EntityExtractionError(
                f"API returned status {response.status_code}: {error_detail}"
            )

        result = response.json()
        return result.get('entities', [])

    def _aggregate_entities(self, raw_entities: List[Dict]) -> List[Entity]:
        """
        Aggregate raw API entities and calculate Delorme scores.

        - Groups by (entity_name, type)
        - Sums salience across mentions
        - Counts total mentions
        - Calculates Delorme score and percentage
        """
        # Aggregate by entity name (uppercase) and type
        aggregated = {}

        for entity in raw_entities:
            name = entity.get('name', '').upper()
            entity_type = entity.get('type', 'UNKNOWN')
            salience = entity.get('salience', 0.0)
            mentions = len(entity.get('mentions', []))

            key = (name, entity_type)

            if key in aggregated:
                aggregated[key]['salience'] += salience
                aggregated[key]['mentions'] += mentions
            else:
                aggregated[key] = {
                    'entity': name,
                    'type': entity_type,
                    'salience': salience,
                    'mentions': max(mentions, 1)  # At least 1 mention
                }

        # Calculate Delorme scores
        entities = []
        for data in aggregated.values():
            delorme_score = data['salience'] * data['mentions']
            entities.append(Entity(
                entity=data['entity'],
                type=data['type'],
                salience=round(data['salience'], 4),
                mentions=data['mentions'],
                delorme_score=round(delorme_score, 4),
                delorme_percent=0.0  # Will be calculated below
            ))

        # Calculate Delorme percentages
        total_score = sum(e.delorme_score for e in entities)
        if total_score > 0:
            for entity in entities:
                entity.delorme_percent = round(
                    (entity.delorme_score / total_score) * 100, 2
                )

        return entities


class EntityExtractionError(Exception):
    """Raised when entity extraction fails."""
    pass


# Convenience function for quick extraction
def extract_entities(
    content: str,
    api_key: str,
    top_n: int = 20,
    min_salience: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Quick function to extract entities from content.

    Args:
        content: Text content to analyze
        api_key: Google Cloud NLP API key
        top_n: Number of top entities to return (default: 20)
        min_salience: Minimum salience threshold (default: 0.0)

    Returns:
        List of entity dictionaries sorted by Delorme score

    Example:
        entities = extract_entities(
            content="Python is a programming language...",
            api_key="YOUR_API_KEY",
            top_n=10
        )
        for e in entities:
            print(f"{e['entity']}: {e['delorme_percent']:.1f}%")
    """
    extractor = EntityExtractor(api_key)
    return extractor.extract_as_dict(content, top_n=top_n, min_salience=min_salience)


if __name__ == "__main__":
    # Example usage / test
    import os

    api_key = os.environ.get("GOOGLE_NLP_API_KEY")
    if not api_key:
        print("Set GOOGLE_NLP_API_KEY environment variable to test")
        exit(1)

    sample_text = """
    Python is a high-level programming language created by Guido van Rossum.
    Python is widely used for web development, data science, and machine learning.
    Companies like Google, Netflix, and Instagram use Python extensively.
    The Python Software Foundation manages the development of Python.
    """

    print("Extracting entities from sample text...\n")

    entities = extract_entities(sample_text, api_key, top_n=10)

    print(f"{'Entity':<30} {'Type':<15} {'Salience':>10} {'Mentions':>10} {'Delorme %':>10}")
    print("-" * 80)

    for e in entities:
        print(f"{e['entity']:<30} {e['type']:<15} {e['salience']:>10.4f} {e['mentions']:>10} {e['delorme_percent']:>9.1f}%")
