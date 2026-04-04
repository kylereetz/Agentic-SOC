"""
Game Theory Minimax / Mixed Strategy Nash Equilibrium Solver
Utilizes the Fictitious Play algorithmic method to solve Zero-Sum games
without requiring hefty third-party Linear Programming dependencies like SciPy.
"""

import logging
from soc.bootstrap import get_soc_path

logger = logging.getLogger("RCA-Strategist")
logger.setLevel(logging.INFO)

class FictitiousPlaySolver:
    """
    SENTINEL-STRATEGIST: Defensive Resource Allocator.
    Solves for the Mixed Strategy Nash Equilibrium (MSNE) using Fictitious Play.
    """
    def __init__(self, iterations: int = 1500):
        self.iterations = iterations
        self.agent_name = "SENTINEL-STRATEGIST"
        
        # [IQ] Doctrine Reference: SENTINEL-STRATEGIST
        logger.info(f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_sentinel_strategist.md')}")

    def solve(self, utility_matrix: List[List[float]]) -> List[float]:
        """
        Solves for the Defender MSNE probabilities against an Adversary.
        utility_matrix: 2D array where rows are Defender actions, cols are Attacker actions.
        Returns: list of probabilities for each Defender action.
        """
        num_def_actions = len(utility_matrix)
        if num_def_actions == 0:
            return []
        num_att_actions = len(utility_matrix[0])
        
        # Empirical sums of payoffs
        def_payoff_sums = [0.0] * num_def_actions
        att_payoff_sums = [0.0] * num_att_actions
        
        # Strategy counts
        def_counts = [0] * num_def_actions
        att_counts = [0] * num_att_actions
        
        # Initial arbitrary choices
        curr_def = random.randint(0, num_def_actions - 1)
        curr_att = random.randint(0, num_att_actions - 1)
        
        for _ in range(self.iterations):
            def_counts[curr_def] += 1
            att_counts[curr_att] += 1
            
            # Update beliefs about payoffs based on opponent's last move
            for i in range(num_def_actions):
                def_payoff_sums[i] += utility_matrix[i][curr_att]
                
            for j in range(num_att_actions):
                att_payoff_sums[j] += utility_matrix[curr_def][j]
                
            # Attacker chooses column that MINIMIZES defender's payoff
            curr_att = att_payoff_sums.index(min(att_payoff_sums))
            
            # Defender chooses row that MAXIMIZES their payoff
            curr_def = def_payoff_sums.index(max(def_payoff_sums))
            
        # Convert defender counts to probabilities
        total = sum(def_counts)
        if total == 0:
            return [1.0 / num_def_actions] * num_def_actions
            
        return [round(c / total, 3) for c in def_counts]
