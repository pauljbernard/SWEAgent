from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
import os
from src.core.chat_models import (
    client_8b,
    client_flash,
    client_pro,
    client_exp_pro,
    client_exp_flash,
    get_claude_response,
    get_openai_o4_mini_response
)
import requests
import json
import logging
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure the API key for Google Generative AI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the FastAPI app
app = FastAPI()

# Create a thread pool executor for handling model inference
executor = ThreadPoolExecutor(max_workers=40)

url = "http://libraire:8001/score"

# Define the request and response models
class QueryRequest(BaseModel):
    message: str
    model_name: str
    cache_id: str
    repo_name: str
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = ConfigDict(protected_namespaces=())  # Add this line


class QueryResponse(BaseModel):
    response: str


# Define the endpoint
@app.post("/generate", response_model=QueryResponse)
async def generate_content(request: QueryRequest):
    try:
        # Configure API clients with keys from the request if provided
        if request.GEMINI_API_KEY:
            # Configure Gemini with the provided API key
            import google.generativeai as genai
            genai.configure(api_key=request.GEMINI_API_KEY)
            
            # Define safety settings
            safe = [
                {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Create new client instances with the provided API key
            client_8b_instance = genai.GenerativeModel(
                model_name="gemini-1.5-flash-8b-001",
                safety_settings=safe,
                generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
            )
            
            client_exp_flash_instance = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                safety_settings=safe,
                generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
            )
            
            client_exp_pro_instance = genai.GenerativeModel(
                model_name="gemini-exp-1206",
                safety_settings=safe,
                generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
            )
            
            client_flash_instance = genai.GenerativeModel(
                model_name="gemini-1.5-flash-002",
                safety_settings=safe,
                generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
            )
            
            client_pro_instance = genai.GenerativeModel(
                model_name="gemini-1.5-pro-002",
                safety_settings=safe,
                generation_config={"temperature": 0, "top_p": 1, "max_output_tokens": 8000},
            )
        else:
            # Use the default clients
            client_8b_instance = client_8b
            client_exp_flash_instance = client_exp_flash
            client_exp_pro_instance = client_exp_pro
            client_flash_instance = client_flash
            client_pro_instance = client_pro
        
        # Configure OpenAI client if API key is provided
        if request.OPENAI_API_KEY:
            from openai import OpenAI
            try:
                openai_client = OpenAI(api_key=request.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}\n {traceback.format_exc()}. The api key is %s", request.OPENAI_API_KEY)
        else:
            from openai import OpenAI
            try:
                openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}\n {traceback.format_exc()}. The api key is %s", os.getenv("OPENAI_API_KEY"))
            
        # Configure Anthropic client if API key is provided
        if request.ANTHROPIC_API_KEY:
            from anthropic import Anthropic, Timeout
            anthropic_client = Anthropic(
                timeout=Timeout(
                    60.0 * 30,  # 30 minutes timeout
                    connect=5.0,
                ),
                api_key=request.ANTHROPIC_API_KEY,
            )
        else:
            from anthropic import Anthropic, Timeout
            anthropic_client = Anthropic(
                timeout=Timeout(
                    60.0 * 30,  # 30 minutes timeout
                    connect=5.0,
                ),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
            
        # Generate content using the appropriate model
        if "gemini" in request.model_name:
            # Use asyncio to run the model inference in a separate thread
            if request.model_name == "gemini-exp-1206":
                response = await asyncio.get_event_loop().run_in_executor(
                    executor, client_exp_pro_instance.generate_content, [request.message]
                )
            elif request.model_name == "gemini-2.0-flash-exp":
                response = await asyncio.get_event_loop().run_in_executor(
                    executor, client_exp_flash_instance.generate_content, [request.message]
                )
            elif request.model_name == "gemini-1.5-flash-8b-001":
                response = await asyncio.get_event_loop().run_in_executor(
                    executor, client_8b_instance.generate_content, [request.message]
                )
            elif request.model_name == "gemini-1.5-flash-002":
                response = await asyncio.get_event_loop().run_in_executor(
                    executor, client_flash_instance.generate_content, [request.message]
                )
            elif request.model_name == "gemini-1.5-pro-002":
                response = await asyncio.get_event_loop().run_in_executor(
                    executor, client_pro_instance.generate_content, [request.message]
                )
            return {"response": response.text}

        elif request.model_name == "Claude-3.7-Sonnet-32k-budget":
            # Define a custom function to use the configured client
            def get_openai_response_with_key(prompt):
                response = openai_client.responses.create(
                    model="o3",
                    reasoning={"effort": "high"},
                    input=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.output_text
                
            response = await asyncio.get_event_loop().run_in_executor(
                executor, get_openai_response_with_key, request.message
            )
            return {"response": response}

        elif request.model_name == "Custom Documentalist":
            # Load JSON files asynchronously
            with open(f"/app/docstrings_json/{request.repo_name}.json", "r") as json_file1:
                response_dict = json.load(json_file1)
            with open(
                f"/app/ducomentations_json/{request.repo_name}.json", "r"
            ) as json_file2:
                ducomentations_json = json.load(json_file2)
            with open(f"/app/configs_json/{request.repo_name}.json", "r") as json_file3:
                configs_json = json.load(json_file3)

            # Make the API request with API keys
            response = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: requests.post(
                    url,
                    json={
                        "repository_name": request.repo_name,
                        "documentation": response_dict,
                        "config": configs_json,
                        "documentation_md": ducomentations_json,
                        "cache_id": request.cache_id,
                        "user_problem": request.message,
                        "GEMINI_API_KEY": request.GEMINI_API_KEY,
                        "ANTHROPIC_API_KEY": request.ANTHROPIC_API_KEY,
                        "OPENAI_API_KEY": request.OPENAI_API_KEY,
                    },
                    # timeout=60,  # Add timeout to prevent hanging requests
                ),
            )
            return {"response": response.json()["libraire_response"]}

    except Exception as e:
        logger.error(f"Error generating content: {e}\n {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the app with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8050, workers=4
    )  # Use multiple workers for better concurrency
