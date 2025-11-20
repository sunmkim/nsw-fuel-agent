import os
from dotenv import load_dotenv
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager
from bedrock_agentcore.memory.session import MemorySession

load_dotenv()


def create_memory_resource(memory_name: str, region: str = os.getenv("AWS_REGION")):
    # create short-term memory resource that will be shared between our subagents
    try:
        memory_manager = MemoryManager(region_name=region)
        print(f"Creating memory '{memory_name}' for short-term conversational storage...")
        memory = memory_manager.get_or_create_memory(
            name=memory_name,
            description="Shared memory store between fuel_price_assistant and directions_assistant",
            strategies=[],  # no strategies needed for short-term memory
            event_expiry_days=7,
            memory_execution_role_arn=None
        )
        memory_id = memory.id
        print("✅ Memory successfully created!")
        print(f"- Memory Name: {memory_name}")
        print(f"- Memory Id: {memory_id}")
        print(f"- Memory Status: {memory.status}")
        return memory
    except Exception as err:
        print(f"❌ Memory creation failed:\n {err}")
        print(f"Error type: {type(err).__name__}")
        # Cleanup on error - delete the memory if it was partially created
        if 'memory_id' in locals():
            try:
                print(f"Attempting cleanup of partially created memory: {memory_id}")
                memory_manager.delete_memory(memory_id)
                print(f"✅ Successfully cleaned up memory: {memory_id}")
            except Exception as cleanup_error:
                print(f"❌ Failed to clean up memory: {cleanup_error}")
        
        # Re-raise the original exception
        raise


def create_memory_session(
        actor_id: str, 
        session_id: str, 
        memory_session_manager: str, 
    ) -> MemorySession:
  
    # Create memory session for the specific actor/session combination
    memory_session = memory_session_manager.create_memory_session(
        actor_id=actor_id, 
        session_id=session_id
    )

    print(f"✅ Memory session created for actor: {actor_id}, and session: {session_id}")
    return memory_session