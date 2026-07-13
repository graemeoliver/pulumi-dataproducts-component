"""
Pulumi component package for Dataplex Data Products
"""

from .dataproduct import DataProductWithAspects
from .simple_test import SimpleTestComponent
from .data_product_dh2_orchestrator import DataProductDH2Orchestrator

__all__ = [
    "DataProductWithAspects",
    "SimpleTestComponent",
    "DataProductDH2Orchestrator",
]
