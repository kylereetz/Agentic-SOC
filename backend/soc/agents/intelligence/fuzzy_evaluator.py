"""
Fuzzy Threat Severity Evaluator (FTSE)
Maps crisp inputs (entropy_sigma, login_failures) to fuzzy linguistic states
and defuzzifies to a Threat Score [0, 1] via Mamdani Inference.
"""


def fuzzify_trapezoidal(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    elif a < x < b:
        return (x - a) / (b - a)
    elif b <= x <= c:
        return 1.0
    elif c < x < d:
        return (d - x) / (d - c)
    return 0.0


class FuzzyThreatEvaluator:
    METRIC_THRESHOLDS = {
        "entropy_sigma": {
            "stable": (-1.0, 0.0, 1.0, 2.5),
            "volatile": (1.5, 2.5, 3.5, 4.5),
            "chaotic": (3.5, 4.5, 100.0, 100.0),
        },
        "failed_logins": {
            "stable": (-1.0, 0.0, 2.0, 4.0),
            "volatile": (3.0, 4.0, 6.0, 8.0),
            "chaotic": (6.0, 8.0, 100.0, 100.0),
        },
        "out_degree": {
            "stable": (-1.0, 0.0, 10.0, 15.0),
            "volatile": (12.0, 15.0, 25.0, 30.0),
            "chaotic": (25.0, 30.0, 1000.0, 1000.0),
        },
        "in_degree_velocity": {
            "stable": (-1.0, 0.0, 2.0, 5.0),
            "volatile": (4.0, 6.0, 15.0, 20.0),
            "chaotic": (15.0, 20.0, 1000.0, 1000.0),
        },
        "beaconing_jitter_variance": {
            "stable": (50.0, 100.0, 1000.0, 1000.0),
            "volatile": (5.0, 10.0, 50.0, 100.0),
            "chaotic": (-1.0, 0.0, 5.0, 10.0),
        },  # Low variance is chaotic
        "payload_asymmetry": {
            "stable": (-1.0, 0.0, 2.0, 5.0),
            "volatile": (3.0, 5.0, 20.0, 30.0),
            "chaotic": (25.0, 30.0, 10000.0, 10000.0),
        },
        "process_lineage_depth": {
            "stable": (-1.0, 0.0, 2.0, 4.0),
            "volatile": (3.0, 4.0, 6.0, 8.0),
            "chaotic": (7.0, 8.0, 50.0, 50.0),
        },
        "resource_variance": {
            "stable": (-1.0, 0.0, 1.5, 2.5),
            "volatile": (2.0, 2.5, 4.0, 5.0),
            "chaotic": (4.0, 5.0, 100.0, 100.0),
        },
        "file_mod_velocity": {
            "stable": (-1.0, 0.0, 5.0, 10.0),
            "volatile": (8.0, 10.0, 50.0, 80.0),
            "chaotic": (60.0, 80.0, 10000.0, 10000.0),
        },
        "subnet_velocity": {
            "stable": (-1.0, 0.0, 10.0, 50.0),
            "volatile": (40.0, 50.0, 300.0, 500.0),
            "chaotic": (400.0, 500.0, 20000.0, 20000.0),
        },  # mph / km/h equivalent
        "token_access_freq": {
            "stable": (-1.0, 0.0, 10.0, 20.0),
            "volatile": (15.0, 20.0, 50.0, 80.0),
            "chaotic": (60.0, 80.0, 10000.0, 10000.0),
        },
    }

    def __init__(self):
        pass

    def fuzzify_metric(self, name: str, val: float):
        if name not in self.METRIC_THRESHOLDS:
            return {
                "Stable": 1.0,
                "Volatile": 0.0,
                "Chaotic": 0.0,
            }  # Ignore unknown, treat as stable

        t = self.METRIC_THRESHOLDS[name]
        stable = fuzzify_trapezoidal(val, *t["stable"])
        volatile = fuzzify_trapezoidal(val, *t["volatile"])
        chaotic = fuzzify_trapezoidal(val, *t["chaotic"])
        return {"Stable": stable, "Volatile": volatile, "Chaotic": chaotic}

    def evaluate(self, metrics: dict):
        # Default states
        rule_critical = 0.0
        rule_high = 0.0
        rule_moderate = 0.0
        rule_low = 1.0

        for name, val in metrics.items():
            if val is None or not isinstance(val, (int, float)):
                continue

            u = self.fuzzify_metric(name, float(val))

            # Simple aggregations
            # If ANY metric is chaotic, threat pushes towards Critical
            rule_critical = max(rule_critical, u["Chaotic"])

            # If ANY metric is volatile, threat pushes towards High
            rule_high = max(rule_high, u["Volatile"])

            # Moderate occurs if Volatile is somewhat present but not maxed out
            rule_moderate = max(rule_moderate, min(u["Volatile"], u["Stable"]))

            # Low is only maintained if Stable is high
            rule_low = min(rule_low, u["Stable"])

        # Prevent 0.0 division and bias low cleanly if no metrics provided
        if not metrics:
            rule_low = 1.0

        # Defuzzification spaces (Centers roughly mapping to Technical Specification)
        # Low: [0.0, 0.3), Moderate: [0.3, 0.6), High: [0.6, 0.8), Critical: [0.8, 1.0]

        numerator = 0.0
        denominator = 0.0

        # Discretize y from 0 to 1 with 100 points
        for i in range(101):
            y = i / 100.0

            # Membership of y in severity buckets
            m_low = fuzzify_trapezoidal(y, -0.1, 0.0, 0.15, 0.3)
            m_mod = fuzzify_trapezoidal(y, 0.2, 0.35, 0.45, 0.6)
            m_high = fuzzify_trapezoidal(y, 0.5, 0.65, 0.75, 0.85)
            m_crit = fuzzify_trapezoidal(y, 0.75, 0.85, 1.0, 1.1)

            # Max-Min composition
            agg_low = min(m_low, rule_low)
            agg_mod = min(m_mod, rule_moderate)
            agg_high = min(m_high, rule_high)
            agg_crit = min(m_crit, rule_critical)

            max_membership = max(agg_low, agg_mod, agg_high, agg_crit)

            numerator += y * max_membership
            denominator += max_membership

        if denominator == 0.0:
            return 0.0

        return numerator / denominator
