
def export_to_ris_string(records):
    """
    Converts a list of reference dictionaries back to a RIS formatted string.
    """
    lines = []
    
    for record in records:
        # Default to JOUR if unknown
        rtype = record.get('type_of_reference', 'JOUR')
        if isinstance(rtype, float): rtype = 'JOUR'
        lines.append(f"TY  - {rtype}")
        
        # Title
        title = record.get('title') or record.get('ti') or record.get('primary_title')
        if title and not isinstance(title, float):
            lines.append(f"TI  - {title}")
            
        # Authors
        authors = record.get('authors') or record.get('au') or []
        if isinstance(authors, float):
            authors = []
        if isinstance(authors, str):
            authors = [authors]
            
        if hasattr(authors, '__iter__'):
            for author in authors:
                if author and not isinstance(author, float):
                    lines.append(f"AU  - {author}")
            
        # Year
        year = record.get('year') or record.get('py') or record.get('y1')
        if year and not isinstance(year, float):
            lines.append(f"PY  - {int(year) if isinstance(year, (int, float)) and year == year else year}")
            
        # Journal
        journal = record.get('journal_name') or record.get('jo') or record.get('t2')
        if journal and not isinstance(journal, float):
            lines.append(f"JO  - {journal}")
            
        # DOI
        doi = record.get('doi') or record.get('do')
        if doi and not isinstance(doi, float):
            lines.append(f"DO  - {doi}")
            
        # Abstract
        abstract = record.get('abstract') or record.get('ab') or record.get('n2')
        if abstract and not isinstance(abstract, float):
            lines.append(f"AB  - {abstract}")

        # End Record
        lines.append("ER  - \n")
        
    return "\n".join(lines)
