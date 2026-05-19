import logging
import time
from typing import Dict, Any, List

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# --- In-memory storage for agent insights ---

class GeminiStorage:
    """Simple in-memory storage for agent insights and remapping states."""
    _latest_insights = None
    _remap_state = {
        "status": "idle",
        "message": "System ready.",
        "logs": ["Remapper agent initialized."],
        "data": None
    }

    @classmethod
    def update(cls, data: Dict[str, Any]):
        cls._latest_insights = data

    @classmethod
    def get(cls):
        return cls._latest_insights

    @classmethod
    def update_remap(cls, status: str, message: str, logs: list = None, data: Dict[str, Any] = None):
        cls._remap_state["status"] = status
        cls._remap_state["message"] = message
        if logs is not None:
            cls._remap_state["logs"] = logs
        if data is not None:
            cls._remap_state["data"] = data

    @classmethod
    def add_remap_log(cls, log_line: str):
        if "logs" not in cls._remap_state or cls._remap_state["logs"] is None:
            cls._remap_state["logs"] = []
        cls._remap_state["logs"].append(log_line)
        cls._remap_state["message"] = log_line

    @classmethod
    def get_remap(cls):
        return cls._remap_state


# --- ADK Tool Function ---

def submit_repository_insights(
    architecture_overview: str,
    architecture_patterns: list[str],
    hardware_mapping: str,
    control_flow: str,
    communication_protocols: list[str],
    risks: list[str],
    onboarding_pitch: str,
) -> str:
    """
    Tool for the Gemini agent to submit engineering insights discovered during
    repository analysis. Call this tool when you have finished reasoning
    through the codebase.

    Args:
        architecture_overview: A 2-3 sentence summary of the overall architecture.
        architecture_patterns: List of architectural patterns detected.
        hardware_mapping: Description of detected hardware targets and boards.
        control_flow: Description of the main execution loop or pipeline.
        communication_protocols: List of communication protocols found.
        risks: List of technical risks and security concerns.
        onboarding_pitch: A 2-3 sentence quick-start guide for a new developer.

    Returns:
        A confirmation message.
    """
    insights = {
        "metadata": {
            "engine": "Google Gemini (ADK Agent)",
            "timestamp": time.time(),
            "status": "success",
        },
        "insights": {
            "architecture": {
                "overview": architecture_overview,
                "patterns": architecture_patterns,
                "tech_stack": ["Detected by Gemini"],
            },
            "hardware_mapping": {
                "resource_utilization": hardware_mapping,
                "deployment_targets": ["Live Detection"],
                "io_strategy": "Async detected",
            },
            "control_flow": {
                "primary_pipeline": control_flow,
                "error_handling": "Inferred from code",
            },
            "communication": {
                "internal": "Real-time discovery",
                "external": "Real-time discovery",
                "protocols": communication_protocols,
            },
            "risks": risks,
            "onboarding_summary": {
                "tldr": onboarding_pitch,
                "quick_start": "Follow the agent's guidance.",
                "key_files": ["Analyzed by Gemini"],
            },
        },
    }

    GeminiStorage.update(insights)
    return "Insights successfully pushed to the Repository Analyzer UI."


# --- ADK Agent Definition ---

AGENT_MODEL = "gemini-3.1-flash-lite"

root_agent = Agent(
    model=AGENT_MODEL,
    name="hobbyt_analyzer",
    description="A robotics repository analysis agent powered by Google Gemini.",
    instruction="""You are an expert robotics software engineer. When asked to
analyze a repository, perform a comprehensive engineering audit covering:
1. Architectural patterns and structural integrity.
2. Hardware dependencies and resource mapping.
3. Critical control flow and state management.
4. Communication protocols and data flow.
5. Technical risks and security debt.

After your analysis, use the 'submit_repository_insights' tool to push your
findings to the visualization UI.""",
    tools=[submit_repository_insights],
)


# --- Analyzer Class (used by FastAPI as fallback) ---

class GeminiAnalyzer:
    """
    Google Gemini Analysis Service — coordinates with the ADK agent and
    provides fallback logic for the FastAPI endpoints.
    """

    def __init__(self):
        self.logger = logging.getLogger("GeminiAnalyzer")

    async def analyze_repo_fallback(self, repo_name: str, file_list: list) -> dict:
        """
        Fallback analysis for when the agent isn't providing real-time data.
        """
        stored = GeminiStorage.get()
        if stored:
            return stored

        return {
            "metadata": {"engine": "Google Gemini Fallback", "status": "waiting"},
            "insights": None,
            "message": "Waiting for real-time insights from the Gemini agent. "
                       "Please use the agent to analyze the repo.",
        }


if __name__ == "__main__":
    # When run directly, start the ADK agent in interactive CLI mode
    import asyncio
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    async def main():
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="hobbyt_analyzer",
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name="hobbyt_analyzer", user_id="cli_user"
        )

        print(f"Hobbyt Analyzer Agent started (model: {AGENT_MODEL})")
        print("Type your message (or 'quit' to exit):\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit"):
                break

            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)],
            )
            response_text = ""
            async for event in runner.run_async(
                user_id="cli_user",
                session_id=session.id,
                new_message=content,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    response_text = event.content.parts[0].text

            print(f"Agent: {response_text}\n")

    asyncio.run(main())
