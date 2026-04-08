import difflib
import re
from typing import List, Dict, Any

def compare(script_text: str, transcribed_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compares the manuscript to the transcribed words.
    Returns a list of dicts reflecting the sequence of words:
      - 'type': 'match', 'skipped', or 'added'
      - 'word': The string word
      - 'start': Float timestamp (if available)
    """
    # Simply split by whitespace to keep the script's visual format as much as possible,
    # but strip out punctuation for the actual sequence matching.
    script_tokens = [w for w in script_text.split() if w.strip()]
    
    def clean_word(w: str) -> str:
        return re.sub(r'[^\w\s]', '', w).lower()
        
    script_clean = [clean_word(w) for w in script_tokens]
    audio_clean = [clean_word(w['word']) for w in transcribed_words]
    
    matcher = difflib.SequenceMatcher(None, script_clean, audio_clean)
    results = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Match
            for idx in range(i1, i2):
                audio_idx = j1 + (idx - i1)
                start_time = transcribed_words[audio_idx]['start'] if audio_idx < len(transcribed_words) else None
                results.append({
                    'type': 'match',
                    'word': script_tokens[idx],
                    'start': start_time
                })
        elif tag == 'delete':
            # Skipped (in script, but not spoken/transcribed)
            for idx in range(i1, i2):
                results.append({
                    'type': 'skipped',
                    'word': script_tokens[idx],
                    'start': None 
                })
        elif tag == 'insert':
            # Added (spoken/transcribed, but not in script)
            for idx in range(j1, j2):
                results.append({
                    'type': 'added',
                    'word': transcribed_words[idx]['word'],
                    'start': transcribed_words[idx]['start']
                })
        elif tag == 'replace':
            # Mismatch. Treat as script word skipped, audio word added.
            for idx in range(i1, i2):
                results.append({
                    'type': 'skipped',
                    'word': script_tokens[idx],
                    'start': None
                })
            for idx in range(j1, j2):
                results.append({
                    'type': 'added',
                    'word': transcribed_words[idx]['word'],
                    'start': transcribed_words[idx]['start']
                })
                
    return results
