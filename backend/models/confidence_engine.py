import numpy as np

class AdaptiveConformalInference:
    def __init__(self, target_coverage=0.90, gamma=0.01):
        self.target_coverage = target_coverage
        self.gamma = gamma
        
        # alpha is 1 - coverage
        self.alpha_t = 1.0 - target_coverage
        
        self.q_t = None
        self.residuals = []
        
    def fit(self, residuals):
        """Fit on a validation set to get the initial baseline quantile"""
        self.residuals = np.abs(residuals)
        n = len(self.residuals)
        
        q_level = np.clip((n + 1.0) * (1 - self.alpha_t) / n, 0.0, 1.0)
        self.q_t = np.quantile(self.residuals, q_level)
        return self.q_t
        
    def step(self, error):
        """
        Update alpha_t dynamically based on whether the last prediction covered the true value.
        error: the absolute residual of the LAST prediction
        """
        covered = error <= self.q_t
        
        # ACI Update: alpha_{t+1} = alpha_t + gamma * (alpha_target - err_t)
        err_t = 1.0 if not covered else 0.0
        
        self.alpha_t = self.alpha_t + self.gamma * ((1 - self.target_coverage) - err_t)
        
        self.alpha_t = np.clip(self.alpha_t, 0.01, 0.99)
        
        n = len(self.residuals)
        if n > 0:
            q_level = np.clip((n + 1.0) * (1 - self.alpha_t) / n, 0.0, 1.0)
            self.q_t = np.quantile(self.residuals, q_level)
        
    def get_confidence_interval(self):
        """Returns the +- band for the prediction."""
        return self.q_t
        
    def get_confidence_score(self):
        """
        Synthesize a 0-100% confidence score.
        A smaller conformal band (q_t) means higher confidence.
        """
        if self.q_t is None:
            return 0
            
        # A simple heuristic: if q_t is huge, confidence is low.
        # Max acceptable error ~3.0 degrees F for "0%" confidence
        max_acceptable_err = 3.0
        
        score = 1.0 - (self.q_t / max_acceptable_err)
        score = np.clip(score, 0.0, 1.0)
        
        return round(score * 100)
