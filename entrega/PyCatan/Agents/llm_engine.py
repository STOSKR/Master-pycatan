from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import glob
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request

from PyCatan.Agents.llm_prompts import build_llm_messages


class ProviderError(RuntimeError):
    pass


@dataclass
class LLMGeneration:
    text: str
    raw_response: Dict[str, Any]
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass
class DecisionOutcome:
    decision_name: str
    selected_index: int
    selected_action: Dict[str, Any]
    used_fallback: bool
    reason: str
    prompt_variant: str
    provider: str
    model: str
    latency_ms: int
    raw_response: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]


class BaseLLMProvider(ABC):
    provider_name: str
    model: str

    @abstractmethod
    def generate(
        self, system_prompt: str, user_prompt: str, timeout_seconds: float
    ) -> LLMGeneration:
        raise NotImplementedError


def _post_json(
    url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_seconds: float
) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url=url, data=data, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code} calling {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Network error calling {url}: {exc}") from exc


class OllamaProvider(BaseLLMProvider):
    provider_name = "ollama"

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        cli_path: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.cli_path = cli_path.strip() if cli_path else ""
        self._resolved_cli_path: Optional[str] = None

    def _candidate_cli_paths(self) -> List[str]:
        candidates: List[str] = []

        env_cli = os.getenv("CATAN_OLLAMA_CLI_PATH", "").strip()
        if env_cli:
            candidates.append(env_cli)

        if self.cli_path:
            candidates.append(self.cli_path)

        candidates.append("ollama")

        user_profile = os.getenv("USERPROFILE", "").strip()
        if user_profile:
            candidates.append(
                os.path.join(
                    user_profile, "AppData", "Local", "Programs", "Ollama", "ollama.exe"
                )
            )

        candidates.extend(
            glob.glob("/mnt/c/Users/*/AppData/Local/Programs/Ollama/ollama.exe")
        )

        # Preserve order while removing duplicates.
        deduped: List[str] = []
        seen = set()
        for item in candidates:
            normalized = item.strip()
            if normalized and normalized not in seen:
                deduped.append(normalized)
                seen.add(normalized)
        return deduped

    def _resolve_cli_path(self) -> Optional[str]:
        if self._resolved_cli_path:
            return self._resolved_cli_path

        for candidate in self._candidate_cli_paths():
            if os.path.isabs(candidate):
                if os.path.exists(candidate):
                    self._resolved_cli_path = candidate
                    return candidate
                continue

            executable = shutil.which(candidate)
            if executable:
                self._resolved_cli_path = executable
                return executable

        return None

    def _generate_via_cli(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float,
    ) -> Optional[LLMGeneration]:
        cli = self._resolve_cli_path()
        if not cli:
            return None

        combined_prompt = (
            f"System instructions:\n{system_prompt}\n\n"
            f"User payload (JSON):\n{user_prompt}\n\n"
            "Return only JSON with action_index."
        )

        try:
            completed = subprocess.run(
                [cli, "run", self.model],
                input=combined_prompt,
                text=True,
                capture_output=True,
                timeout=max(1.0, timeout_seconds),
            )
        except Exception:
            return None

        if completed.returncode != 0:
            return None

        text = (completed.stdout or "").strip()
        if not text:
            return None

        return LLMGeneration(
            text=text,
            raw_response={
                "transport": "ollama_cli",
                "stderr": (completed.stderr or "")[-2000:],
            },
            input_tokens=None,
            output_tokens=None,
        )

    def generate(
        self, system_prompt: str, user_prompt: str, timeout_seconds: float
    ) -> LLMGeneration:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            response_json = _post_json(
                url=f"{self.base_url}/api/chat",
                payload=payload,
                headers={"Content-Type": "application/json"},
                timeout_seconds=timeout_seconds,
            )
        except ProviderError:
            fallback_generation = self._generate_via_cli(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout_seconds=timeout_seconds,
            )
            if fallback_generation is None:
                raise
            return fallback_generation

        message = response_json.get("message", {})
        text = message.get("content", "")

        return LLMGeneration(
            text=text,
            raw_response=response_json,
            input_tokens=response_json.get("prompt_eval_count"),
            output_tokens=response_json.get("eval_count"),
        )


class UPVProvider(BaseLLMProvider):
    provider_name = "upv"

    def __init__(self, model: str, chat_endpoint: str, api_key: str):
        self.model = model
        self.chat_endpoint = chat_endpoint
        self.api_key = api_key

    def generate(
        self, system_prompt: str, user_prompt: str, timeout_seconds: float
    ) -> LLMGeneration:
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        response_json = _post_json(
            url=self.chat_endpoint,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout_seconds=timeout_seconds,
        )

        choices = response_json.get("choices", [])
        if not choices:
            raise ProviderError(f"UPV response has no choices: {response_json}")

        text = choices[0].get("message", {}).get("content", "")
        usage = response_json.get("usage", {})

        return LLMGeneration(
            text=text,
            raw_response=response_json,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )


class BedrockProvider(BaseLLMProvider):
    provider_name = "bedrock"

    def __init__(self, model: str, region_name: str = "eu-west-1"):
        self.model = model
        self.region_name = region_name

        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise ProviderError("boto3 is required for BedrockProvider") from exc

        self._client = boto3.client("bedrock-runtime", region_name=region_name)

    def generate(
        self, system_prompt: str, user_prompt: str, timeout_seconds: float
    ) -> LLMGeneration:
        # boto3 handles timeout via config; this method keeps a compatible signature.
        response_json = self._client.converse(
            modelId=self.model,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_prompt}],
                }
            ],
            inferenceConfig={"temperature": 0.1, "maxTokens": 250},
        )

        content = response_json.get("output", {}).get("message", {}).get("content", [])
        text = ""
        if content and isinstance(content, list):
            text = content[0].get("text", "")

        usage = response_json.get("usage", {})

        return LLMGeneration(
            text=text,
            raw_response=response_json,
            input_tokens=usage.get("inputTokens"),
            output_tokens=usage.get("outputTokens"),
        )


