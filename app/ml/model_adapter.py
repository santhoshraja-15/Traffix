"""
ML model adapter shim for the ``app/ml`` package.

Thin wrapper that re-exports the public interface of
``app.integrations.existing_ml_adapter`` under the ``ml`` package namespace.
This lets higher-level modules import from ``app.ml.model_adapter`` without
depending directly on the integrations layer.
"""
from __future__ import annotations

# Re-export the adapter class and factory function so callers can do:
#   from app.ml.model_adapter import get_model_adapter, TrafficModelAdapter
from app.integrations.existing_ml_adapter import TrafficModelAdapter, get_model_adapter

__all__ = ["TrafficModelAdapter", "get_model_adapter"]
