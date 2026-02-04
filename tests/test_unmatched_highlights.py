"""
Test that unmatched references still show highlighting for partial matches
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.search_engine import search_references
import pandas as pd

# Create test data
test_df = pd.DataFrame([
    {
        'title': 'ChatGPT in Medical Education',  # Has ChatGPT but NOT risk assessment
        'abstract': 'This paper discusses ChatGPT applications in medical education.',
        'year': 2024,
        'authors': ['Smith, J.']
    },
    {
        'title': 'Risk Assessment Methods in Clinical Trials',  # Has risk assessment but NOT ChatGPT/LLM
        'abstract': 'Traditional approaches to risk assessment in trials.',
        'year': 2023,
        'authors': ['Doe, A.']
    },
    {
        'title': 'ChatGPT for Risk-of-Bias Assessment',  # Matches BOTH - should be matched
        'abstract': 'Using ChatGPT to automate bias assessment.',
        'year': 2024,
        'authors': ['Jones, B.']
    }
])

# Query requires BOTH ChatGPT/LLM AND risk assessment
query = '("ChatGPT" OR "LLM") AND ("Risk Assessment" OR "Risk-of-Bias")'
fields = ['title', 'abstract']

print("=" * 70)
print("TEST: Partial Match Highlighting in Unmatched References")
print("=" * 70)
print(f"Query: {query}")
print(f"Fields: {fields}\n")

matched, unmatched, stats = search_references(test_df, query, fields)

print(f"Matched: {stats['matched_count']}")
print(f"Unmatched: {stats['unmatched_count']}")
print("\n" + "=" * 70)

print("\nMATCHED REFERENCES:")
for i, ref in enumerate(matched, 1):
    print(f"{i}. {ref['title']}")
    if ref.get('title_highlighted'):
        print(f"   ✓ Title highlighted: Yes")
    if ref.get('abstract_highlighted'):
        print(f"   ✓ Abstract highlighted: Yes")

print("\n" + "=" * 70)
print("UNMATCHED REFERENCES (should still show partial matches):")
for i, ref in enumerate(unmatched, 1):
    print(f"{i}. {ref['title']}")
    if ref.get('title_highlighted'):
        print(f"   ✓ Title highlighted: Yes (partial match)")
    else:
        print(f"   ✗ No title highlighting")
    
    if ref.get('abstract_highlighted'):
        print(f"   ✓ Abstract highlighted: Yes (partial match)")
    else:
        print(f"   ✗ No abstract highlighting")

print("\n" + "=" * 70)
print("EXPECTED:")
print("- Reference 1: Unmatched, but should highlight 'ChatGPT'")
print("- Reference 2: Unmatched, but should highlight 'Risk Assessment'")
print("- Reference 3: Matched, with both highlighted")
print("=" * 70)