def _looks_like_aws_access_key_id(value: str) -> bool:
    normalized = (value or "").strip()
    return normalized.startswith("AKIA") or normalized.startswith("ASIA")


def _prepare_bedrock_credentials_from_env() -> None:
    """
    Supports two Bedrock auth modes:
    1) Standard AWS credentials (access key id + secret + optional session token).
    2) Bearer token mode used in class labs via AWS_BEARER_TOKEN_BEDROCK.
    """
    catan_access = os.getenv("CATAN_AWS_ACCESS_KEY", "").strip()
    catan_secret = os.getenv("CATAN_AWS_SECRET_KEY", "").strip()
    catan_session = os.getenv("CATAN_AWS_SESSION_TOKEN", "").strip()

    if catan_access:
        if _looks_like_aws_access_key_id(catan_access):
            os.environ.setdefault("AWS_ACCESS_KEY_ID", catan_access)
        else:
            # Lab mode (single Bedrock bearer key).
            os.environ.setdefault("AWS_BEARER_TOKEN_BEDROCK", catan_access)

    if catan_secret:
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", catan_secret)
    if catan_session:
        os.environ.setdefault("AWS_SESSION_TOKEN", catan_session)

    bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    access_id = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

    # If bearer mode is present and key-id is partial/misaligned, prefer bearer mode.
    if bearer and access_id and not secret:
        os.environ.pop("AWS_ACCESS_KEY_ID", None)


def _looks_like_url(value: str) -> bool:
    normalized = (value or "").strip().lower()
    return normalized.startswith("http://") or normalized.startswith("https://")


