"""
AI Service for generating executive summaries.
Uses Google Gemini by default.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_executive_summary(findings_data, url, config=None):
    """
    Generate an executive summary using the configured AI provider.

    Args:
        findings_data: List of finding dicts with title, severity, description, recommendation.
        url: The scanned URL.
        config: Optional OrganizationLLMConfig object.

    Returns:
        dict with 'content' and 'token_usage'.
    """
    try:
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
5. **Fragmentos de Código de Corrección**: Only if applicable, provide concrete code snippets that could fix the vulnerabilities found. Use the language/framework relevant to each finding. Skip this section if code snippets are not applicable.
6. **Próximos Pasos**: Suggested timeline for remediation

Scan Results:
{findings_text}

Total findings: {len(findings_data)}
High severity: {sum(1 for f in findings_data if f['severity'] == 'HIGH')}
Medium severity: {sum(1 for f in findings_data if f['severity'] == 'MEDIUM')}
Low severity: {sum(1 for f in findings_data if f['severity'] == 'LOW')}

Write the summary in a professional but accessible tone. Use markdown formatting."""

        provider = config.provider if config else 'default'
        api_key = config.api_key if config and config.api_key else settings.GEMINI_API_KEY
        model_name = config.model_name if config and config.model_name else "gemini-2.5-flash"

        if provider == 'openai':
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return {
                'content': response.choices[0].message.content,
                'token_usage': response.usage.total_tokens if response.usage else 0,
            }

        elif provider == 'anthropic':
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return {
                'content': response.content[0].text,
                'token_usage': response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
            }

        elif provider == 'opencode_go':
            # OpenCode Go uses OpenAI compatibility for some models and Anthropic for others.
            # We'll use OpenAI compatibility by default for Go, pointing to their base_url.
            import openai
            client = openai.OpenAI(
                api_key=api_key, 
                base_url="https://opencode.ai/zen/go/v1"
            )
            # Make sure to prepend the opencode-go prefix if not already present, though 
            # usually the user types exactly the model ID shown in docs
            actual_model = model_name.replace('opencode-go/', '')

            response = client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return {
                'content': response.choices[0].message.content,
                'token_usage': response.usage.total_tokens if response.usage else 0,
            }

        else:
            # Default or gemini
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
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
