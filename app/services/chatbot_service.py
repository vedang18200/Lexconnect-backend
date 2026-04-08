"""Chatbot service"""
from sqlalchemy.orm import Session


QUICK_QUESTION_CATEGORIES = [
    {"key": "consumer_rights", "title": "Consumer Rights", "subtitle": "Consumer Law"},
    {"key": "property_law", "title": "Property Law", "subtitle": "Property Law"},
    {"key": "criminal_law", "title": "Criminal Law", "subtitle": "Criminal Law"},
    {"key": "family_law", "title": "Family Law", "subtitle": "Family Law"},
    {"key": "employment", "title": "Employment", "subtitle": "Labour Law"},
    {"key": "corporate_law", "title": "Corporate Law", "subtitle": "Corporate Law"},
]

DEFAULT_SUGGESTIONS = [
    "What is a consumer complaint?",
    "How to file a property dispute?",
    "Explain criminal law basics",
    "What are my rights as an employee?",
]

class ChatbotService:
    """Chatbot service for AI interactions"""

    @staticmethod
    def generate_response(user_message: str, language: str = "en") -> str:
        """Generate a chatbot response"""
        text = (user_message or "").strip().lower()

        if "consumer" in text:
            return (
                "Under consumer law, you can seek refund, replacement, or compensation for defective goods "
                "or deficient services. Keep invoices, emails, and screenshots as evidence before filing a complaint."
            )
        if "property" in text:
            return (
                "For property disputes, collect title documents, sale deeds, and mutation records first. "
                "Most cases start with legal notice and then a civil proceeding if settlement fails."
            )
        if "criminal" in text:
            return (
                "In criminal matters, filing an FIR is usually the first step. Preserve digital and physical evidence, "
                "and avoid sharing sensitive case facts publicly before legal consultation."
            )
        if "family" in text:
            return (
                "Family law covers divorce, maintenance, custody, and domestic violence remedies. "
                "Outcomes depend on documents, timelines, and jurisdiction-specific procedure."
            )
        if "employment" in text or "labour" in text:
            return (
                "For employment issues, retain appointment letters, payslips, and termination notices. "
                "Wrongful termination and unpaid dues can be pursued through labour authorities or court, based on facts."
            )
        if "corporate" in text or "company" in text:
            return (
                "Corporate law matters often involve contracts, compliance, governance, and disputes. "
                "Please share whether this is advisory, drafting, or litigation support so the guidance can be narrowed."
            )

        return (
            "I can help with consumer, property, criminal, family, labour, and corporate law basics. "
            "Share your issue in 2-3 lines and I will suggest practical next legal steps."
        )

    @staticmethod
    def process_legal_query(query: str, language: str = "en") -> str:
        """Process legal queries"""
        return ChatbotService.generate_response(query, language)

    @staticmethod
    def get_quick_questions() -> dict:
        """Get static quick-question categories and starter prompts for frontend widgets."""
        return {
            "title": "Quick Questions",
            "categories": QUICK_QUESTION_CATEGORIES,
            "suggestions": DEFAULT_SUGGESTIONS,
            "welcome": (
                "Hello! I'm LexConnect AI, your legal assistant. "
                "I can help you with basic legal information and common legal questions."
            ),
            "disclaimer": "This is general information only. For specific legal advice, consult a qualified lawyer.",
        }

    @staticmethod
    def get_suggestions(context: str | None = None) -> list[str]:
        """Get contextual suggestions for follow-up prompts."""
        if not context:
            return DEFAULT_SUGGESTIONS

        text = context.lower()
        if "consumer" in text:
            return [
                "How do I file a consumer complaint online?",
                "What documents are needed for a consumer case?",
                "Can I claim compensation for delayed delivery?",
            ]
        if "property" in text:
            return [
                "What is the first step in a property dispute?",
                "How long can a civil property case take?",
                "How to verify ownership documents?",
            ]
        if "criminal" in text:
            return [
                "When should I file an FIR?",
                "What evidence is useful in cybercrime cases?",
                "Can police refuse to register an FIR?",
            ]
        return DEFAULT_SUGGESTIONS