def _normalize_upv_chat_endpoint(value: str) -> str:
    candidate = (value or "").strip().strip('"').strip("'")
    if not candidate:
        return ""
    if candidate.endswith("/chat/completions"):
        return candidate
    return candidate.rstrip("/") + "/chat/completions"


def _resolve_upv_api_key() -> str:
    """
    Resolves UPV API key from preferred env var and accepted alias.
    Priority:
    1) CATAN_UPV_API_KEY
    2) API_UPV (only if it does not look like an URL)
    """
    canonical = os.getenv("CATAN_UPV_API_KEY", "").strip()
    if canonical:
        return canonical

    alias = os.getenv("API_UPV", "").strip()
    if alias and not _looks_like_url(alias):
        # Keep downstream tooling consistent once alias is used.
        os.environ.setdefault("CATAN_UPV_API_KEY", alias)
        return alias

    return ""


def _resolve_upv_chat_endpoint() -> str:
    """
    Resolves UPV chat endpoint from preferred env var and accepted alias.
    Priority:
    1) CATAN_UPV_CHAT_ENDPOINT
    2) API_UPV (if it looks like an URL, interpreted as base URL)
    """
    canonical = os.getenv("CATAN_UPV_CHAT_ENDPOINT", "").strip()
    if canonical:
        normalized = _normalize_upv_chat_endpoint(canonical)
        os.environ.setdefault("CATAN_UPV_CHAT_ENDPOINT", normalized)
        return normalized

    alias = os.getenv("API_UPV", "").strip()
    if alias and _looks_like_url(alias):
        normalized = _normalize_upv_chat_endpoint(alias)
        os.environ.setdefault("CATAN_UPV_CHAT_ENDPOINT", normalized)
        return normalized

    return ""


