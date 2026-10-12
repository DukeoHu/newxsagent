from xsagent.domain.project.models import InterventionLevel
from xsagent.domain.memory.patch_models import RiskLevel


def should_auto_apply(intervention: InterventionLevel, risk: RiskLevel) -> bool:
    if risk == RiskLevel.LOW:
        return True
    if risk == RiskLevel.MEDIUM:
        return intervention in {InterventionLevel.AGGRESSIVE, InterventionLevel.BALANCED}
    if risk == RiskLevel.HIGH:
        return intervention == InterventionLevel.AGGRESSIVE
    return False
