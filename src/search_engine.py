"""
Search Engine for RIS References

Executes Boolean search queries against reference datasets with field selection,
wildcard matching, and term highlighting.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Tuple, Set
from src.query_parser import ASTNode, TermNode, OperatorNode, parse_query


def wildcard_to_regex(term: str) -> str:
    """
    Convert wildcard term to regex pattern.
    
    Wildcards:
    - * matches zero or more word characters (non-greedy)
    - Case insensitive
    
    Args:
        term: Term with optional wildcards (e.g., "GPT*", "*model", "assess*")
        
    Returns:
        Regex pattern string
    """
    # Escape special regex characters except *
    escaped = re.escape(term)
    # Replace escaped \* with non-greedy word character match
    # Use \w* instead of .* to match word characters only
    pattern = escaped.replace(r'\*', r'\w*')
    return pattern


def match_term(term: str, text: str, is_phrase: bool = False) -> Tuple[bool, List[str]]:
    """
    Match a term against text with wildcard support.
    
    Args:
        term: Search term (may contain wildcards)
        text: Text to search in
        is_phrase: If True, match exact phrase (but wildcards still work)
        
    Returns:
        (matched: bool, matched_strings: List[str])
    """
    if not text or pd.isna(text):
        return False, []
    
    text_str = str(text)
    
    # Check if term contains wildcards
    has_wildcard = '*' in term
    
    # For both phrases and terms, handle wildcards the same way
    if has_wildcard:
        # Convert wildcard to regex pattern
        pattern = wildcard_to_regex(term)
        # Add word boundaries to prevent partial word matches
        # Use \b at start/end unless the wildcard is at that position
        if not term.startswith('*'):
            pattern = r'\b' + pattern
        if not term.endswith('*'):
            pattern = pattern + r'\b'
        
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(text_str)
        return len(matches) > 0, matches
    elif is_phrase:
        # Exact phrase match without wildcards (case insensitive)
        # Use word boundaries for phrases too
        pattern = r'\b' + re.escape(term) + r'\b'
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(text_str)
        return len(matches) > 0, matches
    else:
        # Regular term with word boundaries
        pattern = r'\b' + re.escape(term) + r'\b'
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(text_str)
        return len(matches) > 0, matches






def evaluate_ast(node: ASTNode, reference: Dict[str, Any], fields: List[str]) -> Tuple[bool, Dict[str, Set[str]]]:
    """
    Evaluate AST against a reference with field-specific match tracking.
    
    Args:
        node: AST node to evaluate
        reference: Reference dictionary
        fields: List of fields to search in (e.g., ['title', 'abstract'])
        
    Returns:
        (matched: bool, field_matches: Dict[field_name -> Set[matched_terms]])
        field_matches contains ALL matches found, even if the boolean result is False
    """
    if isinstance(node, TermNode):
        # Leaf node - check if term matches in any selected field
        field_matches = {}
        
        for field in fields:
            # Map field names to possible column names
            field_columns = {
                'title': ['title', 'ti', 'primary_title'],
                'abstract': ['abstract', 'ab', 'n2'],
                'keywords': ['keywords', 'kw'],
                'journal': ['journal_name', 'jo', 't2'],
                'authors': ['authors', 'au', 'a1']
            }
            
            possible_cols = field_columns.get(field, [field])
            matched_terms = set()
            
            for col in possible_cols:
                if col in reference:
                    field_value = reference[col]
                    matched, matches = match_term(node.term, field_value, node.is_phrase)
                    
                    if matched:
                        # Track which actual strings were matched in THIS field
                        matched_terms.update(matches)
            
            if matched_terms:
                field_matches[field] = matched_terms
        
        # Return True if ANY field matched
        return len(field_matches) > 0, field_matches
    
    elif isinstance(node, OperatorNode):
        left_match, left_field_matches = evaluate_ast(node.left, reference, fields)
        right_match, right_field_matches = evaluate_ast(node.right, reference, fields)
        
        # Always merge ALL matches from both sides, regardless of boolean result
        combined_matches = {}
        for field in set(left_field_matches.keys()) | set(right_field_matches.keys()):
            combined_matches[field] = left_field_matches.get(field, set()) | right_field_matches.get(field, set())
        
        if node.operator == 'AND':
            # Both must match for boolean result to be True
            # But we still return all partial matches
            return (left_match and right_match), combined_matches
        
        elif node.operator == 'OR':
            # Either can match for boolean result to be True
            # And we return all partial matches
            return (left_match or right_match), combined_matches
    
    return False, {}




def highlight_text(text: str, matched_terms: Set[str]) -> str:
    """
    Highlight matched terms in text using HTML <mark> tags.
    
    Maximizes the number of distinct highlighted matches by selecting
    the combination of non-overlapping matches that gives the most highlights.
    
    Args:
        text: Original text
        matched_terms: Set of terms that were matched
        
    Returns:
        HTML string with highlighted terms
    """
    if not text or pd.isna(text) or not matched_terms:
        return str(text) if not pd.isna(text) else ""
    
    text_str = str(text)
    
    # Find all match positions with their terms
    matches = []
    for term in matched_terms:
        if not term:
            continue
        
        # Find all occurrences of this term (case insensitive)
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        for match in pattern.finditer(text_str):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'term': match.group(),  # Use actual matched text (preserves case)
                'length': match.end() - match.start()
            })
    
    if not matches:
        return text_str
    
    # Sort by start position, then by length (shorter first to maximize count)
    # Shorter matches allow more room for other matches
    matches.sort(key=lambda m: (m['start'], m['length']))
    
    # Track which positions are already highlighted
    highlighted_positions = set()
    selected_matches = []
    
    # Greedy algorithm: select matches that don't overlap, prioritizing:
    # 1. Earlier position (left to right)
    # 2. Shorter length (to leave room for more matches)
    for match in matches:
        positions = set(range(match['start'], match['end']))
        # Check if this match overlaps with any already selected
        if not positions.intersection(highlighted_positions):
            selected_matches.append(match)
            highlighted_positions.update(positions)
    
    # Sort selected matches by position for proper insertion
    selected_matches.sort(key=lambda m: m['start'])
    
    # Build highlighted string by inserting <mark> tags
    result = []
    last_pos = 0
    
    for match in selected_matches:
        # Add text before this match
        result.append(text_str[last_pos:match['start']])
        # Add highlighted match
        result.append(f"<mark>{match['term']}</mark>")
        last_pos = match['end']
    
    # Add remaining text
    result.append(text_str[last_pos:])
    
    return ''.join(result)



def search_references(
    df: pd.DataFrame,
    query: str,
    fields: List[str]
) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
    """
    Search references using Boolean query.
    
    Args:
        df: DataFrame of references
        query: Boolean search query string
        fields: List of fields to search in (e.g., ['title', 'abstract'])
        
    Returns:
        (matched_refs, unmatched_refs, stats)
    """
    if df.empty:
        return [], [], {
            'total_refs': 0,
            'matched_count': 0,
            'unmatched_count': 0,
            'match_percentage': 0.0,
            'query': query,
            'fields': fields,
            'error': None
        }
    
    # Parse query
    try:
        ast = parse_query(query)
    except Exception as e:
        return [], [], {
            'total_refs': len(df),
            'matched_count': 0,
            'unmatched_count': len(df),
            'match_percentage': 0.0,
            'query': query,
            'fields': fields,
            'error': str(e)
        }
    
    # Evaluate each reference
    matched_refs = []
    unmatched_refs = []
    
    for idx, row in df.iterrows():
        reference = row.to_dict()
        
        # Evaluate AST - now returns field-specific matches
        is_match, field_matches = evaluate_ast(ast, reference, fields)
        
        if is_match:
            # Add highlighting for matched fields
            ref_copy = reference.copy()
            
            # Highlight title if it's a search field AND it has matches
            if 'title' in field_matches:
                for col in ['title', 'ti', 'primary_title']:
                    if col in ref_copy and ref_copy[col]:
                        ref_copy[f'{col}_highlighted'] = highlight_text(ref_copy[col], field_matches['title'])
            
            # Highlight abstract if it's a search field AND it has matches
            if 'abstract' in field_matches:
                for col in ['abstract', 'ab', 'n2']:
                    if col in ref_copy and ref_copy[col]:
                        ref_copy[f'{col}_highlighted'] = highlight_text(ref_copy[col], field_matches['abstract'])
            
            # Collect all matched terms from all fields for display
            # Use list instead of set to count all occurrences
            all_matched_terms = []
            for field_terms in field_matches.values():
                all_matched_terms.extend(field_terms)
            
            ref_copy['matched_terms'] = all_matched_terms  # Now includes duplicates
            ref_copy['match_count'] = len(all_matched_terms)  # Total occurrences
            matched_refs.append(ref_copy)
        else:
            # Even for unmatched, apply highlighting for any partial matches
            ref_copy = reference.copy()
            
            # Highlight title if there were any title matches (even if query failed overall)
            if 'title' in field_matches:
                for col in ['title', 'ti', 'primary_title']:
                    if col in ref_copy and ref_copy[col]:
                        ref_copy[f'{col}_highlighted'] = highlight_text(ref_copy[col], field_matches['title'])
            
            # Highlight abstract if there were any abstract matches
            if 'abstract' in field_matches:
                for col in ['abstract', 'ab', 'n2']:
                    if col in ref_copy and ref_copy[col]:
                        ref_copy[f'{col}_highlighted'] = highlight_text(ref_copy[col], field_matches['abstract'])
            
            unmatched_refs.append(ref_copy)

    
    # Calculate statistics
    total = len(df)
    matched_count = len(matched_refs)
    unmatched_count = len(unmatched_refs)
    match_percentage = (matched_count / total * 100) if total > 0 else 0.0
    
    stats = {
        'total_refs': total,
        'matched_count': matched_count,
        'unmatched_count': unmatched_count,
        'match_percentage': round(match_percentage, 2),
        'query': query,
        'fields': fields,
        'error': None
    }
    
    return matched_refs, unmatched_refs, stats


# Example usage and testing
if __name__ == "__main__":
    # Test data
    test_refs = pd.DataFrame([
        {
            'title': 'Large Language Models for Medical Diagnosis',
            'abstract': 'We present a study on GPT-4 for risk assessment in clinical trials.',
            'year': 2024,
            'authors': ['Smith, J.', 'Doe, A.']
        },
        {
            'title': 'Transformer Architecture Review',
            'abstract': 'A comprehensive review of transformer models and their applications.',
            'year': 2023,
            'authors': ['Johnson, M.']
        },
        {
            'title': 'Traditional Machine Learning Methods',
            'abstract': 'Classical approaches to classification and regression.',
            'year': 2020,
            'authors': ['Lee, K.']
        }
    ])
    
    # Test query
    query = '("Large Language Model*" OR "GPT*" OR "Transformer*") AND "risk assessment"'
    fields = ['title', 'abstract']
    
    matched, unmatched, stats = search_references(test_refs, query, fields)
    
    print(f"Query: {query}")
    print(f"Stats: {stats}")
    print(f"\nMatched: {len(matched)}")
    for ref in matched:
        print(f"  - {ref.get('title', 'N/A')}")
        print(f"    Matched terms: {ref.get('matched_terms', [])}")
    
    print(f"\nUnmatched: {len(unmatched)}")
    for ref in unmatched:
        print(f"  - {ref.get('title', 'N/A')}")