def build_provider_from_env() -> Optional[BaseLLMProvider]:
    provider = os.getenv("CATAN_LLM_PROVIDER", "").strip().lower()
    model = os.getenv("CATAN_LLM_MODEL", "").strip()

    if not provider:
        return None

    if provider == "ollama":
        if not model:
            model = "llama3.1:8b"
        base_url = os.getenv("CATAN_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        return OllamaProvider(model=model, base_url=base_url)

    if provider == "upv":
        chat_endpoint = _resolve_upv_chat_endpoint()
        api_key = _resolve_upv_api_key()
        if not (chat_endpoint and api_key and model):
            raise ProviderError(
                "UPV provider requires CATAN_LLM_MODEL and both auth+endpoint: "
                "CATAN_UPV_API_KEY plus CATAN_UPV_CHAT_ENDPOINT, "
                "or API_UPV as compatible alias"
            )
        return UPVProvider(model=model, chat_endpoint=chat_endpoint, api_key=api_key)

    if provider == "bedrock":
        if not model:
            raise ProviderError("Bedrock provider requires CATAN_LLM_MODEL")
        _prepare_bedrock_credentials_from_env()
        region = os.getenv("CATAN_BEDROCK_REGION", "eu-west-1")
        return BedrockProvider(model=model, region_name=region)

    raise ProviderError(f"Unsupported CATAN_LLM_PROVIDER value: {provider}")


def _extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    trimmed = text.strip()
    if not trimmed:
        return None

    try:
        parsed = json.loads(trimmed)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start_positions = [index for index, char in enumerate(trimmed) if char == "{"]
    for start in start_positions:
        depth = 0
        in_string = False
        escaping = False
        for end in range(start, len(trimmed)):
            char = trimmed[end]

            if in_string:
                if escaping:
                    escaping = False
                elif char == "\\":
                    escaping = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = trimmed[start : end + 1]
                    try:
                        parsed = json.loads(candidate)
                    except json.JSONDecodeError:
                        break
                    if isinstance(parsed, dict):
                        return parsed
                    break

    return None


def _extract_action_index_relaxed(text: str) -> Optional[int]:
    if not text:
        return None

    stripped = text.strip()
    if stripped.isdigit():
        try:
            return int(stripped)
        except ValueError:
            pass

    patterns = [
        r'"action_index"\s*[:=]\s*"?(\d+)"?',
        r"\baction_index\b\s*(?:is|=|:)\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    numbers = re.findall(r"\b\d+\b", stripped)
    if len(numbers) == 1 and len(stripped) <= 120:
        try:
            return int(numbers[0])
        except ValueError:
            return None

    return None


class LLMDecisionEngine:
    def __init__(
        self, provider: Optional[BaseLLMProvider], default_timeout_seconds: float = 8.0
    ):
        self.provider = provider
        self.default_timeout_seconds = default_timeout_seconds

    @property
    def is_enabled(self) -> bool:
        return self.provider is not None

    def decide_action(
        self,
        decision_name: str,
        state: Dict[str, Any],
        legal_actions: List[Dict[str, Any]],
        prompt_variant: str,
        fallback_index: int,
        timeout_seconds: Optional[float] = None,
    ) -> DecisionOutcome:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")

        timeout = timeout_seconds or self.default_timeout_seconds
        fallback_index = max(0, min(fallback_index, len(legal_actions) - 1))

        provider_name = "none"
        model = "none"

        if self.provider is None:
            return DecisionOutcome(
                decision_name=decision_name,
                selected_index=fallback_index,
                selected_action=legal_actions[fallback_index],
                used_fallback=True,
                reason="provider_not_configured",
                prompt_variant=prompt_variant,
                provider=provider_name,
                model=model,
                latency_ms=0,
                raw_response="",
                input_tokens=None,
                output_tokens=None,
            )

        provider_name = self.provider.provider_name
        model = self.provider.model

        system_prompt, user_prompt = build_llm_messages(
            decision_name=decision_name,
            state=state,
            legal_actions=legal_actions,
            variant=prompt_variant,
        )

        start = time.perf_counter()
        try:
            generation = self.provider.generate(system_prompt, user_prompt, timeout)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return DecisionOutcome(
                decision_name=decision_name,
                selected_index=fallback_index,
                selected_action=legal_actions[fallback_index],
                used_fallback=True,
                reason=f"provider_error:{exc}",
                prompt_variant=prompt_variant,
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                raw_response="",
                input_tokens=None,
                output_tokens=None,
            )

        latency_ms = int((time.perf_counter() - start) * 1000)

        parsed = _extract_first_json_object(generation.text)
        action_index: Optional[int] = None

        if parsed and "action_index" in parsed:
            parsed_index = parsed.get("action_index")
            if isinstance(parsed_index, int):
                action_index = parsed_index
            elif isinstance(parsed_index, str) and parsed_index.isdigit():
                action_index = int(parsed_index)

        if action_index is None:
            action_index = _extract_action_index_relaxed(generation.text)

        if action_index is None:
            return DecisionOutcome(
                decision_name=decision_name,
                selected_index=fallback_index,
                selected_action=legal_actions[fallback_index],
                used_fallback=True,
                reason="invalid_json_response",
                prompt_variant=prompt_variant,
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                raw_response=generation.text,
                input_tokens=generation.input_tokens,
                output_tokens=generation.output_tokens,
            )

        if action_index < 0 or action_index >= len(legal_actions):
            return DecisionOutcome(
                decision_name=decision_name,
                selected_index=fallback_index,
                selected_action=legal_actions[fallback_index],
                used_fallback=True,
                reason="action_index_out_of_range",
                prompt_variant=prompt_variant,
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                raw_response=generation.text,
                input_tokens=generation.input_tokens,
                output_tokens=generation.output_tokens,
            )

        return DecisionOutcome(
            decision_name=decision_name,
            selected_index=action_index,
            selected_action=legal_actions[action_index],
            used_fallback=False,
            reason="ok",
            prompt_variant=prompt_variant,
            provider=provider_name,
            model=model,
            latency_ms=latency_ms,
            raw_response=generation.text,
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
        )
