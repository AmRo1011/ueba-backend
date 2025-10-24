from app.domain.rules.after_hours import AfterHoursRule
from app.domain.rules.failed_logins import FailedLoginsRule
from app.domain.rules.impossible_travel import ImpossibleTravelRule

ALL_RULES = {
  "after_hours": AfterHoursRule(),
  "failed_logins": FailedLoginsRule(),
  "impossible_travel": ImpossibleTravelRule(),
}

def get_rules(enabled=None):
    if not enabled:
        return list(ALL_RULES.values())
    return [ALL_RULES[k] for k in enabled if k in ALL_RULES]
