import os
import asyncio
from typing import TYPE_CHECKING
import google.generativeai as genai
import openai
import anthropic
import requests
from dotenv import load_dotenv

if TYPE_CHECKING:
    from ..types import VaptState

load_dotenv()

def _blocking_gemini_call(prompt: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    safety_settings = {'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'}
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()

def _blocking_openai_call(prompt: str, api_key: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def _blocking_anthropic_call(prompt: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

def _blocking_ollama_call(prompt: str, model_to_use: str) -> str:
    try:
        response = requests.post(
            'http://127.0.0.1:11434/api/generate',
            json={
                "model": model_to_use,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json().get('response', '').strip()
    except requests.exceptions.ConnectionError as e:
        print(f"\n[✖] Ollama connection failed. Is Ollama running? Error: {e}")
        return ""

async def call_generative_model(prompt: str, state: "VaptState") -> str:
    model_name = state.get("selected_ai_model")
    api_key = state.get("ai_api_key")

    if not api_key and "Ollama" not in model_name:
        print(f"[✖] AI call failed: API key is missing for cloud model {model_name}.")
        return ""

    print(f"[LLM] Routing call to model: {model_name}")

    try:
        if model_name == 'Gemini':
            response_text = await asyncio.to_thread(_blocking_gemini_call, prompt, api_key)

        elif model_name == 'OpenAI (GPT-4)':
            response_text = await asyncio.to_thread(_blocking_openai_call, prompt, api_key)

        elif model_name == 'Anthropic (Claude 3 Sonnet)':
            response_text = await asyncio.to_thread(_blocking_anthropic_call, prompt, api_key)

        elif model_name == 'Ollama (Llama3)':
            response_text = await asyncio.to_thread(_blocking_ollama_call, prompt, "llama3")

        else:
            print(f"[✖] Unknown AI model selected: {model_name}")
            return ""

        if not response_text:
            print("[⚠] AI model returned an empty response.")
            return ""

        return response_text

    except Exception as e:
        print(f"\n[✖] Critical error in AI model call for {model_name}: {e}")
        return ""
