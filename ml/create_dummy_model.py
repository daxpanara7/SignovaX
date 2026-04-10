"""
Create a dummy ensemble model to avoid 503 errors
This creates a minimal working model that can make predictions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from model import SignovaEnsemble

# Create and save a dummy model
print("Creating dummy ensemble model...")
model = SignovaEnsemble()

model_path = os.path.join(os.path.dirname(__file__), "..", "models", "ensemble.joblib")
model.save(model_path)
print(f"✅ Dummy model saved to {model_path}")
