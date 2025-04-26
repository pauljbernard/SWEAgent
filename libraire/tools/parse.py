# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
from promptflow.core import tool
import instructor
from promptflow.connections import CustomConnection
import google.generativeai as genai
from src.schemas.doc_retriver import get_necesary_files

import time
import random

from src.monitor.langfuse import get_langfuse_context, trace
import dotenv
import os

dotenv.load_dotenv()

DOCUMENTATION_CONTEXT_RETRIVER = os.getenv("DOCUMENTATION_CONTEXT_RETRIVER")


@trace
@tool
def documentation_context_retriver(
    symstem_prompt: str,
    user_prompt: str,
    max_workers: int = 10,  # Number of parallel workers
    config_doc: dict = None,
    documentation_md: dict = None,
    GEMINI_API_KEY: str = "",
    ANTHROPIC_API_KEY: str = "",
    OPENAI_API_KEY: str = "",
) -> str:
    span = get_langfuse_context().get("span")
    # if span:
    #     span.set("batch_size", batch_size)
    #     span.set("max_workers", max_workers)
    scores = [0]
    # Load documentations md and configs
    documentation = []

    documentation_md = documentation_md.get("documentation_md")
    config_doc = config_doc.get("config")
    if documentation_md and documentation_md[0] != {}:
        documentation = documentation + documentation_md
        if config_doc and config_doc[0] != {}:
            documentation = documentation + config_doc

    for index, doc in enumerate(documentation):
        doc["file_id"] = index

    user_prompt = user_prompt.replace("FILES_HERE", str(documentation))

    if len(documentation) == 0:
        return {"files_list": []}
    # Configure safety settings
    safe = [
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # Configure Gemini with API key from request if provided
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        # Use default API key from environment
        genai.configure()
        
    client_gemini = instructor.from_gemini(
        client=genai.GenerativeModel(
            model_name=DOCUMENTATION_CONTEXT_RETRIVER, safety_settings=safe
        ),
        mode=instructor.Mode.GEMINI_JSON,
    )

    # Process batches in parallel
    messages = [
        {"role": "system", "content": symstem_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Simulate a delay with random jitter
    delay = random.uniform(0.1, 0.5)
    time.sleep(delay)

    if span:
        generation = span.generation(
            name="gemini",
            model=DOCUMENTATION_CONTEXT_RETRIVER,
            model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 8000},
            input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
        )

    try:
        completion, raw = client_gemini.chat.create_with_completion(
            messages=messages,
            response_model=get_necesary_files({"documentation": documentation}),
            generation_config={
                "temperature": 0.0,
                "top_p": 1,
                "candidate_count": 1,
                "max_output_tokens": 8000,
            },
            max_retries=10,
        )
        result = completion.model_dump()

    except Exception as e:
        if span:
            generation.end(
                output=None,
                status_message=f"Error processing batch: {str(e)}",
                level="ERROR",
            )

    if span:
        generation.end(
            output=result,
            usage={
                "input": raw.usage_metadata.prompt_token_count,
                "output": raw.usage_metadata.candidates_token_count,
            },
        )

    return result
