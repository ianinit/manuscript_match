from faster_whisper import WhisperModel
from typing import Callable, List, Dict, Any

class Transcriber:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        # To avoid blocking the UI, device="cpu" is safer without knowing CUDA availability.
        # "int8" helps keep memory usage low.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str, progress_callback: Callable[[float], None] = None) -> List[Dict[str, Any]]:
        """
        Transcribes the audio and extracts word-level timestamps.
        progress_callback: A function that takes a float between 0.0 and 1.0
        """
        segments, info = self.model.transcribe(audio_path, word_timestamps=True)
        duration = info.duration
        
        words = []
        for segment in segments:
            # Update progress
            if progress_callback and duration > 0:
                progress = min(segment.end / duration, 1.0)
                progress_callback(progress)
                
            for word in segment.words:
                words.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end
                })
                
        if progress_callback:
            progress_callback(1.0)
            
        return words
