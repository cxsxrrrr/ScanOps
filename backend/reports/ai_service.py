"""
AI Service for generating executive summaries.
Uses Google Gemini by default.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_executive_summary(findings_data, url):
    """
    Generate an executive summary using Google Gemini AI.

    Args:
        findings_data: List of finding dicts with title, severity, description, recommendation.
        url: The scanned URL.

    Returns:
        dict with 'content' and 'token_usage'.
    """
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Build the prompt
        findings_text = "\n".join([
            f"- [{f['severity']}] {f['title']}: {f['description']}"
            for f in findings_data
        ])

        prompt = f"""You are a cybersecurity expert writing an executive summary for a non-technical business audience.

Based on the following security scan results for {url}, write a clear, concise executive summary in Spanish.

The summary should include:
1. **Estado General**: An overall risk assessment (Critical/High/Moderate/Low)
2. **Hallazgos Principales**: The most important findings explained simply
3. **Impacto Potencial**: What could happen if these issues are not addressed
4. **Recomendaciones Prioritarias**: Top 3-5 actions to take, ordered by importance
5. **Próximos Pasos**: Suggested timeline for remediation

Scan Results:
{findings_text}

Total findings: {len(findings_data)}
High severity: {sum(1 for f in findings_data if f['severity'] == 'HIGH')}
Medium severity: {sum(1 for f in findings_data if f['severity'] == 'MEDIUM')}
Low severity: {sum(1 for f in findings_data if f['severity'] == 'LOW')}

Write the summary in a professional but accessible tone. Use markdown formatting."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            'content': response.text,
            'token_usage': getattr(response.usage_metadata, 'total_token_count', 0) if response.usage_metadata else 0,
        }

    except Exception as e:
        logger.exception(f"AI summary generation failed: {e}")
        return {
            'content': f'Error generating summary: {str(e)}',
            'token_usage': 0,
        }
