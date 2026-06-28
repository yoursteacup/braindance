from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any


LOCAL_STACK_PATH = Path(os.getenv("BRAINDANCE_LOCAL_STACK_PATH", "/home/ivsed/PyCharmMiscProject"))
LOCAL_STACK_SRC = LOCAL_STACK_PATH / "src"
MODEL_REGISTRY_PATH = Path(os.getenv("BRAINDANCE_MODEL_REGISTRY", str(LOCAL_STACK_PATH / "config" / "models.json")))
GENERATED_DIR = Path(os.getenv("BRAINDANCE_GENERATED_DIR", str(LOCAL_STACK_PATH / "var" / "generated")))
IMAGE_BACKEND_PYTHON = os.getenv("BRAINDANCE_IMAGE_BACKEND_PYTHON", str(LOCAL_STACK_PATH / ".venv" / "bin" / "python"))
IMAGE_TIMEOUT_SECONDS = float(os.getenv("BRAINDANCE_IMAGE_TIMEOUT_SECONDS", "900"))
TEXT_TIMEOUT_SECONDS = float(os.getenv("BRAINDANCE_TEXT_TIMEOUT_SECONDS", "240"))
ENABLE_LOCAL_TEXT = os.getenv("BRAINDANCE_ENABLE_LOCAL_TEXT", "1").lower() in {"1", "true", "yes", "on"}

_CONTAINER: Any | None = None
_CONTAINER_ERROR: str | None = None
_LAST_TEXT_ERROR: str | None = None


def _local_stack_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return LOCAL_STACK_PATH / path


def _prepare_local_stack_settings() -> Any:
    _ensure_import_path()
    old_cwd = Path.cwd()
    try:
        # Load .env from the provider repo, then normalize every provider-owned
        # relative path so later calls do not depend on braindance's cwd.
        os.chdir(LOCAL_STACK_PATH)
        from llama_telegram_service.config.settings import Settings

        settings = Settings()
    finally:
        os.chdir(old_cwd)

    settings.data_dir = _local_stack_path(settings.data_dir)
    settings.database_path = _local_stack_path(settings.database_path)
    settings.resource_lock_path = _local_stack_path(settings.resource_lock_path)
    settings.media_dir = _local_stack_path(settings.media_dir)
    settings.log_dir = _local_stack_path(settings.log_dir)
    settings.smoke_image_path = _local_stack_path(settings.smoke_image_path)
    settings.model_registry_path = _local_stack_path(settings.model_registry_path)
    settings.lora_metadata_path = _local_stack_path(settings.lora_metadata_path)
    settings.generated_media_dir = _local_stack_path(settings.generated_media_dir)
    if not Path(settings.image_backend_python).is_absolute():
        settings.image_backend_python = str(LOCAL_STACK_PATH / settings.image_backend_python)
    return settings


def provider_status() -> dict[str, Any]:
    return {
        "provider": "PyCharmMiscProject local stack",
        "stack_path": str(LOCAL_STACK_PATH),
        "src_path": str(LOCAL_STACK_SRC),
        "model_registry": str(MODEL_REGISTRY_PATH),
        "generated_dir": str(GENERATED_DIR),
        "image_backend_python": IMAGE_BACKEND_PYTHON,
        "local_text_enabled": ENABLE_LOCAL_TEXT,
        "container_loaded": _CONTAINER is not None,
        "container_error": _CONTAINER_ERROR,
        "last_text_error": _LAST_TEXT_ERROR,
    }


def _ensure_import_path() -> None:
    src = str(LOCAL_STACK_SRC)
    if src not in sys.path:
        sys.path.insert(0, src)


def _get_container() -> Any:
    global _CONTAINER, _CONTAINER_ERROR
    if _CONTAINER is not None:
        return _CONTAINER

    _ensure_import_path()
    try:
        from llama_telegram_service.app.bootstrap import build_application_container

        _CONTAINER = build_application_container(_prepare_local_stack_settings())
        _CONTAINER_ERROR = None
        return _CONTAINER
    except Exception as exc:  # pragma: no cover - depends on local machine stack
        _CONTAINER_ERROR = f"{type(exc).__name__}: {exc}"
        raise


