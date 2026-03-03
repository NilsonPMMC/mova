"""
Roteamento automático (Auto-Dispatch) baseado na confiança da IA.

Regra de ouro: se urgência < 5, categoria válida com setor padrão e confiança aceitável,
a manifestação é encaminhada automaticamente. Caso contrário, permanece em triagem manual.
"""
import logging
from reports.models import Manifestation, ManifestationUpdate

logger = logging.getLogger(__name__)

# Slug considerado genérico: sempre triagem manual
GENERIC_CATEGORY_SLUGS = ('outros', 'outras', 'geral')


def _confidence_ok(nlp_analysis) -> bool:
    """
    Confiança aceitável para auto-dispatch.
    Se a API da LLM retornar probabilidade no raw_ai_response, usar; senão
    assumir confiança quando a IA definiu categoria e não é "Outros".
    """
    raw = getattr(nlp_analysis, 'raw_ai_response', None) or {}
    parsed = raw.get('parsed_json') or raw.get('full_response') or {}
    prob = parsed.get('confidence') or parsed.get('probability')
    if prob is not None:
        try:
            return float(prob) >= 0.7
        except (TypeError, ValueError):
            pass
    # Heurística: categoria definida e não genérica
    cat = nlp_analysis.suggested_category
    if not cat:
        return False
    slug = (getattr(cat, 'slug', None) or '').strip().lower()
    return slug not in GENERIC_CATEGORY_SLUGS


def route_manifestation(manifestation):
    """
    Aplica a regra de auto-dispatch: se condições forem atendidas, encaminha
    automaticamente; senão mantém WAITING_TRIAGE.

    Returns:
        bool: True se foi feito auto-dispatch, False caso contrário.
    """
    if not manifestation or manifestation.status != Manifestation.STATUS_WAITING_TRIAGE:
        return False

    try:
        nlp_analysis = getattr(manifestation, 'nlp_analysis', None)
        if not nlp_analysis:
            # Reload from DB if needed (e.g. just created)
            from intelligence.models import NLPAnalysis
            nlp_analysis = NLPAnalysis.objects.filter(manifestation=manifestation).first()
        if not nlp_analysis or not nlp_analysis.suggested_category_id:
            return False

        suggested = nlp_analysis.suggested_category
        sector = (getattr(suggested, 'default_sector', None) or '').strip()
        if not sector:
            return False

        if nlp_analysis.urgency_level >= 5:
            logger.info(
                f"Manifestação {manifestation.protocol} mantida em triagem: "
                f"urgência {nlp_analysis.urgency_level} (crítica)."
            )
            return False

        if not _confidence_ok(nlp_analysis):
            return False

        manifestation.status = Manifestation.STATUS_FORWARDED
        manifestation.category = suggested
        manifestation.save(update_fields=['status', 'category'])

        ManifestationUpdate.objects.create(
            manifestation=manifestation,
            new_status=Manifestation.STATUS_FORWARDED,
            internal_note="Despachado automaticamente pela IA.",
            updated_by=None,
        )
        logger.info(
            f"Auto-dispatch: manifestação {manifestation.protocol} encaminhada para "
            f"setor {sector} (categoria: {suggested.name})."
        )
        return True
    except Exception as e:
        logger.exception("Erro no roteamento automático da manifestação %s: %s", manifestation.protocol, e)
        return False
