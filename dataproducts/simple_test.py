"""
Simple component for testing multi-language provider without GCP dependencies
"""

import pulumi
from pulumi import ComponentResource, ResourceOptions, Input
from typing_extensions import TypedDict


class SimpleTestArgs(TypedDict):
    """Arguments for simple test component"""
    message: Input[str]
    """The test message to output"""


class SimpleTestComponent(ComponentResource):
    """Simple component that doesn't create any resources - just for testing"""

    message: pulumi.Output[str]
    """The test message output"""

    def __init__(self, name: str, args: SimpleTestArgs, opts: ResourceOptions = None):
        super().__init__('dataproducts:index:SimpleTest', name, {}, opts)

        # Store the message as output
        self.message = pulumi.Output.from_input(args["message"])

        # Register outputs
        self.register_outputs({
            "message": self.message
        })
