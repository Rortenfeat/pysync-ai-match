import whisper
import math

class Sync: 
    def __init__(self, model_size="medium"):
        self.model: whisper.Whisper = whisper.load_model(model_size)

    def get_segments(self, vocal_file: str):
        result = self.model.transcribe(vocal_file)
        segments: list[list[str, str]] = []
        for seg in result['segments']:
            time: float = seg['start']
            minute: str = '{:02d}'.format(math.floor(time // 60))
            second: str = '{:02d}'.format(math.floor(time % 60))
            centisecond: str = '{:02d}'.format(int(math.floor(time * 100) % 100))
            formatted_time: str = f"{minute}:{second}.{centisecond}"
            text: str = seg['text']
            segments.append([formatted_time, text])
        print(f"Segments: {segments}")
        return segments

    def jaccard_similarity(self, sent1, sent2):
        """Find text similarity using jaccard similarity"""
        # Tokenize sentences
        token1 = set(sent1.split())
        token2 = set(sent2.split())

        # intersection between tokens of two sentences    
        intersection_tokens = token1.intersection(token2)

        # Union between tokens of two sentences
        union_tokens=token1.union(token2)

        sim_= float(len(intersection_tokens) / len(union_tokens))
        return sim_

    

    def sync_segments(self, lyrics, segments):
        lyrics_synced = []
        lyrics_unsynced = lyrics.split('\n')

        for segment in segments:
            top_similarity = 0.0
            top_similarity_final_index = 1

            for i in range(1, len(lyrics_unsynced)):
                trial_text = ' '.join(lyrics_unsynced[:i])
                trial_similarity = self.jaccard_similarity(trial_text, segment['text'])
                if trial_similarity > top_similarity:
                    top_similarity = trial_similarity
                    top_similarity_final_index = i
            lyrics_synced = lyrics_synced + list(map(lambda x: f"[{math.floor(segment['start']/60):02d}:{math.floor(segment['start'] % 60):02d}.00] {x}\n", lyrics_unsynced[:top_similarity_final_index]))
            lyrics_unsynced = lyrics_unsynced[top_similarity_final_index:]


        lyrics_synced = lyrics_synced + list(map(lambda x: f"[{math.floor(segments[-1]['start']/60):02d}:{math.floor(segments[-1]['start'] % 60):02d}.00] {x}\n", lyrics_unsynced[0:]))

        return lyrics_synced