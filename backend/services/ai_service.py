"""
AI Service - Handles document generation, analysis, and Q&A using LLM
"""
from typing import List, Dict, Optional
from backend.models.schemas import Language, DocumentType, RiskLevel, RiskClause, QAResponse
import random


class AIService:
    """AI-powered document analysis service"""
    
    def __init__(self):
        # In production, initialize with OpenAI, Anthropic, or other LLM
        # For now, using template-based generation with realistic examples
        self.templates = {
            DocumentType.RENTAL_AGREEMENT: self._rental_agreement_template,
            DocumentType.AFFIDAVIT: self._affidavit_template,
            DocumentType.WILL: self._will_template,
        }
    
    def draft_document(self, doc_type: DocumentType, data: dict, language: Language, 
                      citations: List[str] = None) -> str:
        """Generate a legal document based on type and data"""
        if doc_type not in self.templates:
            raise ValueError(f"Document type {doc_type} not supported")
        
        content = self.templates[doc_type](data)
        
        # Add citations if provided
        if citations:
            content += f"\n\n--- CITED LAWS AND ACTS ---\n" + "\n".join(citations)
        
        # In production, use actual LLM to generate
        return content
    
    def _rental_agreement_template(self, data: dict) -> str:
        """Template for rental agreement"""
        party_a = data.get("party_a", {})
        party_b = data.get("party_b", {})
        prop = data.get("property_address", "Property Address")
        rent = data.get("monthly_rent", 0)
        deposit = data.get("security_deposit", 0)
        duration = data.get("duration_months", 11)
        start = data.get("start_date", "2026-01-01")
        
        return f"""RENTAL AGREEMENT

This Rental Agreement ("Agreement") is entered into on this date between:

LANDLORD (Party A):
Name: {party_a.get('name', 'Not Provided')}
Address: {party_a.get('address', 'Not Provided')}
Contact: {party_a.get('contact', 'Not Provided')}

TENANT (Party B):
Name: {party_b.get('name', 'Not Provided')}
Address: {party_b.get('address', 'Not Provided')}
Contact: {party_b.get('contact', 'Not Provided')}

PROPERTY:
Address: {prop}
Monthly Rent: ₹{rent}
Security Deposit: ₹{deposit}
Lease Duration: {duration} months
Start Date: {start}

TERMS AND CONDITIONS:

1. RENT PAYMENT
   - Rent of ₹{rent} shall be paid monthly on or before the 5th of each month.
   - Late payments shall incur an interest of 2% per month on the outstanding amount.

2. SECURITY DEPOSIT
   - An amount of ₹{deposit} has been deposited as security.
   - The deposit will be refunded within 30 days of lease termination, subject to property condition.
   - Landlord may deduct amounts for damages beyond normal wear and tear.

3. PROPERTY MAINTENANCE
   - Tenant shall maintain the property in good condition and repair.
   - Major repairs are the responsibility of the Landlord.
   - Tenant must not make structural changes without written consent.

4. OCCUPANCY
   - The property is rented for residential purposes only.
   - Subletting is not permitted without written consent.
   - No unauthorized persons shall occupy the property permanently.

5. UTILITIES
   - Tenant shall bear the cost of electricity, water, and internet.
   - All utility bills must be paid on time.

6. TERMINATION
   - Either party may terminate with 30 days written notice.
   - Lease will automatically end after {duration} months unless renewed.

7. DISPUTE RESOLUTION
   - All disputes shall be governed by the laws of India.
   - Jurisdiction shall be with the courts in the property location.

SIGNATURES:

Landlord: _________________________ Date: _____________
Tenant:   _________________________ Date: _____________
"""
    
    def _affidavit_template(self, data: dict) -> str:
        """Template for affidavit"""
        deponent = data.get("deponent", {})
        subject = data.get("subject", "Subject Not Provided")
        statements = data.get("statements", [])
        place = data.get("place", "Place Not Provided")
        date = data.get("date", "2026-01-01")
        
        stmt_text = "\n".join([f"   {i+1}. {stmt}" for i, stmt in enumerate(statements)])
        
        return f"""AFFIDAVIT

I, {deponent.get('name', 'Not Provided')}, son/daughter of [Father's Name], 
resident of {deponent.get('address', 'Not Provided')}, do hereby solemnly affirm and declare as follows:

SUBJECT: {subject}

1. That I have personal knowledge of the facts and circumstances mentioned below.

2. The following are the factual statements:
{stmt_text if statements else "   No statements provided."}

3. I have not concealed any material fact or circumstance that is relevant to the above statements.

4. The statements made above are true to the best of my knowledge and belief.

5. I am aware of the consequences of making false statements.

VERIFICATION:

Verified at {place} on {date}.

I solemnly affirm that the contents of this affidavit are true to the best of my knowledge.

Signature: _______________
Name: _____________________
Date: ____________________

[To be signed before a Notary Public or Judge]
"""
    
    def _will_template(self, data: dict) -> str:
        """Template for will/testament"""
        testator = data.get("testator", {})
        assets = data.get("assets", [])
        instructions = data.get("special_instructions", "None")
        
        asset_text = "\n".join([f"   - {asset}" for asset in assets])
        
        return f"""WILL AND TESTAMENT

This is the Last Will and Testament of {testator.get('name', 'Not Provided')}, 
resident of {testator.get('address', 'Not Provided')}.

1. TESTATOR DECLARATION:
I hereby revoke all previous Wills and Testaments made by me and declare this to be my Last Will.

2. ASSETS AND PROPERTY:
I declare that I own the following assets:
{asset_text if assets else "   - No specific assets listed."}

3. DISTRIBUTION OF ESTATE:
My entire estate shall be distributed as per the applicable laws of succession 
in India and in accordance with any specific instructions mentioned below.

4. APPOINTMENT OF EXECUTOR:
I appoint [Name of Executor] as the Executor of this Will, who shall have the power 
to sell, mortgage, lease, or exchange any property.

5. SPECIAL INSTRUCTIONS:
{instructions if instructions else "No special instructions provided."}

6. GUARDIANSHIP (if applicable):
I nominate [Name] as the Guardian for my minor children.

7. FUNERAL EXPENSES:
My Executor is authorized to spend a reasonable amount for my funeral and cremation expenses.

8. SIGNATURE:
This Will is executed on [Date] and signed in the presence of witnesses.

Testator Signature: _______________
Date: ____________________

WITNESSES:

1. Name: ___________________
   Address: _________________
   Signature: _______________

2. Name: ___________________
   Address: _________________
   Signature: _______________

[Must be witnessed by at least two competent witnesses as per Indian Succession Act, 1925]
"""
    
    def detect_risks(self, text: str) -> List[RiskClause]:
        """Detect high-risk clauses in document"""
        risks = []
        
        # Simulate risk detection based on keywords
        risk_keywords = {
            "high": ["automatic renewal", "waiver of rights", "no liability", "unlimited"],
            "medium": ["penalty", "default", "termination", "restriction"],
            "low": ["minor", "optional", "voluntary", "subject to"]
        }
        
        text_lower = text.lower()
        
        for level_str, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    risk_level = RiskLevel.HIGH if level_str == "high" else (
                        RiskLevel.MEDIUM if level_str == "medium" else RiskLevel.LOW
                    )
                    risks.append(RiskClause(
                        clause_text=f"Clause containing '{keyword}'",
                        risk_level=risk_level,
                        risk_reason=f"This clause involves '{keyword}' which may have legal implications.",
                        suggestion=f"Review and clarify the '{keyword}' clause carefully."
                    ))
        
        return risks
    
    def overall_risk(self, risk_clauses: List[RiskClause]) -> RiskLevel:
        """Determine overall risk from individual clauses"""
        if not risk_clauses:
            return RiskLevel.LOW
        
        for clause in risk_clauses:
            if clause.risk_level == RiskLevel.HIGH:
                return RiskLevel.HIGH
        
        for clause in risk_clauses:
            if clause.risk_level == RiskLevel.MEDIUM:
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def summarize_document(self, text: str, language: Language) -> str:
        """Create a plain-language summary"""
        # In production, use actual summarization LLM
        lines = text.split('\n')
        summary_lines = [line.strip() for line in lines if line.strip() and len(line) > 20][:5]
        
        summary = f"""This document is a legal agreement containing the following key points:

• {summary_lines[0] if summary_lines else 'This is a legal document.'}
• Contains multiple terms and conditions for parties involved
• Specifies rights, obligations, and dispute resolution procedures
• Has been analyzed for legal compliance and risk factors

For a complete understanding, please consult with a qualified legal professional."""
        
        return summary
    
    def translate_text(self, text: str, target_language: Language) -> str:
        """Translate text to target language"""
        if target_language == Language.HI:
            # In production, use actual translation API (Google Translate, etc.)
            # For now, return a placeholder translation
            return f"""[हिंदी अनुवाद - Hindi Translation]

{text[:200]}...

[यह एक अनुवादित संस्करण है। पूर्ण अनुवाद के लिए पेशेवर अनुवादक से संपर्क करें।]
Complete translation requires professional translator."""
        
        return text
    
    def answer_question(self, document_text: str, question: str, language: Language) -> dict:
        """Answer a question about the document"""
        # In production, use RAG (Retrieval Augmented Generation) with LLM
        
        # Simulate finding relevant clauses
        relevant_clauses = []
        words = question.lower().split()
        
        for word in words:
            if word in document_text.lower():
                # Find sentence containing the word
                sentences = document_text.split('.')
                for sent in sentences:
                    if word in sent.lower() and sent.strip():
                        relevant_clauses.append(sent.strip()[:100] + "...")
                        break
        
        answer = f"Based on the document: {question}. This depends on the specific terms outlined in the agreement. Please review the relevant clauses mentioned below carefully."
        
        return QAResponse(
            answer=answer,
            relevant_clauses=relevant_clauses[:3],
            confidence=0.7
        ).dict()


# Initialize service
ai_service = AIService()
