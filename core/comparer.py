import difflib
import re
import jellyfish
from num2words import num2words
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
    
    def get_match_key(w: str) -> str:
        w_clean = re.sub(r'[^\w\s]', '', w).lower()
        if w_clean.isdigit():
            try:
                # Convert numbers to words (e.g. "50" -> "fifty")
                w_clean = num2words(int(w_clean)).replace("-", "").replace(" ", "")
            except Exception:
                pass
        
        # Use metaphone for homophone matching (e.g. "Cara" -> "KR", "Kara" -> "KR")
        meta = jellyfish.metaphone(w_clean)
        return meta if meta else w_clean
        
    script_clean = [get_match_key(w) for w in script_tokens]
    audio_clean = [get_match_key(w['word']) for w in transcribed_words]
    
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
            # Check if this replace is just a compound word split/merge mismatch
            # by comparing the concatenated clean (Metaphone) versions.
            script_concat = "".join(script_clean[i1:i2])
            audio_concat = "".join(audio_clean[j1:j2])
            
            if script_concat and script_concat == audio_concat:
                # Treat as match
                for idx in range(i1, i2):
                    audio_idx = j1 + min((idx - i1), (j2 - j1 - 1))
                    start_time = transcribed_words[audio_idx]['start'] if (0 <= audio_idx < len(transcribed_words)) else None
                    results.append({
                        'type': 'match',
                        'word': script_tokens[idx],
                        'start': start_time if idx == i1 else None
                    })
            else:
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
                    
    # Forward-fill and backward-fill missing timestamps so skipped words have an approximate location
    last_known_time = 0.0
    for r in results:
        if r['start'] is not None:
            last_known_time = r['start']
        else:
            r['start'] = last_known_time
            
    return results
