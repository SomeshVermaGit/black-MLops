"""
Chaos Engineering Integration for ML Pipelines
Adapted from ChaosEater project
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional
import asyncio
import time


class ChaosLayer(Enum):
    DATA = "data"
    MODEL = "model"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class ChaosExperiment:
    name: str
    layer: ChaosLayer
    fault_type: str
    parameters: Dict[str, Any]
    duration: int
    id: Optional[str] = None


class ChaosController:
    """Main chaos engineering controller for ML pipelines"""

    def __init__(self):
        self.injectors = {}
        self.observers = []
        self.active_experiments = {}

    def register_injector(self, layer: ChaosLayer, injector):
        """Register fault injector for specific layer"""
        self.injectors[layer] = injector

    def register_observer(self, observer):
        """Register metrics observer"""
        self.observers.append(observer)

    def create_experiment(
        self,
        name: str,
        layer: ChaosLayer,
        fault_type: str,
        parameters: Dict[str, Any],
        duration: int
    ) -> ChaosExperiment:
        """Create a new chaos experiment"""
        experiment = ChaosExperiment(
            name=name,
            layer=layer,
            fault_type=fault_type,
            parameters=parameters,
            duration=duration,
            id=f"{name}_{int(time.time())}"
        )
        return experiment

    async def run_experiment(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Execute chaos experiment and collect metrics"""
        print(f"🧪 Starting experiment: {experiment.name}")

        # Get appropriate injector
        injector = self.injectors.get(experiment.layer)
        if not injector:
            raise ValueError(f"No injector registered for layer {experiment.layer}")

        # Start experiment
        start_time = time.time()
        self.active_experiments[experiment.id] = experiment

        # Inject fault
        await injector.inject_fault(experiment.fault_type, experiment.parameters)

        # Wait for experiment duration
        await asyncio.sleep(experiment.duration)

        # Stop fault injection
        await injector.stop_fault()

        # Collect metrics
        metrics = {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "duration": time.time() - start_time,
            "status": "completed",
            "resilience_score": self._calculate_resilience_score()
        }

        # Notify observers
        for observer in self.observers:
            observer.record_metrics(metrics)

        del self.active_experiments[experiment.id]
        print(f"✅ Experiment completed: {experiment.name}")

        return metrics

    def _calculate_resilience_score(self) -> float:
        """Calculate resilience score based on metrics"""
        # Simplified scoring - in real implementation,
        # this would use actual metrics from observers
        base_score = 100.0
        return base_score


class DataFaultInjector:
    """Inject data-layer faults"""

    async def inject_fault(self, fault_type: str, parameters: Dict[str, Any]):
        """Inject specific data fault"""
        print(f"💉 Injecting {fault_type} with params: {parameters}")
        # Implementation would add actual fault injection logic

    async def stop_fault(self):
        """Stop fault injection"""
        print("🛑 Stopping fault injection")


class ModelFaultInjector:
    """Inject model-layer faults"""

    async def inject_fault(self, fault_type: str, parameters: Dict[str, Any]):
        print(f"💉 Injecting model fault: {fault_type}")

    async def stop_fault(self):
        print("🛑 Stopping model fault")


class MetricsObserver:
    """Observe and record experiment metrics"""

    def __init__(self):
        self.metrics_history = []

    def record_metrics(self, metrics: Dict[str, Any]):
        """Record experiment metrics"""
        self.metrics_history.append(metrics)
        print(f"📊 Metrics recorded: Resilience Score = {metrics.get('resilience_score', 0)}")

    def get_history(self) -> List[Dict[str, Any]]:
        """Get all recorded metrics"""
        return self.metrics_history