def _mock_text(character_state: dict[str, Any], world_state: dict[str, Any], user_text: str, reason: str | None = None) -> str:
    name = character_state.get("name") or "Mara"
    mood = character_state.get("mood") or "unknown"
    location = world_state.get("location") or "Neural Exchange"
    base = (
        f"{name} stays present in {location}, mood {mood}. "
        f"She answers the latest signal directly: {user_text or 'no user text was available'}."
    )
    if reason:
        return f"{base}\n\n[local text fallback: {reason}]"
    return base


async def _generate_text_async(character_state: dict[str, Any], world_state: dict[str, Any], user_text: str) -> str:
    container = _get_container()
    name = character_state.get("name") or "Mara"
    system_prompt = (
        f"You are {name}, a live character inside Braindance. "
        f"Current mood: {character_state.get('mood')}. "
        f"Stress: {character_state.get('stress')}, trust: {character_state.get('trust')}, "
        f"focus: {character_state.get('focus')}. "
        f"Current goal: {character_state.get('current_goal')}. "
        f"Location: {world_state.get('location')}. "
        "Reply in-character, concise, vivid, and grounded in the current state."
    )
    return await asyncio.wait_for(
        container.resource_dispatcher.run_roleplay_turn(
            session_key="braindance:mvp",
            system_prompt=system_prompt,
            user_text=user_text or "React to the current Braindance frame.",
        ),
        timeout=TEXT_TIMEOUT_SECONDS,
    )


def generate_text(character_state: dict[str, Any], world_state: dict[str, Any], user_text: str) -> str:
    global _LAST_TEXT_ERROR
    if not ENABLE_LOCAL_TEXT:
        _LAST_TEXT_ERROR = "local text disabled by BRAINDANCE_ENABLE_LOCAL_TEXT"
        return _mock_text(character_state, world_state, user_text, _LAST_TEXT_ERROR)

    try:
        text = asyncio.run(_generate_text_async(character_state, world_state, user_text))
        _LAST_TEXT_ERROR = None
        return text.strip()
    except Exception as exc:  # pragma: no cover - depends on local machine stack
        _LAST_TEXT_ERROR = f"{type(exc).__name__}: {exc}"
        return _mock_text(character_state, world_state, user_text, _LAST_TEXT_ERROR)


def _select_image_model() -> Any:
    container = _get_container()
    requested_id = os.getenv("BRAINDANCE_IMAGE_MODEL_ID")
    if requested_id:
        model = container.model_registry.get_model(requested_id)
        if not model or model.family != "image_gen" or not model.enabled or not model.available:
            raise RuntimeError(f"BRAINDANCE_IMAGE_MODEL_ID not found or unavailable: {requested_id}")
        return model

    model = container.model_registry.get_default_model("image_gen")
    if model is None:
        raise RuntimeError("no enabled image_gen model found in model registry")
    return model


async def _generate_image_async(prompt: str) -> dict[str, Any]:
    container = _get_container()
    model = _select_image_model()
    generated = await asyncio.wait_for(
        container.resource_dispatcher.generate_images(
            model,
            [prompt],
            output_prefix="braindance",
        ),
        timeout=IMAGE_TIMEOUT_SECONDS + 30,
    )
    if not generated:
        raise RuntimeError("image dispatcher returned no generated artifacts")
    payload = generated[0]
    output_path = str(payload.get("output_path", ""))
    return {
        "status": "ok",
        "path": output_path,
        "error": None,
        "model_id": model.id,
        "prompt": prompt,
        "raw": payload,
    }


def generate_image(frame_state: dict[str, Any] | str) -> dict[str, Any]:
    prompt = frame_state if isinstance(frame_state, str) else frame_state.get("frame_prompt") or frame_state.get("prompt") or "Braindance dream frame"
    try:
        return asyncio.run(_generate_image_async(str(prompt)))
    except TimeoutError as exc:  # pragma: no cover - depends on local GPU runtime
        return {
            "status": "timeout",
            "path": "",
            "error": f"image generation timed out after {IMAGE_TIMEOUT_SECONDS + 30}s: {exc}",
            "prompt": str(prompt),
        }
    except Exception as exc:  # pragma: no cover - depends on local machine stack
        return {
            "status": "error",
            "path": "",
            "error": f"{type(exc).__name__}: {exc}",
            "prompt": str(prompt),
        }
