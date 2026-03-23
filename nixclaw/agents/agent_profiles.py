from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any

from nixclaw.tools.file_operations import read_file, write_file, delete_file
from nixclaw.tools.directory_ops import list_dir, create_dir
from nixclaw.tools.search_tools import search_files, search_content
from nixclaw.tools.shell_executor import execute_shell_command


@dataclass
class AgentProfile:
    """Template for creating specialized agents."""

    name: str
    system_message: str
    description: str
    tools: list[Callable[..., Any]] = field(default_factory=list)


# ── Core tool sets ───────────────────────────────────────────────────────────

FILE_TOOLS: list[Callable[..., Any]] = [read_file, write_file, delete_file]
DIR_TOOLS: list[Callable[..., Any]] = [list_dir, create_dir]
SEARCH_TOOLS: list[Callable[..., Any]] = [search_files, search_content]
SHELL_TOOLS: list[Callable[..., Any]] = [execute_shell_command]
ALL_TOOLS: list[Callable[..., Any]] = FILE_TOOLS + DIR_TOOLS + SEARCH_TOOLS + SHELL_TOOLS

# ── Pre-defined profiles ────────────────────────────────────────────────────

PROFILES: dict[str, AgentProfile] = {
    "CodeGenerator": AgentProfile(
        name="code_generator",
        description="Generates, modifies, and refactors code",
        system_message=(
            "You are an expert code generator. You write clean, efficient, well-structured code. "
            "You have access to file operations and shell commands. "
            "When writing code:\n"
            "- Follow best practices for the language\n"
            "- Add minimal but clear comments for non-obvious logic\n"
            "- Handle edge cases and errors\n"
            "- Use the provided tools to read existing code, write new files, and test your work\n"
            "Report your results clearly when done."
        ),
        tools=ALL_TOOLS,
    ),
    "Analyzer": AgentProfile(
        name="analyzer",
        description="Analyzes code, data, and systems for insights and issues",
        system_message=(
            "You are an expert analyst. You examine code, data, logs, and system state to provide "
            "clear, actionable insights. You can:\n"
            "- Read and analyze source code for bugs, patterns, and improvements\n"
            "- Search codebases for specific patterns or issues\n"
            "- Analyze command output and logs\n"
            "- Provide structured analysis with severity levels\n"
            "Always provide evidence-based conclusions with specific file/line references."
        ),
        tools=FILE_TOOLS + DIR_TOOLS + SEARCH_TOOLS,
    ),
    "Researcher": AgentProfile(
        name="researcher",
        description="Researches topics, gathers information, and synthesizes findings",
        system_message=(
            "You are a thorough researcher. You gather information from available sources, "
            "analyze it, and synthesize clear findings. You can:\n"
            "- Search files and directories for relevant information\n"
            "- Read documentation and code to understand systems\n"
            "- Compile findings into structured summaries\n"
            "Always cite your sources (file paths, line numbers) and distinguish facts from inferences."
        ),
        tools=FILE_TOOLS + DIR_TOOLS + SEARCH_TOOLS,
    ),
    "SystemAdmin": AgentProfile(
        name="system_admin",
        description="Executes system commands, manages processes and infrastructure",
        system_message=(
            "You are an experienced system administrator. You manage system operations safely "
            "and efficiently. You can:\n"
            "- Execute shell commands with proper safety checks\n"
            "- Manage files and directories\n"
            "- Monitor system state and processes\n"
            "- Install and configure software\n"
            "Always explain what commands will do before executing them. "
            "Prefer safe, reversible operations. Report command output clearly."
        ),
        tools=ALL_TOOLS,
    ),
    "Debugger": AgentProfile(
        name="debugger",
        description="Investigates and fixes bugs, errors, and failures",
        system_message=(
            "You are an expert debugger. You systematically identify and fix bugs. Your approach:\n"
            "1. Reproduce: Understand the error and its context\n"
            "2. Investigate: Search code, read logs, trace execution paths\n"
            "3. Diagnose: Identify the root cause with evidence\n"
            "4. Fix: Apply the minimal correct fix\n"
            "5. Verify: Test that the fix works\n"
            "Always explain your reasoning and show evidence for your diagnosis."
        ),
        tools=ALL_TOOLS,
    ),
    "General": AgentProfile(
        name="general_assistant",
        description="General-purpose agent for miscellaneous tasks",
        system_message=(
            "You are a capable general-purpose assistant. You handle a variety of tasks "
            "using the tools available to you. Be concise and effective. "
            "Use the most appropriate tools for each task and report results clearly."
        ),
        tools=ALL_TOOLS,
    ),
}


def get_profile(name: str) -> AgentProfile:
    """Get an agent profile by name. Falls back to General if not found."""
    profile = PROFILES.get(name)
    if profile is None:
        profile = PROFILES["General"]
    return profile


def list_profiles() -> list[str]:
    """List all available profile names."""
    return list(PROFILES.keys())
