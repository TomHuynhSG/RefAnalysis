
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exporter import export_to_ris_string

def test_export_nan_handling():
    # Simulate data with NaNs (float)
    records = [
        {
            'type_of_reference': 'JOUR',
            'title': 'Test Title',
            'authors': float('nan'), # This caused the crash
            'year': float('nan'),
            'journal_name': float('nan')
        },
        {
            'type_of_reference': float('nan'), # Should default to JOUR
            'title': float('nan'),
            'authors': ['Valid Author'],
            'year': 2023
        }
    ]
    
    try:
        ris_string = export_to_ris_string(records)
        print("Successfully generated RIS string:")
        print(ris_string)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_export_nan_handling()
