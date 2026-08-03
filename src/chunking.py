from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        for index in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[index : index + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()] if current_text.strip() else []
            
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        parts = current_text.split(separator)
        if len(parts) <= 1:
            return self._split(current_text, remaining_separators[1:])

        chunks: list[str] = []
        current_doc: list[str] = []
        total_len = 0

        for part in parts:
            part_str = part.strip()
            if not part_str and separator in ["\n\n", "\n"]:
                continue

            add_len = len(part) + (len(separator) if current_doc else 0)

            # Gom nhóm các phần nhỏ lại cho đến khi đạt chunk_size
            if total_len + add_len <= self.chunk_size:
                current_doc.append(part)
                total_len += add_len
            else:
                if current_doc:
                    joined = separator.join(current_doc).strip()
                    if joined:
                        chunks.append(joined)
                    current_doc = []
                    total_len = 0

                # Nếu phần hiện tại bản thân nó dài hơn chunk_size -> Đệ quy tiếp với separator nhỏ hơn
                if len(part) > self.chunk_size:
                    sub_chunks = self._split(part, remaining_separators[1:])
                    chunks.extend(sub_chunks)
                else:
                    current_doc.append(part)
                    total_len = len(part)

        if current_doc:
            joined = separator.join(current_doc).strip()
            if joined:
                chunks.append(joined)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0)
        sentence = SentenceChunker(max_sentences_per_chunk=2)
        recursive = RecursiveChunker(chunk_size=chunk_size)

        return {
            "fixed_size": {
                "count": len(fixed.chunk(text)),
                "avg_length": sum(len(chunk) for chunk in fixed.chunk(text)) / max(1, len(fixed.chunk(text))),
                "chunks": fixed.chunk(text),
            },
            "by_sentences": {
                "count": len(sentence.chunk(text)),
                "avg_length": sum(len(chunk) for chunk in sentence.chunk(text)) / max(1, len(sentence.chunk(text))),
                "chunks": sentence.chunk(text),
            },
            "recursive": {
                "count": len(recursive.chunk(text)),
                "avg_length": sum(len(chunk) for chunk in recursive.chunk(text)) / max(1, len(recursive.chunk(text))),
                "chunks": recursive.chunk(text),
            },
        }