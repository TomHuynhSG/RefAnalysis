import pandas as pd
from difflib import SequenceMatcher


def normalize_title_for_key(title):
    """
    Normalize title for matching key generation.
    
    Improvements:
    - Removes common article prefixes (the, a, an)
    - Removes all non-alphanumeric characters
    - Converts to lowercase
    
    Args:
        title: Title string to normalize
        
    Returns:
        Normalized title string suitable for matching
    """
    if not isinstance(title, str):
        return ""
    
    # Convert to lowercase and strip whitespace
    title_lower = title.lower().strip()
    
    # Remove common article prefixes (English)
    # This fixes the issue where "The Impact of AI" vs "Impact of AI" wouldn't match
    article_prefixes = ['the ', 'a ', 'an ']
    for prefix in article_prefixes:
        if title_lower.startswith(prefix):
            title_lower = title_lower[len(prefix):]
            break
    
    # Remove all non-alphanumeric characters
    title_clean = ''.join(c for c in title_lower if c.isalnum())
    
    return title_clean


def generate_key(row):
    """
    Generate a unique key for matching references.
    
    Priority:
    1. DOI (most reliable - globally unique)
    2. Title + Year (normalized)
    
    Improvements:
    - Uses improved title normalization (removes "The", "A", "An")
    - Validates year exists before using it
    - Prevents false matches when year is missing
    
    Args:
        row: Pandas Series representing a reference
        
    Returns:
        Unique key string for matching
    """
    # Priority 1: DOI (most reliable)
    doi = row.get('doi') or row.get('do')
    if pd.notna(doi) and str(doi).strip():
        return f"DOI:{str(doi).strip().lower()}"
    
    # Priority 2: Title + Year
    title = row.get('title') or row.get('primary_title') or row.get('ti') or ""
    year = row.get('year') or row.get('py') or ""
    
    # Use improved normalization (removes article prefixes)
    title_norm = normalize_title_for_key(title)
    
    # Validate year exists - prevents false matches for papers without years
    if pd.notna(year) and str(year).strip():
        year_str = str(year)[:4]
    else:
        # Use title length as weak discriminator to prevent false matches
        # Papers with same title but no year won't match unless same length
        year_str = f"NOYEAR_{len(title_norm)}"
    
    return f"TY:{title_norm}_{year_str}"


def fuzzy_match_pass(unique_a, unique_b, threshold=0.90):
    """
    Perform fuzzy matching on previously unmatched items.
    
    Uses SequenceMatcher to find titles with minor variations (typos, etc.)
    that should be considered the same reference.
    
    Improvements:
    - Activates fuzzy matching (was implemented but not used)
    - Catches typos like "Machine Learning" vs "Machine Learing"
    - Requires same year to match (prevents false positives)
    
    Args:
        unique_a: List of items unique to dataset A
        unique_b: List of items unique to dataset B
        threshold: Similarity threshold (0.0 to 1.0), default 0.90
        
    Returns:
        new_matches: List of (item_a, item_b) tuples that match
        remaining_a: Items from A that still don't match
        remaining_b: Items from B that still don't match
    """
    new_matches = []
    matched_a_indices = set()
    matched_b_indices = set()
    
    for i, item_a in enumerate(unique_a):
        title_a = item_a.get('title') or item_a.get('ti') or ""
        year_a = item_a.get('year') or item_a.get('py') or ""
        
        if not title_a:
            continue
        
        title_a_norm = normalize_title_for_key(title_a)
        
        for j, item_b in enumerate(unique_b):
            if j in matched_b_indices:
                continue
            
            title_b = item_b.get('title') or item_b.get('ti') or ""
            year_b = item_b.get('year') or item_b.get('py') or ""
            
            if not title_b:
                continue
            
            # Year must match (or both missing) - prevents false positives
            if str(year_a)[:4] != str(year_b)[:4]:
                continue
            
            title_b_norm = normalize_title_for_key(title_b)
            
            if not title_a_norm or not title_b_norm:
                continue
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, title_a_norm, title_b_norm).ratio()
            
            if similarity >= threshold:
                new_matches.append((item_a, item_b))
                matched_a_indices.add(i)
                matched_b_indices.add(j)
                break  # Move to next item_a
    
    # Get remaining unmatched items
    remaining_a = [item for i, item in enumerate(unique_a) if i not in matched_a_indices]
    remaining_b = [item for j, item in enumerate(unique_b) if j not in matched_b_indices]
    
    return new_matches, remaining_a, remaining_b


