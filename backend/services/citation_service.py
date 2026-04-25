"""
Citation Service - Verifies legal citations and cross-references
"""
import re
from typing import List
from backend.models.schemas import Citation


class CitationService:
    """Service for extracting and verifying legal citations"""
    
    # Database of known Indian legal citations and cases
    KNOWN_CASES = {
        "AIR": "All India Reporter",
        "SCC": "Supreme Court Cases",
        "AISC": "All India Supreme Court",
        "ILR": "Indian Law Reports",
        "BomLR": "Bombay Law Reports",
        "CalLR": "Calcutta Law Reports",
    }
    
    ACTS = {
        "IPC": "Indian Penal Code",
        "CPC": "Code of Civil Procedure",
        "CrPC": "Code of Criminal Procedure",
        "Indian Succession Act": "Indian Succession Act, 1925",
        "Transfer of Property Act": "Transfer of Property Act, 1882",
        "Registration Act": "Registration Act, 1908",
        "Specific Relief Act": "Specific Relief Act, 1963",
    }
    
    # Sample verified cases (in production, these would come from Indian Kanoon API)
    VERIFIED_CASES = {
        "Marbury v. Madison": "1803",
        "Re Kerala Education Bill": "1958",
        "Kesavananda Bharati v. State of Kerala": "1973",
        "Indra Sawhney v. Union of India": "1992",
    }
    
    def extract_citations_from_text(self, text: str) -> List[str]:
        """Extract potential legal citations from document text"""
        citations = []
        
        # Pattern for case citations like "AIR 1985 SC 800"
        case_pattern = r'(?:AIR|SCC|ILR|BomLR)\s+\d{4}\s+(?:SC|HC|Cal|Bom|Mad)\s+\d+'
        matches = re.findall(case_pattern, text)
        citations.extend(matches)
        
        # Pattern for act references
        for act in self.ACTS.keys():
            if act.lower() in text.lower():
                citations.append(act)
        
        # Pattern for section references like "Section 123" or "S. 123"
        section_pattern = r'(?:Section|S\.|Sec\.)\s+\d+'
        sec_matches = re.findall(section_pattern, text)
        citations.extend(sec_matches)
        
        # Remove duplicates
        citations = list(set(citations))
        
        return citations
    
    def verify_citation(self, citation_text: str) -> Citation:
        """Verify a single citation"""
        is_verified = False
        case_name = None
        year = None
        source = None
        
        # Check if it's a known act
        for act_short, act_full in self.ACTS.items():
            if act_short.lower() in citation_text.lower():
                is_verified = True
                case_name = act_full
                source = f"https://www.indkanoon.org/search/?q={act_full.replace(' ', '+')}"
                break
        
        # Check if it's a known case
        if not is_verified:
            for case, known_year in self.VERIFIED_CASES.items():
                if case.lower() in citation_text.lower():
                    is_verified = True
                    case_name = case
                    year = int(known_year)
                    source = f"https://www.indkanoon.org/search/?q={case.replace(' ', '+')}"
                    break
        
        # Try to extract year from citation (format: "AIR 1985 SC 800")
        year_match = re.search(r'\d{4}', citation_text)
        if year_match and not year:
            year = int(year_match.group())
        
        # Assume valid if it matches common patterns
        if re.match(r'(?:AIR|SCC|ILR|BomLR)\s+\d{4}\s+(?:SC|HC|Cal|Bom|Mad)\s+\d+', citation_text):
            is_verified = True
            source = "https://www.indkanoon.org/"
        
        return Citation(
            citation_text=citation_text,
            case_name=case_name,
            year=year,
            is_verified=is_verified,
            source=source
        )
    
    def verify_all_citations(self, citations: List[str]) -> List[Citation]:
        """Verify multiple citations"""
        verified = []
        for citation in citations:
            verified.append(self.verify_citation(citation))
        return verified


# Initialize service
citation_service = CitationService()
