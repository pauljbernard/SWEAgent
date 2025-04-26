# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
from promptflow.core import tool
import instructor
from google.generativeai import caching
from promptflow.connections import CustomConnection
import google.generativeai as genai
from src.schemas.doc_retriver import GoalRewriteModel
import traceback

from src.monitor.langfuse import get_langfuse_context, trace
import dotenv
import os

dotenv.load_dotenv()

QUERRY_REWRITING_MODEL = os.getenv("QUERRY_REWRITING_MODEL")


def process_batch(
    client_gemini,
    symstem_prompt: str,
    user_prompt: str,
    span=None,
) -> Dict:
    """Process a batch of files using Gemini API"""

    messages = [
        {"role": "system", "content": symstem_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if span:
        generation = span.generation(
            name="gemini",
            model=QUERRY_REWRITING_MODEL,
            model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 8000},
            input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
        )

    try:
        completion, raw = client_gemini.chat.create_with_completion(
            messages=messages,
            response_model=GoalRewriteModel,
            generation_config={
                "temperature": 0.0,
                "top_p": 1,
                "candidate_count": 1,
                "max_output_tokens": 8000,
            },
            max_retries=10,
        )
        result = completion.model_dump()
        # if span:
        #     span.score(name="number_try", value=raw.n_attempts)
    except Exception as e:
        if span:
            generation.end(
                output=None,
                status_message=f"Error processing batch: {str(e)}, {traceback.format_exc()}",
                level="ERROR",
            )
        raise e

    if span:
        generation.end(
            output=result,
            usage={
                "input": raw.usage_metadata.prompt_token_count,
                "output": raw.usage_metadata.candidates_token_count,
            },
        )

    return result


@trace
@tool
def querry_rewritter(
    symstem_prompt: str,
    user_prompt: str,
    GEMINI_API_KEY: str = "",
    ANTHROPIC_API_KEY: str = "",
    OPENAI_API_KEY: str = "",
) -> str:
    span = get_langfuse_context().get("span")

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
            model_name=QUERRY_REWRITING_MODEL, safety_settings=safe
        ),
        mode=instructor.Mode.GEMINI_JSON,
    )

    rewrite = process_batch(client_gemini, symstem_prompt, user_prompt, span)

    return rewrite
