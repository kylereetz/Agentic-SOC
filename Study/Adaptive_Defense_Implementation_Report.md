# Adaptive Cyber Defense Technology Mapping

This report serves as a technical index detailing the implementation of the advanced AI and predictive math frameworks natively embedded into the Agentic SOC. Rather than relying on external libraries or API dependencies, these mechanisms exist as raw mathematical engines interwoven directly into the fabric of the internal agents.

---

## Layer 1: Thermodynamic Anomaly Detection
**Objective:** Overcome static netflow thresholds by mathematically "modeling the normal."

*   **Technology Mechanism:** Shannon Entropy Calculations & Welford’s Online Variance Algorithm.
*   **File Location:** `backend/soc/agents/traffic_sieve.py`
*   **Core Execution:** `TrafficSieveAgent._analyze_graph_flow()`
*   **Description:** Instead of triggering alerts when an IP breaches a static payload volume, the system bins network traffic logarithmically to compute the instantaneous Shannon Entropy. It utilizes Welford’s algorithm to maintain highly performant, one-pass rolling averages and variance. If a connection's entropy spikes > 3 Sigma above its historical baseline, a `GRAPH_ENTROPY_SPIKE` heuristic is flagged.

---

## Layer 2: Fuzzy Logic Escalation
**Objective:** Eliminate binary alert fatigue by introducing gradient contextual inference.

*   **Technology Mechanism:** Mamdani Fuzzy Inference Engine with Trapezoidal Membership variables.
*   **File Location:** 
    *   Engine: `backend/soc/agents/fuzzy_evaluator.py`
    *   Integration: `backend/soc/agents/triage.py`
*   **Core Execution:** `FuzzyThreatEvaluator.evaluate()` and `TriageEngine.classify_event()`
*   **Description:** Rather than firing alerts because a singular boolean threshold was crossed, the Triage agent passes 11 different contextual dimensions (e.g., `payload_asymmetry`, `beaconing_jitter_variance`) into a custom fuzzy calculus engine. If overlapping metrics drift into the `Warning` or `Chaotic` trapezoidal brackets, a continuous threat score `[0, 1]` is calculated via Centroid-of-Area, dynamically overriding standard severity classifications.

---

## Layer 3: Game-Theoretic Defense Matrix
**Objective:** Shift incident remediation from a predictable, static reaction into a probabilistic strategic defense.

*   **Technology Mechanism:** Von Neumann Minimax / Mixed Strategy Nash Equilibrium (MSNE) via Fictitious Play algorithm.
*   **File Location:** 
    *   Engine: `backend/soc/agents/game_theory_solver.py`
    *   Integration: `backend/soc/agents/responder.py`
*   **Core Execution:** `FictitiousPlaySolver.solve()` and `ResponderAgent._determine_action()`
*   **Description:** When a critical breach occurs, the Responder evaluates an internal utility payoff matrix contrasting core SOC actions (Quarantine, Honeypot, Rate Limit, Monitor) against assumed Attacker permutations (Evasion, Escalation, Persistence). The Python solver calculates the Nash equilibrium distribution, allowing the agent to predictably roll the dice and generate dynamic interventions (such as deceptive kernel-level `iptables PREROUTING` honeypot mappings) completely neutralizing adversarial adaptation techniques.

---

## Layer 4: Multi-Agent Reinforcement Learning (MARL)
**Objective:** Create a self-healing operational organism that autonomously tunes out noise over time without requiring hard script patches.

*   **Technology Mechanism:** Distributed Q-Learning, The Bellman Update Equation, Epsilon-Greedy Policy algorithms.
*   **File Location:** 
    *   Reward Generator: `backend/soc/agents/responder.py` (`approve_action()`)
    *   Q-Table Processor: `backend/soc/agents/triage.py` (`_marl_worker()`)
*   **Description:** The triage agent natively maintains a `triage_qtable.json` tracker, utilizing contextual state mapping (e.g. `GRAPH_ENTROPY_SPIKE_WARNING`). Each time Human-in-the-Loop input approves or rejects a containment action, the Responder propagates `+1.0` or `-1.0` reward points dynamically across the inter-agent `marl_rewards` bus. The Triage agent updates probability arrays via the Bellman formula on a continuous loop, ensuring that historical SOC decision metrics permanently optimize ongoing alerting. Epsilon values force 5% operational exploration limits ensuring the architecture doesn't trap itself in a cyclical feedback loop.
