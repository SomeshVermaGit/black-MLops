#!/usr/bin/env python3
"""
Example usage of the MLOps Collaborative Platform
Demonstrates all major features and workflows
"""

import asyncio
import sys
import os

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from chaos_engine.chaos_integration import (
    ChaosController, ChaosLayer, DataFaultInjector, MetricsObserver
)
from collab_editor.collab_service import CollabEditorService, User, Operation
from llm_trainer.training_service import LLMTrainingService, ModelSize
from validation_engine.validation_service import ValidationEngine


async def demo_chaos_testing():
    """Demonstrate chaos engineering capabilities"""
    print("\n" + "="*60)
    print("🧪 CHAOS ENGINEERING DEMO")
    print("="*60 + "\n")

    controller = ChaosController()
    controller.register_injector(ChaosLayer.DATA, DataFaultInjector())
    controller.register_observer(MetricsObserver())

    # Create experiment
    experiment = controller.create_experiment(
        name="data_corruption_test",
        layer=ChaosLayer.DATA,
        fault_type="data_corruption",
        parameters={"corruption_rate": 0.1},
        duration=3  # Short duration for demo
    )

    # Run experiment
    metrics = await controller.run_experiment(experiment)
    print(f"\n📊 Results:")
    print(f"   - Experiment ID: {metrics['experiment_id']}")
    print(f"   - Resilience Score: {metrics['resilience_score']}/100")
    print(f"   - Duration: {metrics['duration']:.2f}s")


async def demo_collaborative_editing():
    """Demonstrate collaborative editing"""
    print("\n" + "="*60)
    print("👥 COLLABORATIVE EDITING DEMO")
    print("="*60 + "\n")

    service = CollabEditorService()

    # Create session
    session = service.create_session("demo-session", "model_config.py")

    # Add users
    alice = User(id="user1", username="Alice")
    bob = User(id="user2", username="Bob")

    session.add_user(alice)
    session.add_user(bob)

    # Simulate operations
    op1 = Operation(
        type="insert",
        position=0,
        content="# Model Configuration\n",
        user_id=alice.id,
        version=0
    )

    result = await session.process_operation(op1)
    print(f"✓ Alice added header: {result['success']}")

    op2 = Operation(
        type="insert",
        position=len(session.document.content),
        content="vocab_size = 32000\n",
        user_id=bob.id,
        version=1
    )

    result = await session.process_operation(op2)
    print(f"✓ Bob added config: {result['success']}")

    # Show final state
    state = session.get_state()
    print(f"\n📄 Document content:")
    print(state['content'])
    print(f"\n👤 Active users: {', '.join([u['username'] for u in state['users']])}")


async def demo_llm_training():
    """Demonstrate LLM training workflow"""
    print("\n" + "="*60)
    print("🤖 LLM TRAINING DEMO")
    print("="*60 + "\n")

    service = LLMTrainingService()

    # Create training job
    job = service.create_job(
        job_id="demo-tiny-llm",
        model_size=ModelSize.TINY,
        data_path="./data/sample.txt",
        custom_config={
            "num_epochs": 2,
            "learning_rate": 1e-4
        }
    )

    print(f"✓ Created job: {job.id}")
    print(f"   - Model size: {ModelSize.TINY.value}")
    print(f"   - Embedding dim: {job.model_config.embed_dim}")
    print(f"   - Layers: {job.model_config.num_layers}")

    # Start training
    result = await service.start_training(job.id)

    if result['success']:
        print(f"\n✓ Training completed!")
        print(f"   - Final loss: {result['final_metrics'].get('loss', 'N/A')}")
        print(f"   - Checkpoint: {result['checkpoint_path']}")


def demo_validation():
    """Demonstrate configuration validation"""
    print("\n" + "="*60)
    print("✅ VALIDATION DEMO")
    print("="*60 + "\n")

    engine = ValidationEngine()

    # Test valid config
    valid_config = {
        "vocab_size": 32000,
        "embed_dim": 768,
        "num_heads": 12,
        "num_layers": 12,
        "learning_rate": 5e-5
    }

    results = engine.validate_all(
        config=valid_config,
        dataset_info={"num_samples": 10000}
    )

    print(f"Configuration: {'✓ VALID' if results['passed'] else '✗ INVALID'}")

    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"   - {error['message']}")

    if results['warnings']:
        print("\n⚠️  Warnings:")
        for warning in results['warnings']:
            print(f"   - {warning['message']}")

    print("\n📋 All validation results:")
    for result in results['all_results']:
        icon = "✓" if result['passed'] else "✗"
        print(f"   {icon} {result['rule']}: {result['message']}")

    # Test invalid config
    print("\n" + "-"*60)
    print("Testing INVALID configuration...")
    print("-"*60 + "\n")

    invalid_config = {
        "vocab_size": -1,  # Invalid
        "embed_dim": 770,   # Not divisible by num_heads
        "num_heads": 12,
        "num_layers": 12,
        "learning_rate": 2.0  # Out of range
    }

    results = engine.validate_all(config=invalid_config)

    print(f"Configuration: {'✓ VALID' if results['passed'] else '✗ INVALID'}")

    if results['errors']:
        print("\n❌ Errors found:")
        for error in results['errors']:
            print(f"   - {error['message']}")


async def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("🚀 MLOps Collaborative Platform - Demo")
    print("="*60)

    # Run demos
    demo_validation()
    await demo_chaos_testing()
    await demo_collaborative_editing()
    await demo_llm_training()

    print("\n" + "="*60)
    print("✨ All demos completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
