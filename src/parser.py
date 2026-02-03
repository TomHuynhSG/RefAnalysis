import pandas as pd
import io

def parse_ris_lines(lines):
    entries = []
    current_entry = {}
    last_tag = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('ER  -'):
            if current_entry:
                entries.append(current_entry)
                current_entry = {}
            last_tag = None
            continue
        
        # Check for standard RIS tag format: "XX  - "
        if len(line) >= 6 and line[2] == ' ' and line[3] == ' ' and line[4] == '-' and line[5] == ' ':
            tag = line[:2]
            value = line[6:].strip()
            
            # Standard mapping (simplified)
            # We keep raw tags too for fallback
            key = tag.lower()
            
            # Handle multiple occurrences (like AU)
            if key in current_entry:
                if isinstance(current_entry[key], list):
                    current_entry[key].append(value)
                else:
                    current_entry[key] = [current_entry[key], value]
            else:
                current_entry[key] = value
                
            # Map common fields for easier usage
            if tag == 'TI' or tag == 'T1':
                current_entry['title'] = value
            elif tag == 'PY' or tag == 'Y1':
                 current_entry['year'] = value
            elif tag == 'AU' or tag == 'A1':
                if 'authors' not in current_entry:
                    current_entry['authors'] = []
                # Ensure authors is strictly a list
                if isinstance(current_entry['authors'], str):
                     current_entry['authors'] = [current_entry['authors']]
                current_entry['authors'].append(value)
            elif tag == 'JO' or tag == 'T2':
                current_entry['journal_name'] = value
            elif tag == 'DO':
                current_entry['doi'] = value
            elif tag == 'TY':
                current_entry['type_of_reference'] = value
            elif tag == 'AB' or tag == 'N2':
                current_entry['abstract'] = value
                
            last_tag = key
        else:
            # Continuation line (rare but possible, or malformed)
            # If we strictly valid RIS, we might ignore, but let's append to last tag if reasonable
            if last_tag and current_entry:
                if isinstance(current_entry[last_tag], list):
                    current_entry[last_tag][-1] += " " + line
                else:
                    current_entry[last_tag] += " " + line

    if current_entry:
        entries.append(current_entry)
        
    return entries

def parse_ris_file(file_stream):
    """
    Parse a RIS file and return a list of dictionaries.
    """
    try:
        if isinstance(file_stream, bytes):
            content = file_stream.decode('utf-8', errors='replace')
        elif isinstance(file_stream, io.StringIO):
             content = file_stream.getvalue()
        else:
            content = str(file_stream) # Fallback if it's already a string
            
        lines = content.splitlines()
        return parse_ris_lines(lines)
    except Exception as e:
        print(f"Error parsing RIS file: {e}")
        return []

def entries_to_df(entries):
    """
    Convert list of RIS entries to a Pandas DataFrame.
    """
    if not entries:
        return pd.DataFrame()
    return pd.DataFrame(entries)
