"""
Multi-language component provider entry point for dataproducts.
"""

from pulumi.provider.experimental import component_provider_host

from dataproducts import DataProductWithAspects, SimpleTestComponent

if __name__ == "__main__":
    component_provider_host(
        name="dataproducts",
        components=[DataProductWithAspects, SimpleTestComponent]
    )
