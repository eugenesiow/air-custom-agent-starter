import os
from air import AsyncAIRefinery
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
api_key = str(os.getenv("API_KEY"))

async def recommender_agent(query: str) -> str:
    """
    A custom agent that provides recommendations based on a user query.

    Args:
        query: The user's request for a recommendation.

    Returns:
        A string containing the recommendation and a justification.
    """
    prompt = """Given the query below, your task is to provide the user with a useful and cool
       recommendation followed by a one-sentence justification.\n\nQUERY: {query}"""

    formatted_prompt = prompt.format(query=query)

    # Initialize the AIRefinery client to interact with the LLM
    airefinery_client = AsyncAIRefinery(api_key=api_key)

    # Call the chat completions API
    response = await airefinery_client.chat.completions.create(
        messages=[{"role": "user", "content": formatted_prompt}],
        model="meta-llama/Llama-3.1-70B-Instruct",
    )

    return response.choices[0].message.content

# This dictionary maps the agent name from config.yaml to its function
executor_dict = {"Recommender Agent": recommender_agent}
