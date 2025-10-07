"""
LLM Training Service
Combines Infinity and Arkformer capabilities
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio


class ModelSize(Enum):
    TINY = "tiny"      # ~10M params
    SMALL = "small"    # ~40M params
    MEDIUM = "medium"  # ~100M params
    LARGE = "large"    # ~350M params


@dataclass
class ModelConfig:
    vocab_size: int = 32000
    embed_dim: int = 256
    num_heads: int = 8
    num_layers: int = 6
    max_seq_len: int = 1024
    dropout: float = 0.1
    use_flash_attention: bool = False


@dataclass
class TrainingConfig:
    output_dir: str = "./checkpoints"
    num_epochs: int = 3
    micro_batch_size: int = 4
    learning_rate: float = 5e-5
    warmup_steps: int = 1000
    gradient_accumulation_steps: int = 4
    use_deepspeed: bool = False
    deepspeed_config: Optional[str] = None
    fp16: bool = True


class TrainingJob:
    """Represents a training job"""

    def __init__(
        self,
        job_id: str,
        model_config: ModelConfig,
        training_config: TrainingConfig
    ):
        self.id = job_id
        self.model_config = model_config
        self.training_config = training_config
        self.status = "pending"
        self.progress = 0.0
        self.metrics = {}

    def update_progress(self, progress: float, metrics: Dict[str, Any]):
        """Update training progress"""
        self.progress = progress
        self.metrics = metrics


class LLMTrainingService:
    """Service for managing LLM training jobs"""

    def __init__(self):
        self.active_jobs: Dict[str, TrainingJob] = {}
        self.completed_jobs: List[TrainingJob] = []

    def create_job(
        self,
        job_id: str,
        model_size: ModelSize,
        data_path: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> TrainingJob:
        """Create a new training job"""

        # Set model config based on size
        model_configs = {
            ModelSize.TINY: ModelConfig(embed_dim=256, num_heads=8, num_layers=6),
            ModelSize.SMALL: ModelConfig(embed_dim=512, num_heads=8, num_layers=8),
            ModelSize.MEDIUM: ModelConfig(embed_dim=768, num_heads=12, num_layers=12),
            ModelSize.LARGE: ModelConfig(embed_dim=1024, num_heads=16, num_layers=24),
        }

        model_config = model_configs[model_size]
        training_config = TrainingConfig()

        # Apply custom config if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(training_config, key):
                    setattr(training_config, key, value)

        job = TrainingJob(job_id, model_config, training_config)
        self.active_jobs[job_id] = job

        print(f"🚀 Created training job: {job_id} ({model_size.value})")
        return job

    async def start_training(self, job_id: str) -> Dict[str, Any]:
        """Start training job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        job.status = "running"
        print(f"🏋️ Starting training job: {job_id}")

        # Simulate training progress
        for epoch in range(job.training_config.num_epochs):
            # Simulate epoch training
            await asyncio.sleep(1)

            progress = (epoch + 1) / job.training_config.num_epochs
            metrics = {
                "epoch": epoch + 1,
                "loss": 2.5 - (epoch * 0.3),  # Simulated decreasing loss
                "perplexity": 50 - (epoch * 5),
                "learning_rate": job.training_config.learning_rate
            }

            job.update_progress(progress, metrics)
            print(f"📊 Epoch {epoch + 1}: Loss={metrics['loss']:.3f}")

        # Complete job
        job.status = "completed"
        job.progress = 1.0
        self.completed_jobs.append(job)
        del self.active_jobs[job_id]

        print(f"✅ Training completed: {job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "final_metrics": job.metrics,
            "checkpoint_path": f"{job.training_config.output_dir}/{job_id}"
        }

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get training job status"""
        job = self.active_jobs.get(job_id)
        if not job:
            # Check completed jobs
            for completed_job in self.completed_jobs:
                if completed_job.id == job_id:
                    job = completed_job
                    break

        if not job:
            return {"error": "Job not found"}

        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "metrics": job.metrics,
            "model_config": {
                "vocab_size": job.model_config.vocab_size,
                "embed_dim": job.model_config.embed_dim,
                "num_layers": job.model_config.num_layers
            }
        }

    def list_jobs(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all training jobs"""
        return {
            "active": [
                {"id": j.id, "status": j.status, "progress": j.progress}
                for j in self.active_jobs.values()
            ],
            "completed": [
                {"id": j.id, "status": j.status, "final_metrics": j.metrics}
                for j in self.completed_jobs
            ]
        }


class TokenizerService:
    """Service for managing tokenizers"""

    def __init__(self):
        self.tokenizers: Dict[str, Any] = {}

    def train_tokenizer(
        self,
        tokenizer_id: str,
        data_path: str,
        vocab_size: int = 32000,
        model_type: str = "bpe"
    ) -> Dict[str, Any]:
        """Train a new tokenizer"""
        print(f"🔤 Training tokenizer: {tokenizer_id}")

        # Simulated tokenizer training
        tokenizer_info = {
            "id": tokenizer_id,
            "vocab_size": vocab_size,
            "model_type": model_type,
            "path": f"./tokenizers/{tokenizer_id}.model"
        }

        self.tokenizers[tokenizer_id] = tokenizer_info
        return {"success": True, "tokenizer": tokenizer_info}

    def get_tokenizer(self, tokenizer_id: str) -> Optional[Dict[str, Any]]:
        """Get tokenizer info"""
        return self.tokenizers.get(tokenizer_id)
