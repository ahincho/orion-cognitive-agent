"""AWS integration for ORION Cognitive Agent.

Thin wrappers around AWS SDK services used outside the langchain-aws /
DeepAgents path. The agent itself uses ``ChatBedrockConverse`` so this
package is mostly a quick-access backdoor for tools and health probes
that need to talk to Bedrock Runtime directly.
"""

from orion_cognitive_agent.aws.client import (
    get_bedrock_runtime_client,
    reset_bedrock_runtime_client_cache,
)

__all__ = [
    "get_bedrock_runtime_client",
    "reset_bedrock_runtime_client_cache",
]
