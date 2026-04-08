import shutil
from pathlib import Path
from pypdf import PdfReader

def check_ffmpeg() -> bool:
    """Verifies that ffmpeg is available in the system PATH."""
    return shutil.which("ffmpeg") is not None

def parse_manuscript(filepath: str) -> str:
    """Reads the manuscript text from a file (.txt or .pdf)."""
    path = Path(filepath)
    if not path.exists():
        return ""
        
    if path.suffix.lower() == ".pdf":
        text = ""
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Error reading PDF {filepath}: {e}")
        return text
    else:
        # Default fallback is treating it as plaintext
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading Text {filepath}: {e}")
            return ""
