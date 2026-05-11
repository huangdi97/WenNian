"""Knowledge retrieval module."""

from .rag import LiteratureRetriever, SimpleVectorStore, LITERATURE_ABSTRACTS
from .coagulation_pathway import (
    get_coagulation_pathway, estimate_coagulation_burden, COAGULATION_FACTORS,
)
