"""
Pre-trained Fraud Detection Model for Insurance Claims

This module contains a scikit-learn based fraud detection model that can be
serialized and loaded in Spark UDFs for distributed scoring.
"""

import pickle
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
import os


@dataclass
class FraudModelConfig:
    """Configuration for the fraud detection model"""
    model_version: str = "1.0.0"
    model_name: str = "InsuranceClaimsFraudDetector"
    threshold_high: float = 0.7
    threshold_medium: float = 0.5
    threshold_low: float = 0.3


class FraudDetectionModel:
    """
    Pre-trained fraud detection model using a gradient boosting-like scoring approach.
    
    This model simulates a trained ML model with learned weights from historical
    fraud data. In production, this would be replaced with an actual trained model
    (e.g., XGBoost, LightGBM, or neural network).
    """
    
    def __init__(self):
        self.config = FraudModelConfig()
        self.feature_weights = self._initialize_learned_weights()
        self.loss_type_embeddings = self._initialize_loss_embeddings()
        self.status_embeddings = self._initialize_status_embeddings()
        self.is_fitted = True
    
    def _initialize_learned_weights(self) -> Dict[str, float]:
        """Learned feature weights from training (simulated)"""
        return {
            'estimate_amount_normalized': 0.15,
            'siu_referral_flag': 0.25,
            'investigation_active': 0.18,
            'prior_claims_factor': 0.12,
            'historical_risk_score': 0.10,
            'policy_age_risk': 0.08,
            'injury_flag': 0.05,
            'loss_type_risk': 0.20,
            'reporting_delay_risk': 0.07,
            'premium_ratio_anomaly': 0.10,
            'text_fraud_indicators': 0.15,
            'cross_feature_interaction': 0.05
        }
    
    def _initialize_loss_embeddings(self) -> Dict[str, np.ndarray]:
        """Learned embeddings for loss types (simulated from training)"""
        return {
            'theft': np.array([0.85, 0.9, 0.7, 0.8]),
            'fire': np.array([0.75, 0.8, 0.65, 0.7]),
            'vandalism': np.array([0.55, 0.6, 0.5, 0.55]),
            'collision': np.array([0.35, 0.4, 0.3, 0.35]),
            'hit and run': np.array([0.50, 0.55, 0.45, 0.5]),
            'weather': np.array([0.15, 0.2, 0.1, 0.15]),
            'flood': np.array([0.25, 0.3, 0.2, 0.25]),
            'equipment damage': np.array([0.20, 0.25, 0.15, 0.2]),
            'default': np.array([0.30, 0.35, 0.25, 0.3])
        }
    
    def _initialize_status_embeddings(self) -> Dict[str, float]:
        """Learned embeddings for investigation status"""
        return {
            'open': 0.85,
            'pending': 0.80,
            'monitoring': 0.60,
            'closed': 0.20,
            'legitimate claim': 0.10,
            'n/a': 0.30,
            'default': 0.40
        }
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid activation for probability output"""
        return 1 / (1 + np.exp(-x))
    
    def _normalize_estimate(self, estimate: Optional[float]) -> float:
        """Normalize estimate amount using log transformation"""
        if estimate is None or estimate <= 0:
            return 0.0
        log_estimate = np.log1p(estimate)
        return min(log_estimate / 12.0, 1.0)
    
    def _get_loss_type_embedding(self, loss_type: Optional[str]) -> np.ndarray:
        """Get learned embedding for loss type"""
        if loss_type is None:
            return self.loss_type_embeddings['default']
        loss_lower = loss_type.lower()
        for key in self.loss_type_embeddings:
            if key in loss_lower:
                return self.loss_type_embeddings[key]
        return self.loss_type_embeddings['default']
    
    def _get_status_score(self, status: Optional[str]) -> float:
        """Get learned score for investigation status"""
        if status is None:
            return self.status_embeddings['default']
        status_lower = status.lower()
        for key in self.status_embeddings:
            if key in status_lower:
                return self.status_embeddings[key]
        return self.status_embeddings['default']
    
    def _compute_interaction_features(
        self, 
        loss_embedding: np.ndarray,
        estimate_norm: float,
        siu_flag: float,
        policy_age_risk: float
    ) -> float:
        """Compute cross-feature interactions (learned from training)"""
        interaction_weights = np.array([0.3, 0.25, 0.25, 0.2])
        base_interaction = np.dot(loss_embedding, interaction_weights)
        
        if siu_flag > 0.5 and estimate_norm > 0.5:
            base_interaction *= 1.3
        
        if policy_age_risk > 0.5 and base_interaction > 0.5:
            base_interaction *= 1.2
        
        return min(base_interaction, 1.0)
    
    def predict_proba(
        self,
        loss_type: Optional[str],
        estimate_amount: Optional[float],
        siu_referral: Optional[str],
        investigation_status: Optional[str],
        prior_claims_count: Optional[int],
        historical_risk_score: Optional[float],
        policy_age_days: Optional[int],
        injuries_reported: Optional[str],
        reporting_delay_days: Optional[int] = None,
        estimate_premium_ratio: Optional[float] = None,
        has_fraud_keywords: Optional[bool] = None
    ) -> float:
        """
        Predict fraud probability using the pre-trained model.
        
        Returns a score from 0 to 1 representing fraud probability.
        """
        features = {}
        
        features['estimate_amount_normalized'] = self._normalize_estimate(estimate_amount)
        
        features['siu_referral_flag'] = 1.0 if siu_referral and siu_referral.lower() == 'yes' else 0.0
        
        features['investigation_active'] = self._get_status_score(investigation_status)
        
        prior_count = prior_claims_count or 0
        features['prior_claims_factor'] = min(prior_count * 0.15, 1.0)
        
        features['historical_risk_score'] = (historical_risk_score or 0) / 100.0
        
        policy_age = policy_age_days or 365
        if policy_age < 30:
            features['policy_age_risk'] = 0.9
        elif policy_age < 90:
            features['policy_age_risk'] = 0.7
        elif policy_age < 180:
            features['policy_age_risk'] = 0.4
        else:
            features['policy_age_risk'] = 0.1
        
        features['injury_flag'] = 0.6 if injuries_reported and injuries_reported.lower() == 'yes' else 0.0
        
        loss_embedding = self._get_loss_type_embedding(loss_type)
        features['loss_type_risk'] = np.mean(loss_embedding)
        
        if reporting_delay_days is not None:
            if reporting_delay_days > 7:
                features['reporting_delay_risk'] = 0.7
            elif reporting_delay_days > 3:
                features['reporting_delay_risk'] = 0.4
            elif reporting_delay_days > 1:
                features['reporting_delay_risk'] = 0.2
            else:
                features['reporting_delay_risk'] = 0.0
        else:
            features['reporting_delay_risk'] = 0.0
        
        if estimate_premium_ratio is not None:
            if estimate_premium_ratio > 20:
                features['premium_ratio_anomaly'] = 0.9
            elif estimate_premium_ratio > 10:
                features['premium_ratio_anomaly'] = 0.6
            elif estimate_premium_ratio > 5:
                features['premium_ratio_anomaly'] = 0.3
            else:
                features['premium_ratio_anomaly'] = 0.0
        else:
            features['premium_ratio_anomaly'] = 0.0
        
        features['text_fraud_indicators'] = 0.7 if has_fraud_keywords else 0.0
        
        features['cross_feature_interaction'] = self._compute_interaction_features(
            loss_embedding,
            features['estimate_amount_normalized'],
            features['siu_referral_flag'],
            features['policy_age_risk']
        )
        
        weighted_sum = sum(
            features[key] * self.feature_weights[key]
            for key in self.feature_weights
        )
        
        raw_score = self._sigmoid((weighted_sum - 0.3) * 5)
        
        if features['siu_referral_flag'] > 0.5:
            raw_score = min(raw_score * 1.4, 1.0)
        
        return raw_score
    
    def predict_score(self, *args, **kwargs) -> float:
        """Return fraud risk score from 0-100"""
        return self.predict_proba(*args, **kwargs) * 100
    
    def get_risk_category(self, score: float) -> str:
        """Categorize risk based on score thresholds"""
        if score >= self.config.threshold_high * 100:
            return "High Risk"
        elif score >= self.config.threshold_medium * 100:
            return "Medium Risk"
        elif score >= self.config.threshold_low * 100:
            return "Low Risk"
        else:
            return "Minimal Risk"
    
    def save(self, filepath: str):
        """Serialize model to file"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'FraudDetectionModel':
        """Load model from file"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"Model loaded from: {filepath}")
        return model


def create_and_save_model(output_dir: str) -> str:
    """Create and save the pre-trained model"""
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "fraud_detection_model.pkl")
    
    model = FraudDetectionModel()
    model.save(model_path)
    
    return model_path


if __name__ == "__main__":
    model_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(model_dir, "models")
    
    model_path = create_and_save_model(models_dir)
    
    model = FraudDetectionModel.load(model_path)
    
    print("\n--- Model Test ---")
    test_cases = [
        {
            "loss_type": "Theft",
            "estimate_amount": 45000,
            "siu_referral": "Yes",
            "investigation_status": "Open",
            "prior_claims_count": 2,
            "historical_risk_score": 75,
            "policy_age_days": 45,
            "injuries_reported": "No"
        },
        {
            "loss_type": "Collision",
            "estimate_amount": 5000,
            "siu_referral": "No",
            "investigation_status": None,
            "prior_claims_count": 0,
            "historical_risk_score": None,
            "policy_age_days": 400,
            "injuries_reported": "No"
        },
        {
            "loss_type": "Weather",
            "estimate_amount": 3000,
            "siu_referral": "No",
            "investigation_status": "Closed",
            "prior_claims_count": 0,
            "historical_risk_score": 25,
            "policy_age_days": 200,
            "injuries_reported": "No"
        }
    ]
    
    for i, test in enumerate(test_cases):
        score = model.predict_score(**test)
        category = model.get_risk_category(score)
        print(f"\nTest Case {i+1} ({test['loss_type']}):")
        print(f"  Score: {score:.2f}")
        print(f"  Category: {category}")
