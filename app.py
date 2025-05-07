"""
Entry point for the Assort Health Voice Agent.
This file runs the LiveKit agent directly.
"""
import os
from dotenv import load_dotenv
from livekit import agents
from src.agent.livekit_agent import entrypoint
from src.utils.logger import logger

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Run the LiveKit agent directly
    # This will start the agent and listen for incoming calls
    logger.info("Starting Assort Health Voice Agent")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
