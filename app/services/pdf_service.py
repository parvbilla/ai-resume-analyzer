from __future__ import annotations

import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import pymupdf


logger = logging.getLogger(__name__)


# ============================================================
# PDF ANALYSIS RESULT
# ============================================================

@dataclass
class PDFAnalysis:
    """
    Structured information extracted from a resume PDF.

    This is useful for:
    - ATS analysis
    - Resume quality scoring
    - Debugging
    - Analytics
    - Future dashboard features
    """

    file_name: str
    page_count: int
    text: str

    character_count: int
    word_count: int
    line_count: int

    non_empty_pages: int
    empty_pages: int

    has_text: bool
    is_likely_scanned: bool

    title: str | None
    author: str | None
    subject: str | None

    metadata: dict[str, Any]

    @property
    def average_words_per_page(self) -> float:
        if self.page_count == 0:
            return 0.0

        return round(self.word_count / self.page_count, 2)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["average_words_per_page"] = self.average_words_per_page
        return data


# ============================================================
# PDF SERVICE
# ============================================================

class PDFService:
    """
    Production-grade PDF processing service for ResumeAI.

    Responsibilities:
    - Open PDF safely
    - Extract resume text
    - Clean extracted text
    - Remove repeated headers/footers
    - Analyze document quality
    - Read metadata
    - Detect potentially scanned PDFs
    - Provide structured PDF intelligence
    """

    # Common resume PDF noise
    _MULTIPLE_SPACES = re.compile(r"[ \t]+")
    _MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
    _PAGE_NUMBER = re.compile(
        r"^\s*(?:page\s+)?\d+(?:\s*(?:of|/)\s*\d+)?\s*$",
        re.IGNORECASE,
    )

    # ----------------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------------

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract clean text from a PDF.

        Kept intentionally compatible with the existing route:

            text = PDFService.extract_text(file_path)

        Returns:
            Cleaned resume text.

        Raises:
            FileNotFoundError:
                PDF does not exist.

            ValueError:
                File is invalid, encrypted, or unreadable.

            RuntimeError:
                Unexpected PDF processing failure.
        """

        path = PDFService._validate_path(file_path)

        document = None

        try:
            document = pymupdf.open(path)

            if document.is_encrypted:
                # Try opening with an empty password.
                if not document.authenticate(""):
                    raise ValueError(
                        "The uploaded PDF is password protected and cannot be analyzed."
                    )

            if document.page_count == 0:
                raise ValueError("The PDF contains no pages.")

            pages_text: list[str] = []

            for page_number, page in enumerate(document, start=1):
                try:
                    text = page.get_text("text") or ""

                    cleaned = PDFService._clean_page_text(text)

                    if cleaned:
                        pages_text.append(cleaned)

                except Exception as exc:
                    logger.warning(
                        "Failed to extract page %s from %s: %s",
                        page_number,
                        path.name,
                        exc,
                    )

            if not pages_text:
                raise ValueError(
                    "No readable text was found in this PDF. "
                    "It may be a scanned/image-only resume."
                )

            combined_text = "\n\n".join(pages_text)

            combined_text = PDFService._remove_repeated_headers_footers(
                combined_text
            )

            combined_text = PDFService._normalize_text(combined_text)

            if not combined_text.strip():
                raise ValueError("The PDF contains no usable text.")

            return combined_text

        except ValueError:
            raise

        except Exception as exc:
            logger.exception("PDF extraction failed for %s", path)

            raise RuntimeError(
                "Unable to process the PDF. Please upload a valid, readable resume."
            ) from exc

        finally:
            if document is not None:
                try:
                    document.close()
                except Exception:
                    pass

    # ----------------------------------------------------------------
    # ADVANCED ANALYSIS
    # ----------------------------------------------------------------

    @staticmethod
    def analyze(file_path: str) -> PDFAnalysis:
        """
        Perform complete PDF analysis.

        Useful when the application needs more than plain text.
        """

        path = PDFService._validate_path(file_path)

        document = None

        try:
            document = pymupdf.open(path)

            if document.is_encrypted:
                if not document.authenticate(""):
                    raise ValueError(
                        "The uploaded PDF is password protected."
                    )

            page_count = document.page_count

            if page_count == 0:
                raise ValueError("The PDF contains no pages.")

            raw_pages: list[str] = []
            non_empty_pages = 0

            for page in document:
                text = page.get_text("text") or ""

                cleaned = PDFService._clean_page_text(text)

                raw_pages.append(cleaned)

                if cleaned:
                    non_empty_pages += 1

            empty_pages = page_count - non_empty_pages

            combined_text = "\n\n".join(
                page for page in raw_pages if page
            )

            combined_text = PDFService._remove_repeated_headers_footers(
                combined_text
            )

            combined_text = PDFService._normalize_text(combined_text)

            metadata = document.metadata or {}

            words = PDFService._extract_words(combined_text)

            return PDFAnalysis(
                file_name=path.name,
                page_count=page_count,
                text=combined_text,
                character_count=len(combined_text),
                word_count=len(words),
                line_count=len(
                    [
                        line
                        for line in combined_text.splitlines()
                        if line.strip()
                    ]
                ),
                non_empty_pages=non_empty_pages,
                empty_pages=empty_pages,
                has_text=bool(combined_text.strip()),
                is_likely_scanned=PDFService._is_likely_scanned(
                    combined_text,
                    page_count,
                ),
                title=metadata.get("title") or None,
                author=metadata.get("author") or None,
                subject=metadata.get("subject") or None,
                metadata=metadata,
            )

        except ValueError:
            raise

        except Exception as exc:
            logger.exception("Advanced PDF analysis failed for %s", path)

            raise RuntimeError(
                "Unable to analyze the uploaded PDF."
            ) from exc

        finally:
            if document is not None:
                try:
                    document.close()
                except Exception:
                    pass

    # ----------------------------------------------------------------
    # PDF VALIDATION
    # ----------------------------------------------------------------

    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """
        Quickly determine whether a file can be opened as a PDF.
        """

        try:
            path = PDFService._validate_path(file_path)

            document = pymupdf.open(path)

            try:
                if document.is_encrypted:
                    return document.authenticate("") > 0

                return document.page_count > 0

            finally:
                document.close()

        except Exception:
            return False

    # ----------------------------------------------------------------
    # PAGE EXTRACTION
    # ----------------------------------------------------------------

    @staticmethod
    def extract_pages(file_path: str) -> list[str]:
        """
        Extract cleaned text separately for every page.

        Useful for:
        - Page-level analysis
        - Detecting blank pages
        - Future page quality scoring
        """

        path = PDFService._validate_path(file_path)

        document = None

        try:
            document = pymupdf.open(path)

            if document.is_encrypted:
                if not document.authenticate(""):
                    raise ValueError(
                        "The PDF is password protected."
                    )

            pages: list[str] = []

            for page in document:
                text = page.get_text("text") or ""
                pages.append(PDFService._clean_page_text(text))

            return pages

        except ValueError:
            raise

        except Exception as exc:
            raise RuntimeError(
                "Unable to extract PDF pages."
            ) from exc

        finally:
            if document is not None:
                document.close()

    # ----------------------------------------------------------------
    # METADATA
    # ----------------------------------------------------------------

    @staticmethod
    def get_metadata(file_path: str) -> dict[str, Any]:
        """
        Return PDF metadata without extracting the complete resume.
        """

        path = PDFService._validate_path(file_path)

        document = None

        try:
            document = pymupdf.open(path)

            metadata = document.metadata or {}

            return {
                "file_name": path.name,
                "page_count": document.page_count,
                "metadata": metadata,
            }

        except Exception as exc:
            raise RuntimeError(
                "Unable to read PDF metadata."
            ) from exc

        finally:
            if document is not None:
                document.close()

    # ----------------------------------------------------------------
    # TEXT QUALITY
    # ----------------------------------------------------------------

    @staticmethod
    def text_quality(file_path: str) -> dict[str, Any]:
        """
        Return high-level quality information about extracted PDF text.
        """

        analysis = PDFService.analyze(file_path)

        return {
            "has_text": analysis.has_text,
            "word_count": analysis.word_count,
            "character_count": analysis.character_count,
            "page_count": analysis.page_count,
            "empty_pages": analysis.empty_pages,
            "non_empty_pages": analysis.non_empty_pages,
            "average_words_per_page": analysis.average_words_per_page,
            "is_likely_scanned": analysis.is_likely_scanned,
            "quality": PDFService._calculate_text_quality(
                analysis
            ),
        }

    # ----------------------------------------------------------------
    # PRIVATE HELPERS
    # ----------------------------------------------------------------

    @staticmethod
    def _validate_path(file_path: str) -> Path:
        """
        Validate and normalize the supplied PDF path.
        """

        if not file_path:
            raise ValueError("PDF file path is required.")

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError("The supplied path is not a file.")

        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

        return path

    @classmethod
    def _clean_page_text(cls, text: str) -> str:
        """
        Clean text extracted from a single PDF page.
        """

        if not text:
            return ""

        # Normalize line endings.
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null characters.
        text = text.replace("\x00", "")

        cleaned_lines: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            # Remove standalone page numbers.
            if cls._PAGE_NUMBER.match(line):
                continue

            # Collapse excessive whitespace.
            line = cls._MULTIPLE_SPACES.sub(" ", line)

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """
        Final text normalization for downstream NLP/ATS services.
        """

        if not text:
            return ""

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\x00", "")

        # Normalize non-breaking spaces.
        text = text.replace("\u00a0", " ")

        # Remove excessive spaces.
        text = cls._MULTIPLE_SPACES.sub(" ", text)

        # Remove excessive blank lines.
        text = cls._MULTIPLE_NEWLINES.sub("\n\n", text)

        # Clean spaces immediately around newlines.
        text = re.sub(r" *\n *", "\n", text)

        return text.strip()

    @staticmethod
    def _extract_words(text: str) -> list[str]:
        """
        Extract meaningful word-like tokens.
        """

        if not text:
            return []

        return re.findall(
            r"\b[\w+#.-]+\b",
            text,
            flags=re.UNICODE,
        )

    @classmethod
    def _remove_repeated_headers_footers(
        cls,
        text: str,
    ) -> str:
        """
        Remove lines repeated across multiple pages.

        This prevents repeated:
        - Resume names
        - Website URLs
        - Page labels
        - Headers
        - Footer text

        from artificially inflating ATS keyword counts.
        """

        pages = re.split(r"\n{2,}", text)

        if len(pages) < 2:
            return text

        # This intentionally uses conservative detection.
        # We don't want to accidentally remove legitimate content.
        line_frequency: dict[str, int] = {}

        for page in pages:
            lines = {
                line.strip()
                for line in page.splitlines()
                if line.strip()
            }

            for line in lines:
                normalized = cls._normalize_repeated_line(line)

                if normalized:
                    line_frequency[normalized] = (
                        line_frequency.get(normalized, 0) + 1
                    )

        repeated_lines = {
            line
            for line, count in line_frequency.items()
            if count >= 2
        }

        if not repeated_lines:
            return text

        cleaned_pages: list[str] = []

        for page in pages:
            cleaned_lines = []

            for line in page.splitlines():
                normalized = cls._normalize_repeated_line(line)

                if normalized in repeated_lines:
                    continue

                cleaned_lines.append(line)

            cleaned_pages.append("\n".join(cleaned_lines).strip())

        return "\n\n".join(
            page for page in cleaned_pages if page
        )

    @staticmethod
    def _normalize_repeated_line(line: str) -> str:
        """
        Normalize a line for repeated-header/footer comparison.
        """

        line = line.strip().lower()

        if not line:
            return ""

        line = re.sub(r"\s+", " ", line)

        # Ignore very long paragraphs.
        if len(line) > 120:
            return ""

        return line

    @staticmethod
    def _is_likely_scanned(
        text: str,
        page_count: int,
    ) -> bool:
        """
        Heuristic scanner detection.

        A PDF is considered potentially scanned when:
        - It has pages
        - Very little text was extracted

        This is intentionally a heuristic, not a definitive OCR detector.
        """

        if page_count <= 0:
            return False

        word_count = len(
            re.findall(r"\b\w+\b", text)
        )

        # Less than ~15 words per page is suspicious.
        return word_count < page_count * 15

    @staticmethod
    def _calculate_text_quality(
        analysis: PDFAnalysis,
    ) -> str:
        """
        Classify extracted text quality.
        """

        if analysis.word_count == 0:
            return "poor"

        if analysis.is_likely_scanned:
            return "scanned_or_low_text"

        if analysis.word_count < 80:
            return "low"

        if analysis.word_count < 200:
            return "moderate"

        if analysis.word_count < 1000:
            return "good"

        return "very_high"


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION
# ============================================================

def extract_text(file_path: str) -> str:
    """
    Convenience wrapper.

    Allows future code to use:

        from app.services.pdf_service import extract_text

    while preserving the main PDFService API.
    """

    return PDFService.extract_text(file_path)