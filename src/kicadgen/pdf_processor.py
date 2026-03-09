"""PDF processing: page selection and image rendering."""

import fitz  # PyMuPDF


def select_relevant_pages(doc: fitz.Document, keywords: list[str]) -> list[int]:
    """
    Select pages from PDF that contain relevant keywords.

    Scores pages by keyword frequency and returns indices of top-scoring pages.

    Args:
        doc: PyMuPDF Document object
        keywords: List of keywords to search for (e.g., "Recommended Land Pattern")

    Returns:
        List of page indices (0-based) sorted by relevance
    """
    page_scores = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text()
        score = sum(text.count(keyword) for keyword in keywords)
        if score > 0:
            page_scores.append((page_idx, score))

    # Sort by score descending
    page_scores.sort(key=lambda x: x[1], reverse=True)

    # Return top pages (at least the top 1, up to 3 most relevant)
    return [idx for idx, _ in page_scores[:3]] if page_scores else []


def render_pages_to_png(
    doc: fitz.Document, page_indices: list[int], dpi: int = 300
) -> list[bytes]:
    """
    Render selected pages to PNG images.

    Args:
        doc: PyMuPDF Document object
        page_indices: List of page indices to render
        dpi: Resolution in DPI (default 300)

    Returns:
        List of PNG image bytes
    """
    images = []
    zoom = dpi / 72  # Convert DPI to zoom factor (default 72 DPI in PyMuPDF)

    for page_idx in page_indices:
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        images.append(pix.tobytes("png"))

    return images
