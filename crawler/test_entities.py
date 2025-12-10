"""
Quick test script for entity extraction.

Usage:
    python crawler/test_entities.py --api-key YOUR_KEY --text "Your content here"
    python crawler/test_entities.py --api-key YOUR_KEY --file path/to/file.txt
    python crawler/test_entities.py --api-key YOUR_KEY --url https://example.com (reads from crawl output)
"""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.entity_extractor import EntityExtractor, extract_entities


def print_entities_table(entities: list, title: str = "Extracted Entities"):
    """Print entities in a formatted table."""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print(f"{'=' * 80}\n")

    if not entities:
        print("No entities found.")
        return

    # Header
    print(f"{'#':<4} {'Entity':<35} {'Type':<15} {'Mentions':>8} {'Delorme %':>10}")
    print("-" * 80)

    # Rows
    for i, e in enumerate(entities, 1):
        entity_name = e['entity'][:33] + '..' if len(e['entity']) > 35 else e['entity']
        print(f"{i:<4} {entity_name:<35} {e['type']:<15} {e['mentions']:>8} {e['delorme_percent']:>9.1f}%")

    print("-" * 80)
    print(f"Total entities: {len(entities)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract entities from text using Google NLP API with Delorme scoring"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="Google Cloud NLP API key"
    )
    parser.add_argument(
        "--text",
        help="Text content to analyze"
    )
    parser.add_argument(
        "--file",
        help="Path to text file to analyze"
    )
    parser.add_argument(
        "--json-file",
        help="Path to crawl output JSON file (uses body_text field)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top entities to return (default: 20)"
    )
    parser.add_argument(
        "--min-salience",
        type=float,
        default=0.0,
        help="Minimum salience threshold 0.0-1.0 (default: 0.0)"
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )

    args = parser.parse_args()

    # Get content from one of the sources
    content = None

    if args.text:
        content = args.text

    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()

    elif args.json_file:
        if not os.path.exists(args.json_file):
            print(f"Error: JSON file not found: {args.json_file}")
            sys.exit(1)
        with open(args.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Prefer main_content (excludes nav/header/footer) over body_text
        content = data.get('main_content') or data.get('body_text', '')
        content_source = 'main_content' if data.get('main_content') else 'body_text'

        if not content:
            print("Error: No content found in JSON file")
            sys.exit(1)
        print(f"Loaded content from: {data.get('url', args.json_file)}")
        print(f"Content source: {content_source}")
        print(f"Word count: {len(content.split())}")

    else:
        print("Error: Provide --text, --file, or --json-file")
        parser.print_help()
        sys.exit(1)

    if not content.strip():
        print("Error: Content is empty")
        sys.exit(1)

    # Extract entities
    print(f"\nAnalyzing content ({len(content)} characters)...")

    try:
        entities = extract_entities(
            content=content,
            api_key=args.api_key,
            top_n=args.top,
            min_salience=args.min_salience
        )
    except Exception as e:
        print(f"Error extracting entities: {e}")
        sys.exit(1)

    # Output results
    if args.output == "json":
        print(json.dumps(entities, indent=2))
    else:
        print_entities_table(entities)


if __name__ == "__main__":
    main()
