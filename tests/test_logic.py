import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_ris_file, entries_to_df
from src.analyzer import analyze_references
from src.comparator import compare_datasets
import pandas as pd

def test_logic():
    print("Testing Logic...")
    
    # Load files
    with open('tests/sample_a.ris', 'r') as f:
        content_a = f.read()
    with open('tests/sample_b.ris', 'r') as f:
        content_b = f.read()
        
    entries_a = parse_ris_file(content_a)
    entries_b = parse_ris_file(content_b)
    
    print(f"Entries A: {len(entries_a)} (Expected 3)")
    print(f"Entries B: {len(entries_b)} (Expected 3)")
    
    df_a = entries_to_df(entries_a)
    df_b = entries_to_df(entries_b)
    
    # Test Comparison
    overlap, unique_a, unique_b = compare_datasets(df_a, df_b)
    
    print("\n--- Comparison Results ---")
    print(f"Overlap: {len(overlap)} (Expected 2: 'AI society' and 'ML healthcare')")
    print(f"Unique A: {len(unique_a)} (Expected 1: 'Ancient History')")
    print(f"Unique B: {len(unique_b)} (Expected 1: 'Quantum Computing')")
    
    for item in overlap:
        print(f"  Overlap Item: {item.get('title') or item.get('ti')}")
        
    for item in unique_a:
        print(f"  Unique A Item: {item.get('title') or item.get('ti')}")
        print(f"  Type: {item.get('type_of_reference', 'UNK')} (Expected 'BOOK')")

    # Test Abstract Parsing (implied if we add abstract to sample)

    # Test Analysis
    stats_a = analyze_references(df_a)
    print("\n--- Analysis Stats A ---")
    print(f"Top Authors: {stats_a['top_authors']}")
    print(f"Years: {stats_a['years_distribution']}")

if __name__ == "__main__":
    test_logic()
