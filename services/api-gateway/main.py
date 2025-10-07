"""
Unified API Gateway for MLOps Collaborative Platform
Integrates all services: Chaos Engine, Collaborative Editor, LLM Training, and Validation
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chaos_engine.chaos_integration import (
    ChaosController, ChaosLayer, DataFaultInjector,
    ModelFaultInjector, MetricsObserver
)
from collab_editor.collab_service import (
    CollabEditorService, User, Operation
)
from llm_trainer.training_service import (
    LLMTrainingService, TokenizerService, ModelSize
)
from validation_engine.validation_service import ValidationEngine

# Initialize FastAPI
app = FastAPI(
    title="MLOps Collaborative Platform",
    description="Unified platform for ML training, collaboration, and chaos testing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chaos_controller = ChaosController()
collab_service = CollabEditorService()
training_service = LLMTrainingService()
tokenizer_service = TokenizerService()
validation_engine = ValidationEngine()

# Initialize chaos injectors and observers
chaos_controller.register_injector(ChaosLayer.DATA, DataFaultInjector())
chaos_controller.register_injector(ChaosLayer.MODEL, ModelFaultInjector())
chaos_controller.register_observer(MetricsObserver())


# ==================== Pydantic Models ====================

class ChaosExperimentRequest(BaseModel):
    name: str
    layer: str  # data, model, infrastructure
    fault_type: str
    parameters: Dict[str, Any]
    duration: int = 60


class TrainingJobRequest(BaseModel):
    job_id: str
    model_size: str  # tiny, small, medium, large
    data_path: str
    custom_config: Optional[Dict[str, Any]] = None


class ValidationRequest(BaseModel):
    config: Dict[str, Any]
    dataset_info: Optional[Dict[str, Any]] = None


class CollabSessionRequest(BaseModel):
    session_id: str
    document_id: str
    user_id: str
    username: str


# ==================== Health Check ====================

@app.get("/")
async def root():
    return {
        "name": "MLOps Collaborative Platform",
        "version": "1.0.0",
        "services": {
            "chaos_engine": "active",
            "collab_editor": "active",
            "llm_trainer": "active",
            "validation_engine": "active"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ==================== Chaos Engineering Endpoints ====================

@app.post("/chaos/experiments")
async def create_chaos_experiment(request: ChaosExperimentRequest):
    """Create and run a chaos experiment"""
    try:
        layer = ChaosLayer(request.layer)
        experiment = chaos_controller.create_experiment(
            name=request.name,
            layer=layer,
            fault_type=request.fault_type,
            parameters=request.parameters,
            duration=request.duration
        )

        # Run experiment asynchronously
        metrics = await chaos_controller.run_experiment(experiment)

        return {
            "success": True,
            "experiment_id": experiment.id,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== LLM Training Endpoints ====================

@app.post("/training/jobs")
async def create_training_job(request: TrainingJobRequest):
    """Create a new LLM training job"""
    try:
        model_size = ModelSize(request.model_size)
        job = training_service.create_job(
            job_id=request.job_id,
            model_size=model_size,
            data_path=request.data_path,
            custom_config=request.custom_config
        )

        return {
            "success": True,
            "job_id": job.id,
            "status": job.status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/training/jobs/{job_id}/start")
async def start_training_job(job_id: str):
    """Start a training job"""
    # Run training in background
    asyncio.create_task(training_service.start_training(job_id))

    return {
        "success": True,
        "message": f"Training job {job_id} started"
    }


@app.get("/training/jobs/{job_id}")
async def get_training_job_status(job_id: str):
    """Get training job status"""
    status = training_service.get_job_status(job_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/training/jobs")
async def list_training_jobs():
    """List all training jobs"""
    return training_service.list_jobs()


# ==================== Validation Endpoints ====================

@app.post("/validation/validate")
async def validate_configuration(request: ValidationRequest):
    """Validate model configuration and dataset"""
    results = validation_engine.validate_all(
        config=request.config,
        dataset_info=request.dataset_info
    )

    return results


# ==================== Collaborative Editor Endpoints ====================

@app.post("/collab/sessions")
async def create_collab_session(request: CollabSessionRequest):
    """Create or join a collaborative editing session"""
    # Create session
    session = collab_service.create_session(
        request.session_id,
        request.document_id
    )

    # Join session
    result = await collab_service.join_session(
        request.session_id,
        request.user_id,
        request.username
    )

    return result


@app.get("/collab/sessions/{session_id}")
async def get_session_state(session_id: str):
    """Get current session state"""
    session = collab_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.get_state()


# ==================== WebSocket for Real-time Collaboration ====================

@app.websocket("/ws/collab/{session_id}/{user_id}")
async def websocket_collab(websocket: WebSocket, session_id: str, user_id: str):
    """WebSocket endpoint for real-time collaboration"""
    await websocket.accept()

    try:
        while True:
            # Receive operation from client
            data = await websocket.receive_json()

            # Process operation
            operation = Operation(
                type=data["type"],
                position=data["position"],
                content=data["content"],
                user_id=user_id,
                version=data["version"]
            )

            result = await collab_service.handle_operation(session_id, operation)

            # Send result back to client
            await websocket.send_json(result)

    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected from session {session_id}")


# ==================== Integrated Workflows ====================

@app.post("/workflows/train-with-validation")
async def train_with_validation(
    job_id: str,
    model_size: str,
    data_path: str,
    config: Dict[str, Any]
):
    """Integrated workflow: Validate config, then train"""

    # Step 1: Validate configuration
    validation_results = validation_engine.validate_all(config)

    if not validation_results["passed"]:
        return {
            "success": False,
            "step": "validation",
            "errors": validation_results["errors"]
        }

    # Step 2: Create training job
    try:
        model_size_enum = ModelSize(model_size)
        job = training_service.create_job(
            job_id=job_id,
            model_size=model_size_enum,
            data_path=data_path,
            custom_config=config
        )

        # Start training
        asyncio.create_task(training_service.start_training(job_id))

        return {
            "success": True,
            "validation": validation_results,
            "job_id": job.id,
            "status": "training_started"
        }
    except Exception as e:
        return {
            "success": False,
            "step": "training",
            "error": str(e)
        }


@app.post("/workflows/chaos-test-model")
async def chaos_test_model(
    job_id: str,
    chaos_config: Dict[str, Any]
):
    """Integrated workflow: Run chaos tests on trained model"""

    # Check if job exists
    job_status = training_service.get_job_status(job_id)
    if "error" in job_status:
        raise HTTPException(status_code=404, detail="Training job not found")

    # Run chaos experiment
    layer = ChaosLayer(chaos_config.get("layer", "model"))
    experiment = chaos_controller.create_experiment(
        name=f"chaos_test_{job_id}",
        layer=layer,
        fault_type=chaos_config.get("fault_type", "model_drift"),
        parameters=chaos_config.get("parameters", {}),
        duration=chaos_config.get("duration", 60)
    )

    metrics = await chaos_controller.run_experiment(experiment)

    return {
        "success": True,
        "job_id": job_id,
        "chaos_results": metrics
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
