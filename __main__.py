"""
Multi-language component provider entry point for dataproducts.
"""

from pulumi.provider.experimental import component_provider_host

from dataproduct import DataProductWithAspects

if __name__ == "__main__":
    component_provider_host(
        name="dataproducts",
        components=[DataProductWithAspects]
    )
