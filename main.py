import os
import uuid
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Custom Agent Imports ---
from air import DistillerClient
from custom import executor_dict # Import the agent logic

# --- Initial Setup ---
load_dotenv()
api_key = str(os.getenv("API_KEY"))
project_name = "recommender_project"

# Initialize the Distiller Client and create the project on startup
print(f"Initializing DistillerClient for project: {project_name}")
distiller_client = DistillerClient(api_key=api_key)
# It's better to ensure the project exists rather than creating it on every startup
# In a production scenario, project creation would be a separate, one-time step.
try:
    distiller_client.create_project(config_path="config.yaml", project=project_name)
    print(f"Project '{project_name}' created or already exists.")
except Exception as e:
    # Handle cases where the project might already exist gracefully
    if "already exists" in str(e):
        print(f"Project '{project_name}' already exists.")
    else:
        print(f"An error occurred during project setup: {e}")
        raise

# --- FastAPI Application ---
app = FastAPI(
    title="Custom Agent Server",
    description="A FastAPI server to interact with the Recommender AIR agent via SSE.",
)

# --- Pydantic Models for Request Bodies ---
class QueryRequest(BaseModel):
    """Defines the body for sending a query to the agent."""
    query: str

# --- API Endpoints ---
@app.post("/agent/query")
async def agent_query_stream(request: Request, body: QueryRequest):
    """
    Accepts a query and streams responses from the Recommender agent via SSE.
    
    - **query**: The natural language query to send to the agent.
    """
    
    async def event_generator():
        """
        The async generator that handles the agent query and yields SSE events.
        """
        user_id = f"user-{uuid.uuid4()}"
        
        try:
            # Yield status updates in SSE format
            yield f"event: status\ndata: {json.dumps(f'Connecting to project {project_name} for user {user_id}...')}\n\n"
            
            # Use the async context manager for the DistillerClient
            async with distiller_client(
                project=project_name,
                uuid=user_id,
                executor_dict=executor_dict
            ) as dc:
                
                yield f"event: status\ndata: {json.dumps('Connection successful. Sending query...')}\n\n"
                
                # Send the query to the agent
                responses = await dc.query(query=body.query)
                
                # Stream responses back to the client
                async for response in responses:
                    if await request.is_disconnected():
                        print("Client disconnected, stopping stream.")
                        break
                    
                    # Serialize the Pydantic object to JSON and format as a valid SSE message
                    yield f"event: message\ndata: {response.model_dump_json()}\n\n"
            
            yield f"event: close\ndata: {json.dumps('Stream finished.')}\n\n"
        except Exception as e:
            print(f"An error occurred during query stream: {e}")
            import traceback
            traceback.print_exc()
            error_message = f"An unexpected server error occurred: {type(e).__name__}"
            # Yield the error message in SSE format
            yield f"event: error\ndata: {json.dumps(error_message)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {
        "message": f"Custom Agent Server is running. Loaded project: '{project_name}'. POST to /agent/query to interact."
    }

