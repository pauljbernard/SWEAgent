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
from src.schemas.doc_retriver import get_necesary_files
import traceback

from src.monitor.langfuse import get_langfuse_context, trace

import dotenv
import os

dotenv.load_dotenv()

CONTEXT_CACHING_RETRIVER = os.getenv("CONTEXT_CACHING_RETRIVER")


def process_batch(
    client_gemini,
    symstem_prompt: str,
    user_prompt: str,
    span=None,
    documentation=None,
    cache_id=None,
) -> Dict:
    """Process a batch of files using Gemini API"""

    messages = [
        {"role": "system", "content": symstem_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Simulate a delay with random jitter
    # delay = random.uniform(0.1, 0.5)
    # time.sleep(delay)

    if span:
        generation = span.generation(
            name="gemini",
            model=CONTEXT_CACHING_RETRIVER,
            model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 8000},
            input={
                "system_prompt": symstem_prompt,
                "user_prompt": cache_id + "\n\n" + user_prompt,
            },
        )

    try:
        completion, raw = client_gemini.chat.create_with_completion(
            messages=messages,
            response_model=get_necesary_files(documentation),
            generation_config={
                "temperature": 0.0,
                "top_p": 1,
                "candidate_count": 1,
                "max_output_tokens": 8000,
            },
            max_retries=5,
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
def context_caching_retrival(
    documentation: dict,
    cache_id: str,
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

    # getting the cached client
    cache = caching.CachedContent.get(cache_id)

    client_gemini = instructor.from_gemini(
        client=genai.GenerativeModel.from_cached_content(
            cached_content=cache, safety_settings=safe
        ),
        mode=instructor.Mode.GEMINI_JSON,
    )

    list_of_files = process_batch(
        client_gemini, symstem_prompt, user_prompt, span, documentation, cache_id
    )

    return list_of_files
