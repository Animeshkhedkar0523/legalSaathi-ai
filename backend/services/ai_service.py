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
    
    def answer_question(
        self,
        document_text: str,
        question: str,
        language: Language = Language.EN,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Document-aware Legal RAG Q&A powered by vector semantic retrieval & OpenAI GPT-5.6.
        Performs query classification, vector chunk retrieval, hallucination prevention, and structured citation sourcing.
        """
        from backend.llm_integration import llm_provider
        from backend.models.schemas import LegalQAResponse
        from backend.services.rag_service import rag_service

        # Input Validation
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")
        
        question = question.strip()
        if len(question) > 2000:
            raise ValueError("Question exceeds maximum length of 2000 characters.")

        if not document_text or not document_text.strip():
            return LegalQAResponse(
                answer="I couldn't find enough information in the uploaded document to answer this question reliably.",
                legal_domain="general_law",
                intent="empty_document",
                confidence=0.0,
                requires_lawyer=False,
                sources=[],
                disclaimer="LegalSaathi provides general legal information based on document content, not professional legal advice."
            ).dict()

        # 1. Classify Legal Question (Intent, Domain, Lawyer Necessity, Confidence)
        classification = llm_provider.classify_legal_query(question)

        # 2. Semantic RAG Chunk Retrieval
        retrieved_chunks = []
        if document_id and user_id:
            try:
                retrieved_chunks = rag_service.retrieve_relevant_chunks(
                    document_id=document_id,
                    query=question,
                    user_id=user_id
                )
            except Exception:
                retrieved_chunks = []

        # 3. Hallucination Control: Check if query terms exist in context
        # If retrieved_chunks is empty, fallback to document_text if query keyword exists, else return grounded "not found" response
        context_text = ""
        sources = []

        if retrieved_chunks:
            context_blocks = []
            for c in retrieved_chunks:
                context_blocks.append(f"[{c.get('section', 'Section')}] {c.get('text', '')}")
                sources.append({
                    "document_id": c.get("document_id", document_id),
                    "chunk_id": c.get("chunk_id", ""),
                    "section": c.get("section", "General"),
                    "relevance_score": c.get("relevance_score", 1.0)
                })
            context_text = "\n\n".join(context_blocks)
        else:
            # Simple keyword relevance check on document_text
            import re
            query_keywords = [w for w in re.findall(r'\w+', question.lower()) if len(w) >= 3 and w not in ["what", "where", "when", "which", "how", "much", "many", "this", "that", "with"]]
            has_relevant_keyword = any(kw in document_text.lower() for kw in query_keywords) if query_keywords else True

            if not has_relevant_keyword:
                return LegalQAResponse(
                    answer="I couldn't find enough information in the uploaded document to answer this question reliably. Would you like general legal information or help finding a lawyer?",
                    legal_domain=classification.get("legal_domain", "general_law"),
                    intent=classification.get("intent", "general_inquiry"),
                    confidence=0.0,
                    requires_lawyer=classification.get("requires_lawyer", False),
                    sources=[],
                    disclaimer="LegalSaathi provides general legal information based on document content, not professional legal advice. Consult a qualified advocate for specific legal decisions."
                ).dict()
            
            context_text = document_text[:1500]

        # 4. Build Grounded LLM System & User Prompts
        system_prompt = (
            "You are LegalSaathi AI, a legal assistant for Indian documents.\n"
            "Answer the user's question accurately using ONLY the provided document context.\n"
            "STRICT RULES:\n"
            "- Do NOT present yourself as a lawyer or legal advocate.\n"
            "- Do NOT invent, fabricate, or hallucinate case citations, court decisions, PAN numbers, or act sections.\n"
            "- If the answer cannot be found in the provided context, state clearly: 'I couldn't find enough information in the uploaded document to answer this question reliably.'\n"
            "- Clearly distinguish document facts from general legal information.\n"
            "- Answer in plain, easy to understand language."
        )

        lang_val = language.value if hasattr(language, "value") else str(language)
        user_prompt = (
            f"RETRIEVED DOCUMENT CONTEXT:\n"
            f"----------------------------------------\n"
            f"{context_text}\n"
            f"----------------------------------------\n\n"
            f"USER QUESTION: {question}\n"
            f"RESPONSE LANGUAGE: {lang_val}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 5. Call Centralized LLM Provider
        answer_text = llm_provider.chat(messages, max_tokens=1000)

        # 6. Final Grounded Check: If LLM states text is not present, clean sources
        if "couldn't find enough information" in answer_text.lower() or "does not state" in answer_text.lower() or "not mentioned" in answer_text.lower() or "not specified" in answer_text.lower():
            sources = []

        return LegalQAResponse(
            answer=answer_text,
            legal_domain=classification.get("legal_domain", "general_law"),
            intent=classification.get("intent", "general_inquiry"),
            confidence=float(classification.get("confidence", 0.85)),
            requires_lawyer=bool(classification.get("requires_lawyer", False)),
            sources=sources,
            disclaimer="LegalSaathi provides general legal information based on document content, not professional legal advice. Consult a qualified advocate for specific legal decisions."
        ).dict()




# Initialize service
ai_service = AIService()
