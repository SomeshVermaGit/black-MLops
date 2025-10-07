"""
Validation Engine Service
Adapted from Newton - AI Theorem Prover
Validates configurations, model architectures, and training logic
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationType(Enum):
    CONFIG = "config"
    ARCHITECTURE = "architecture"
    DATA = "data"
    TRAINING = "training"


@dataclass
class ValidationRule:
    """Represents a validation rule"""
    name: str
    type: ValidationType
    condition: str
    error_message: str


@dataclass
class ValidationResult:
    """Result of validation check"""
    passed: bool
    rule_name: str
    message: str
    severity: str = "error"  # error, warning, info


class ConfigValidator:
    """Validates configuration settings"""

    def __init__(self):
        self.rules: List[ValidationRule] = self._init_rules()

    def _init_rules(self) -> List[ValidationRule]:
        """Initialize validation rules"""
        return [
            ValidationRule(
                name="vocab_size_positive",
                type=ValidationType.CONFIG,
                condition="vocab_size > 0",
                error_message="Vocabulary size must be positive"
            ),
            ValidationRule(
                name="embedding_dim_multiple",
                type=ValidationType.CONFIG,
                condition="embed_dim % num_heads == 0",
                error_message="Embedding dimension must be divisible by number of heads"
            ),
            ValidationRule(
                name="learning_rate_range",
                type=ValidationType.CONFIG,
                condition="0 < learning_rate < 1",
                error_message="Learning rate must be between 0 and 1"
            ),
        ]

    def validate(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate configuration"""
        results = []

        for rule in self.rules:
            try:
                # Extract variables from config
                local_vars = {k: v for k, v in config.items()}

                # Evaluate condition
                passed = eval(rule.condition, {"__builtins__": {}}, local_vars)

                results.append(ValidationResult(
                    passed=passed,
                    rule_name=rule.name,
                    message=rule.error_message if not passed else "✓ Passed",
                    severity="error" if not passed else "info"
                ))
            except Exception as e:
                results.append(ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    message=f"Validation error: {str(e)}",
                    severity="error"
                ))

        return results


class ArchitectureValidator:
    """Validates model architecture"""

    def validate_transformer(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate transformer architecture"""
        results = []

        # Check embedding dimension
        embed_dim = config.get("embed_dim", 0)
        num_heads = config.get("num_heads", 1)

        if embed_dim % num_heads != 0:
            results.append(ValidationResult(
                passed=False,
                rule_name="head_dimension",
                message=f"Embed dim ({embed_dim}) must be divisible by num heads ({num_heads})",
                severity="error"
            ))
        else:
            head_dim = embed_dim // num_heads
            results.append(ValidationResult(
                passed=True,
                rule_name="head_dimension",
                message=f"✓ Head dimension: {head_dim}",
                severity="info"
            ))

        # Check model size
        num_layers = config.get("num_layers", 0)
        vocab_size = config.get("vocab_size", 0)

        # Estimate parameters
        params = self._estimate_parameters(
            vocab_size, embed_dim, num_layers, num_heads
        )

        results.append(ValidationResult(
            passed=True,
            rule_name="parameter_count",
            message=f"✓ Estimated parameters: {params / 1e6:.2f}M",
            severity="info"
        ))

        # Memory estimation
        memory_gb = (params * 4) / (1024 ** 3)  # FP32
        if memory_gb > 16:
            results.append(ValidationResult(
                passed=True,
                rule_name="memory_warning",
                message=f"⚠ Large model: ~{memory_gb:.2f}GB memory required",
                severity="warning"
            ))

        return results

    def _estimate_parameters(
        self,
        vocab_size: int,
        embed_dim: int,
        num_layers: int,
        num_heads: int
    ) -> int:
        """Estimate model parameters"""
        # Embedding layer
        embedding_params = vocab_size * embed_dim

        # Transformer layers
        # Attention: Q, K, V projections + output projection
        attention_params = 4 * embed_dim * embed_dim

        # FFN: typically 4x expansion
        ffn_params = 2 * embed_dim * (4 * embed_dim)

        layer_params = attention_params + ffn_params
        transformer_params = num_layers * layer_params

        # Output layer
        output_params = vocab_size * embed_dim

        total = embedding_params + transformer_params + output_params
        return total


class DataValidator:
    """Validates training data"""

    def validate_dataset(self, dataset_info: Dict[str, Any]) -> List[ValidationResult]:
        """Validate dataset"""
        results = []

        # Check dataset size
        num_samples = dataset_info.get("num_samples", 0)
        if num_samples < 100:
            results.append(ValidationResult(
                passed=False,
                rule_name="dataset_size",
                message=f"Dataset too small: {num_samples} samples (minimum: 100)",
                severity="error"
            ))
        elif num_samples < 1000:
            results.append(ValidationResult(
                passed=True,
                rule_name="dataset_size",
                message=f"⚠ Small dataset: {num_samples} samples",
                severity="warning"
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                rule_name="dataset_size",
                message=f"✓ Dataset size: {num_samples} samples",
                severity="info"
            ))

        return results


class ValidationEngine:
    """Main validation engine"""

    def __init__(self):
        self.config_validator = ConfigValidator()
        self.arch_validator = ArchitectureValidator()
        self.data_validator = DataValidator()

    def validate_all(
        self,
        config: Dict[str, Any],
        dataset_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run all validations"""
        all_results = []

        # Config validation
        print("🔍 Validating configuration...")
        config_results = self.config_validator.validate(config)
        all_results.extend(config_results)

        # Architecture validation
        print("🔍 Validating architecture...")
        arch_results = self.arch_validator.validate_transformer(config)
        all_results.extend(arch_results)

        # Data validation
        if dataset_info:
            print("🔍 Validating dataset...")
            data_results = self.data_validator.validate_dataset(dataset_info)
            all_results.extend(data_results)

        # Summarize results
        errors = [r for r in all_results if not r.passed and r.severity == "error"]
        warnings = [r for r in all_results if r.severity == "warning"]
        passed = len(errors) == 0

        return {
            "passed": passed,
            "errors": [{"rule": r.rule_name, "message": r.message} for r in errors],
            "warnings": [{"rule": r.rule_name, "message": r.message} for r in warnings],
            "all_results": [
                {
                    "rule": r.rule_name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity
                }
                for r in all_results
            ]
        }
