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
import traceback
import anthropic
import tiktoken
from src.monitor.langfuse import get_langfuse_context, trace
from src.core.chat_models import  get_claude_response, get_gemini_pro_25_response
import traceback
import logging

logger = logging.getLogger(__name__)




import dotenv
import os


dotenv.load_dotenv()

FINAL_ANSWER_GENERATOR = os.getenv("FINAL_ANSWER_GENERATOR")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# function to count the number of token in a string, using the tiktoken library
def count_tokens(text: str, encoding_name: str = "o200k_base") -> int:
    """
    Counts the number of tokens in a string using a specified tiktoken encoding.

    Args:
        text: The string to tokenize.
        encoding_name: The name of the tiktoken encoding to use.
                       Common options include:
                           - "gpt2" (for models like text-davinci-003)
                           - "r50k_base" (for older models)
                           - "p50k_base" (for code models like Codex)
                           - "cl100k_base" (for newer models like GPT-3.5-turbo, GPT-4)

    Returns:
        The number of tokens in the string.
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except KeyError:
        print(
            f"Error: Encoding '{encoding_name}' not found. Please provide a valid encoding name."
        )
        return -1  # Indicate an error


import os

current_dir = os.getcwd()


@trace
@tool
def answer_user_querry_with_context(
    files_list: dict,
    files_list_md_config: dict,
    documentation: dict,
    documentation_md: dict,
    config: dict,
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

    # Configure Anthropic client with API key from request if provided
    if ANTHROPIC_API_KEY:
        client_claude = anthropic.Client(api_key=ANTHROPIC_API_KEY)
    else:
        # Use default API key from environment
        client_claude = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Get file names from the documentation : files_list_md_config
    for file in files_list_md_config:
        file_id = int(file["file_id"])
        file_name = file["file_name"]
        if ".md" in file_name:
            path = documentation_md["documentation_md"][file_id]["file_paths"]
            try:
                with open(path, "r") as f:
                    symstem_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
            except:
                # raise Exception(
                #     f"Error while reading the file {path}, {traceback.format_exc()}"
                # )
                pass
        else:
            try:
                path = config["config"][file_id]["file_paths"]
                with open(path, "r") as f:
                    symstem_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
            except:
                # raise Exception(
                #     f"Error while reading the file {path}, {traceback.format_exc()}"
                # )
                pass
    # Get file names from the documentation : files_list
    for file in files_list:
        file_id = int(file["file_id"])
        file_name = file["file_name"]
        path = documentation["documentation"][file_id]["file_paths"]
        try:
            with open(path, "r") as f:
                user_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
        except:
            raise Exception(
                f"Error while reading the file {path}, {traceback.format_exc()}"
            )

    # # getting the cached client
    # cache = caching.CachedContent.get(cache_id)

    # client_gemini = genai.GenerativeModel.from_cached_content(
    #     cached_content=cache, safety_settings=safe
    # )

    # Answer = client_gemini.generate_content([(symstem_prompt + "\n" + user_prompt)])

    # if span:
    #     generation.end(
    #         output=Answer.text,
    #         usage={
    #             "input": Answer.usage_metadata.prompt_token_count,
    #             "output": Answer.usage_metadata.candidates_token_count,
    #         },
    #     )
    # return Answer.text
    messages = []

    # Add system prompt if provided

    # Add user message
    try:
        raise Exception("test")


        if span:
            generation = span.generation(
                name="claude",
                model="claude-3-7-sonnet-20250219",
                model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 20000},
                input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
            )

        messages.append({"role": "user", "content": user_prompt})
        
        # Use custom function to pass API key for Claude
        if ANTHROPIC_API_KEY:
            # Create a custom Anthropic client with the provided API key
            custom_client = anthropic.Client(
                timeout=anthropic.Timeout(
                    60.0 * 30,  # 30 minutes timeout
                    connect=5.0,
                ),
                api_key=ANTHROPIC_API_KEY,
            )
            
            # Generate response with the custom client
            Answer = custom_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=64000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 32000,  # Maximum recommended thinking budget
                },
                system=symstem_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ] 
            )
        else:
            # Use the default function
            Answer = get_claude_response(system_prompt=symstem_prompt, user_prompt=user_prompt)

        if span:
            try:
                generation.end(
                    output=Answer.content[1].text,
                    usage={
                        "input": Answer.usage.input_tokens,
                        "output": Answer.usage.output_tokens,
                    },
                )
            except Exception as e:
                generation.end(
                    output=Answer.content[1].text,
                    usage={
                        "input": 0,
                        "output": 0,
                    },
                )
                logger.error(f"Error while answering the user querry, {e}, traceback: {traceback.format_exc()}")

        return Answer.content[1].text
    except Exception as e:
        logger.error(f"Error while answering the user querry, {e}, traceback: {traceback.format_exc()}")
        # #use openai gpt4o
        # if span:
        #     generation.end(
        #         output=f"Error message: {e}, traceback: {traceback.format_exc()}",
        #         usage={
        #             "input": 0,
        #             "output": 0,
        #         },
        #     )
        # if span:
        #     generation = span.generation(
        #         name="gpt4.1",
        #         model="gpt-4.1",
        #         model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 60000},
        #         input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
        #     )

        # Answer = get_openai_gpt4_1_response(system_prompt=symstem_prompt, user_prompt=user_prompt)
        # if span:
        #     generation.end(
        #         output=Answer.choices[0].message.content,
        #         usage={
        #             "input": Answer.usage.prompt_tokens,
        #             "output": Answer.usage.completion_tokens,
        #         },
        #     )
        # return Answer.choices[0].message.content
        if span:
            generation = span.generation(
                name="gemini",
                model="gemini-2.5-pro-preview-03-25",
                model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 60000},
                input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
            )

        # Use custom function to pass API key
        if GEMINI_API_KEY:
            # Configure Gemini with the provided API key
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Create a new client instance with the provided API key
            client_25pro_preview = genai.GenerativeModel(
                model_name="gemini-2.5-pro-preview-03-25",
                safety_settings=safe,
                generation_config={"temperature": 0.95, "top_p": 1, "max_output_tokens": 60000},
            )
            
            # Generate response with the custom client
            Answer = client_25pro_preview.generate_content(symstem_prompt + "\n" + user_prompt)
        else:
            # Use the default function
            Answer = get_gemini_pro_25_response(symstem_prompt + "\n" + user_prompt)

        if span:
            generation.end(
                output=f"# {FINAL_ANSWER_GENERATOR} \n" + Answer.text,
                usage={
                    "input": Answer.usage_metadata.prompt_token_count,
                    "output": Answer.usage_metadata.candidates_token_count,
                },
            )
        return Answer.text
