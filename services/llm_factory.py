from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from google import genai
from config import Config
import time
import requests

class LLMFactory:
    @staticmethod
    def get_llm(provider_name: str):
        """Returns the appropriate LLM provider with fallback logic"""

        # ------------------ OPENAI ------------------
        if provider_name == "openai":
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=Config.OPENAI_API_KEY,
                temperature=0.7
            )

        # ------------------ OLLAMA ------------------
        elif provider_name == "ollama":
            return ChatOllama(
                base_url=Config.OLLAMA_BASE_URL,
                model=Config.OLLAMA_MODEL,
                temperature=0.7
            )

        # ------------------ NVIDIA NIM (NEW) ------------------
        elif provider_name == "nvidia":
            from openai import OpenAI

            class NVIDIAWrapper:
                def __init__(self):
                    # Using the OpenAI client pointed to NVIDIA's NIM infrastructure
                    self.client = OpenAI(
                        base_url="https://integrate.api.nvidia.com/v1",
                        api_key=Config.NVIDIA_API_KEY or ""
                    )
                    self.model = "mistralai/mistral-medium-3.5-128b"

                def invoke(self, messages):
                    # Convert LangChain messages to NVIDIA/OpenAI format
                    nv_messages = []
                    for msg in messages:
                        role = "user" if msg.type == "human" else "assistant"
                        if msg.type == "system": role = "system"
                        nv_messages.append({"role": role, "content": msg.content})

                    class MockLangChainResponse:
                        def __init__(self, text): self.content = text

                    try:
                        completion = self.client.chat.completions.create(
                            model=self.model,
                            messages=nv_messages,
                            temperature=0.7,
                            max_tokens=4096, # Optimized for chat
                        )
                        return MockLangChainResponse(completion.choices[0].message.content)
                    except Exception as e:
                        return MockLangChainResponse(f"NVIDIA API Error: {str(e)}")

            return NVIDIAWrapper()

        # ------------------ OPENROUTER (ENHANCED) ------------------
        elif provider_name == "openrouter":
            from openai import OpenAI

            class ModernOpenRouterWrapper:
                def __init__(self):
                    self.client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=Config.OPENROUTER_API_KEY or "",
                        timeout=15.0
                    )
                    self.models = [
                        "tencent/hy3-preview:free",
                        "openai/gpt-oss-120b:free",
                        "nvidia/nemotron-3-super-120b-a12b:free",
                        "openrouter/free"
                    ]
                    self.max_retries = 2

                def _convert_messages(self, messages):
                    converted = []
                    for msg in messages[-6:]:
                        role = "user" if msg.type == "human" else "assistant"
                        if msg.type == "system": role = "system"
                        converted.append({"role": role, "content": msg.content})
                    return converted

                def invoke(self, messages):
                    or_messages = self._convert_messages(messages)
                    class MockLangChainResponse:
                        def __init__(self, text): self.content = text

                    for model in self.models:
                        for attempt in range(self.max_retries):
                            try:
                                completion = self.client.chat.completions.create(
                                    model=model,
                                    messages=or_messages,
                                    extra_headers={
                                        "HTTP-Referer": "http://localhost:5000",
                                        "X-OpenRouter-Title": "CareerAI Pro",
                                    }
                                )
                                return MockLangChainResponse(completion.choices[0].message.content)
                            except Exception as e:
                                print(f"[OpenRouter] Model {model} failed: {e}")
                                time.sleep(0.5)
                    return MockLangChainResponse("⚠️ All OpenRouter models failed.")

            return ModernOpenRouterWrapper()

        # ------------------ GEMINI ------------------
        elif provider_name == "gemini":
            class ModernGeminiWrapper:
                def __init__(self):
                    self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
                    self.model = "gemini-2.0-flash-exp:free"

                def invoke(self, messages):
                    prompt_text = ""
                    for msg in messages:
                        prompt_text += f"{msg.type.capitalize()}: {msg.content}\n\n"

                    class MockLangChainResponse:
                        def __init__(self, text): self.content = text

                    try:
                        response = self.client.models.generate_content(
                            model=self.model,
                            contents=prompt_text
                        )
                        return MockLangChainResponse(response.text)
                    except Exception as e:
                        return MockLangChainResponse(f"Google GenAI API Error: {str(e)}")

            return ModernGeminiWrapper()

        else:
            raise ValueError(f"Unknown provider: {provider_name}")