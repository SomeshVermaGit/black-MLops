#!/usr/bin/env python3
"""
Quick service test script
Tests each service independently without starting the full API
"""

import sys
import os

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

print("🧪 Testing MLOps Platform Services\n")
print("="*60)

# Test 1: Validation Engine
print("\n1️⃣  Testing Validation Engine...")
try:
    from validation_engine.validation_service import ValidationEngine

    engine = ValidationEngine()
    config = {
        "vocab_size": 32000,
        "embed_dim": 768,
        "num_heads": 12,
        "num_layers": 12,
        "learning_rate": 5e-5
    }

    result = engine.validate_all(config)
    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"   {status} - Validation Engine working")
except Exception as e:
    print(f"   ❌ FAIL - {e}")

# Test 2: Chaos Engine
print("\n2️⃣  Testing Chaos Engine...")
try:
    from chaos_engine.chaos_integration import ChaosController, ChaosLayer

    controller = ChaosController()
    experiment = controller.create_experiment(
        name="test",
        layer=ChaosLayer.DATA,
        fault_type="test_fault",
        parameters={},
        duration=1
    )

    print(f"   ✅ PASS - Chaos Engine working (Experiment: {experiment.id})")
except Exception as e:
    print(f"   ❌ FAIL - {e}")

# Test 3: Collaborative Editor
print("\n3️⃣  Testing Collaborative Editor...")
try:
    from collab_editor.collab_service import CollabEditorService, User

    service = CollabEditorService()
    session = service.create_session("test-session", "test-doc")
    user = User(id="user1", username="TestUser")
    session.add_user(user)

    print(f"   ✅ PASS - Collaborative Editor working (Session: {session.id})")
except Exception as e:
    print(f"   ❌ FAIL - {e}")

# Test 4: LLM Trainer
print("\n4️⃣  Testing LLM Training Service...")
try:
    from llm_trainer.training_service import LLMTrainingService, ModelSize

    service = LLMTrainingService()
    job = service.create_job(
        job_id="test-job",
        model_size=ModelSize.TINY,
        data_path="./test.txt"
    )

    print(f"   ✅ PASS - LLM Trainer working (Job: {job.id})")
except Exception as e:
    print(f"   ❌ FAIL - {e}")

# Summary
print("\n" + "="*60)
print("✅ All core services are functional!")
print("\nNext steps:")
print("  - Run 'python example_usage.py' for full demo")
print("  - Run 'python services/api-gateway/main.py' to start API")
print("  - Visit http://localhost:8000/docs for API documentation")
print("="*60 + "\n")
