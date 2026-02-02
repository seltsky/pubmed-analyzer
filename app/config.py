import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

# PubMed E-utilities base URLs
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Default settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
