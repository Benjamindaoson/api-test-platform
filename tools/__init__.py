

from tools.codegraph_tools import CODEGRAPH_TOOLS
from tools.api_test_tools import API_TEST_TOOLS
from tools.api_gen_tools import API_GEN_TOOLS
from tools.project_tools import PROJECT_TOOLS

# Code analysis tools
CODE_TOOLS = list(CODEGRAPH_TOOLS)

# API testing tools (execution + generation)
TEST_TOOLS = list(API_TEST_TOOLS)
GEN_TOOLS = list(API_GEN_TOOLS)

# Full tool set for api-tester
API_TOOLS = list(API_TEST_TOOLS) + list(API_GEN_TOOLS)

# Supervisor tools include project lookup so it can resolve context.project_id
SUPERVISOR_TOOLS: list = list(PROJECT_TOOLS)

__all__ = [
    "CODEGRAPH_TOOLS", "API_TEST_TOOLS", "API_GEN_TOOLS", "PROJECT_TOOLS",
    "CODE_TOOLS", "TEST_TOOLS", "GEN_TOOLS", "API_TOOLS",
    "SUPERVISOR_TOOLS",
]