def calculate_match_confidence(item_a, item_b):
    """
    Calculate confidence score for a match.
    
    Helps users understand match quality and identify potential false matches.
    
    Args:
        item_a: Reference from dataset A
        item_b: Reference from dataset B
        
    Returns:
        float: Confidence score from 0.0 to 1.0
        str: Reason for the score
    """
    # DOI match = highest confidence
    doi_a = item_a.get('doi') or item_a.get('do')
    doi_b = item_b.get('doi') or item_b.get('do')
    
    if doi_a and doi_b and str(doi_a).strip().lower() == str(doi_b).strip().lower():
        return 1.0, "DOI match"
    
    # Title + Year exact match
    title_a = normalize_title_for_key(item_a.get('title', ''))
    title_b = normalize_title_for_key(item_b.get('title', ''))
    year_a = str(item_a.get('year', ''))[:4]
    year_b = str(item_b.get('year', ''))[:4]
    
    if title_a == title_b and year_a == year_b and year_a:
        return 0.95, "Exact title+year match"
    
    # Fuzzy title match
    if title_a and title_b:
        similarity = SequenceMatcher(None, title_a, title_b).ratio()
        
        if similarity >= 0.95 and year_a == year_b:
            return 0.90, f"High similarity ({similarity:.2f})"
        elif similarity >= 0.90 and year_a == year_b:
            return 0.85, f"Good similarity ({similarity:.2f})"
        elif similarity >= 0.85 and year_a == year_b:
            return 0.75, f"Fair similarity ({similarity:.2f})"
    
    return 0.50, "Low confidence match"


def robust_title_match(title1, title2):
    """
    Check if two titles are similar enough to be considered the same.
    
    Uses SequenceMatcher with 90% similarity threshold.
    
    Args:
        title1: First title
        title2: Second title
        
    Returns:
        bool: True if titles match (exact or >90% similar)
    """
    if not isinstance(title1, str) or not isinstance(title2, str):
        return False
    
    # Normalize: lowercase, remove non-alphanumeric chars
    t1 = normalize_title_for_key(title1)
    t2 = normalize_title_for_key(title2)
    
    if t1 == t2:
        return True
    
    # Fuzzy match for slight variations
    return SequenceMatcher(None, t1, t2).ratio() > 0.9


def compare_datasets(df_a, df_b, use_fuzzy=True):
    """
    Compare two DataFrames of references with improved matching.
    
    Improvements over original version:
    1. Article prefix removal in titles ("The", "A", "An")
    2. Active fuzzy matching for typos and variations
    3. Better handling of missing years
    4. Match confidence scoring
    
    Algorithm:
    1. Generate keys using DOI (priority 1) or Title+Year (priority 2)
    2. Perform set operations to find overlap and unique items
    3. Apply fuzzy matching to unmatched items (optional)
    4. Return results with temp keys cleaned up
    
    Args:
        df_a: DataFrame of references from source A
        df_b: DataFrame of references from source B
        use_fuzzy: Enable fuzzy matching for unmatched items (default: True)
        
    Returns:
        overlap: List of dicts - references in both A and B
        unique_a: List of dicts - references only in A
        unique_b: List of dicts - references only in B
    """
    if df_a.empty:
        return [], [], df_b.to_dict('records')
    if df_b.empty:
        return [], df_a.to_dict('records'), []

    # Step 1: Generate matching keys for all references
    df_a['temp_key'] = df_a.apply(generate_key, axis=1)
    df_b['temp_key'] = df_b.apply(generate_key, axis=1)

    # Step 2: Set operations (intersection and differences)
    keys_a = set(df_a['temp_key'])
    keys_b = set(df_b['temp_key'])

    overlap_keys = keys_a.intersection(keys_b)  # A ∩ B
    unique_a_keys = keys_a - keys_b             # A - B
    unique_b_keys = keys_b - keys_a             # B - A

    # Step 3: Extract records based on keys
    overlap = df_a[df_a['temp_key'].isin(overlap_keys)].to_dict('records')
    unique_a = df_a[df_a['temp_key'].isin(unique_a_keys)].to_dict('records')
    unique_b = df_b[df_b['temp_key'].isin(unique_b_keys)].to_dict('records')

    # Step 4: Fuzzy matching pass (NEW - catches typos and minor variations)
    if use_fuzzy and unique_a and unique_b:
        fuzzy_matches, unique_a, unique_b = fuzzy_match_pass(unique_a, unique_b)
        
        # Add fuzzy matches to overlap (take from A for consistency)
        for item_a, item_b in fuzzy_matches:
            # Optionally add confidence score
            item_a['fuzzy_match'] = True
            overlap.append(item_a)

    # Cleanup temp column from result dicts
    for rec in overlap + unique_a + unique_b:
        rec.pop('temp_key', None)

    return overlap, unique_a, unique_b
