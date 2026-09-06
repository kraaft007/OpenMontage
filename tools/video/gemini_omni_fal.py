"""Gemini Omni Flash generation and editing through fal.ai."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


# fal serves Omni 1.1 under a /v1.1/ path segment; the unversioned slugs still
# resolve to the pre-1.1 preview model. Verified against fal's published API docs
# 2026-09-05.
_ENDPOINTS = {
    "text_to_video": "google/gemini-omni-flash/v1.1/text-to-video",
    "image_to_video": "google/gemini-omni-flash/v1.1/image-to-video",
    "reference_to_video": "google/gemini-omni-flash/v1.1/reference-to-video",
    "edit_video": "google/gemini-omni-flash/v1.1/edit",
}

# fal's published per-output-second rates by resolution tier (2026-09-05).
# The prior flat 0.13/s constant over-reported 720p by 30%.
_PRICE_PER_SECOND = {"360p": 0.03, "720p": 0.10, "1080p": 0.15, "4k": 0.30}
_DEFAULT_RESOLUTION = "720p"
_DEFAULT_DURATION = 8


class GeminiOmniFalVideo(BaseTool):
    name = "gemini_omni_fal"
    version = "0.3.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "gemini_omni"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API
    agent_skills = ["gemini-omni", "ai-video-gen"]
    capabilities = [
        "text_to_video",
        "image_to_video",
        "reference_to_video",
        "edit_video",
    ]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "reference_to_video": True,
        "video_to_video": True,
        "multiple_reference_images": True,
        "reference_video": True,
        "first_last_frame_to_video": True,
        "native_audio": True,
    }
    best_for = [
        "Gemini Omni 1.1 Flash with a fal.ai key",
        "reference-image-driven 3-10 second video with synchronized audio",
        "first-and-last-frame interpolation via end_image_url",
        "cheap 360p drafts at $0.03/s before committing to a 720p or 1080p take",
    ]
    # Scene extension (10s of prior context, cumulative 40s) is a multi-turn
    # previous_interaction_id workflow on Google's own Interactions API. fal
    # exposes no extend endpoint and accepts no interaction id as input, so that
    # capability stays with the direct `gemini_omni_video` tool.
    not_good_for = [
        "scene extension / multi-turn continuation (use gemini_omni_video)",
        "offline generation",
    ]
    fallback_tools = ["gemini_omni_video", "runway_video", "veo_video"]
    dependencies = ["env:FAL_KEY"]
    install_instructions = (
        "Set FAL_KEY (or FAL_AI_API_KEY) from https://fal.ai/dashboard/keys."
    )
    quality_score = 0.85
    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": [
                    "text_to_video",
                    "image_to_video",
                    "reference_to_video",
                    "edit_video",
                ],
                "default": "text_to_video",
            },
            "image_url": {"type": "string"},
            "image_path": {"type": "string"},
            "end_image_url": {
                "type": "string",
                "description": (
                    "Closing frame for image_to_video. When set, the model "
                    "interpolates from image_url to this frame."
                ),
            },
            "end_image_path": {
                "type": "string",
                "description": "Local closing frame, uploaded then used as end_image_url.",
            },
            "reference_image_urls": {"type": "array", "items": {"type": "string"}},
            "reference_image_paths": {"type": "array", "items": {"type": "string"}},
            "reference_video_urls": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 3,
                "description": (
                    "reference_to_video only. Up to three clips, each at most "
                    "three seconds. Reference media is consumed in list order."
                ),
            },
            "video_url": {
                "type": "string",
                "description": "Source clip for edit_video",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16"],
                "default": "16:9",
            },
            "resolution": {
                "type": "string",
                "enum": ["360p", "720p", "1080p", "4k"],
                "default": _DEFAULT_RESOLUTION,
                "description": "Drives both output size and price; 360p is the draft tier.",
            },
            "duration": {
                "type": "integer",
                "minimum": 3,
                "maximum": 10,
                "default": _DEFAULT_DURATION,
            },
            "output_path": {"type": "string"},
        },
    }
    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(
        max_retries=2, retryable_errors=["rate_limit", "timeout"]
    )
    idempotency_key_fields = [
        "prompt",
        "operation",
        "aspect_ratio",
        "resolution",
        "duration",
        "reference_image_urls",
    ]
    side_effects = ["writes video file to output_path", "calls fal.ai API"]
    user_visible_verification = ["Watch the clip and listen for synchronized audio"]

    @staticmethod
    def _api_key() -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        rate = _PRICE_PER_SECOND.get(
            str(inputs.get("resolution") or _DEFAULT_RESOLUTION).lower(),
            _PRICE_PER_SECOND[_DEFAULT_RESOLUTION],
        )
        return round(rate * int(inputs.get("duration", _DEFAULT_DURATION)), 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 90.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._api_key()
        if not api_key:
            return ToolResult(
                success=False, error="FAL_KEY not set. " + self.install_instructions
            )
        import requests
        from tools.video._shared import probe_output, upload_image_fal

        operation = inputs.get("operation", "text_to_video")
        urls = list(inputs.get("reference_image_urls") or [])
        for local in inputs.get("reference_image_paths") or []:
            urls.append(upload_image_fal(local))
        if inputs.get("image_url"):
            urls.insert(0, inputs["image_url"])
        elif inputs.get("image_path"):
            urls.insert(0, upload_image_fal(inputs["image_path"]))
        reference_videos = list(inputs.get("reference_video_urls") or [])
        if len(reference_videos) > 3:
            return ToolResult(
                success=False,
                error="reference_video_urls accepts at most three clips",
            )
        if operation == "image_to_video" and not urls:
            return ToolResult(
                success=False,
                error="image_to_video requires at least one reference image",
            )
        # 1.1 lets reference_to_video be driven by videos alone, so images are no
        # longer the only admissible reference.
        if operation == "reference_to_video" and not urls and not reference_videos:
            return ToolResult(
                success=False,
                error="reference_to_video requires reference images or reference videos",
            )

        if operation not in _ENDPOINTS:
            return ToolResult(
                success=False, error=f"unsupported Gemini Omni operation: {operation}"
            )
        if operation in {"text_to_video", "edit_video"} and urls:
            return ToolResult(
                success=False,
                error=f"{operation} does not accept reference images on fal.ai",
            )
        endpoint = _ENDPOINTS[operation]
        resolution = str(
            inputs.get("resolution") or _DEFAULT_RESOLUTION
        ).lower()
        if resolution not in _PRICE_PER_SECOND:
            return ToolResult(
                success=False,
                error=f"unsupported resolution: {resolution}",
            )
        payload: dict[str, Any] = {
            "prompt": inputs["prompt"],
            "aspect_ratio": inputs.get("aspect_ratio", "16:9"),
            "resolution": resolution,
            "duration": int(inputs.get("duration", _DEFAULT_DURATION)),
        }
        if operation == "image_to_video":
            payload["image_url"] = urls[0]
            end_url = inputs.get("end_image_url")
            if not end_url and inputs.get("end_image_path"):
                end_url = upload_image_fal(inputs["end_image_path"])
            if end_url:
                payload["end_image_url"] = end_url
        elif operation == "reference_to_video":
            if urls:
                payload["image_urls"] = urls
            if reference_videos:
                payload["reference_video_urls"] = reference_videos
        elif operation == "edit_video":
            if not inputs.get("video_url"):
                return ToolResult(success=False, error="edit_video requires video_url")
            # The edit endpoint takes no aspect_ratio or duration — it inherits
            # both from the source clip.
            payload = {
                "prompt": inputs["prompt"],
                "video_url": inputs["video_url"],
                "resolution": resolution,
            }
        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }
        started = time.time()
        try:
            submit = requests.post(
                f"https://queue.fal.run/{endpoint}",
                headers=headers,
                json=payload,
                timeout=30,
            )
            submit.raise_for_status()
            queued = submit.json()
            while True:
                time.sleep(5)
                status_response = requests.get(
                    queued["status_url"], headers=headers, timeout=15
                )
                status_response.raise_for_status()
                status = status_response.json().get("status")
                if status == "COMPLETED":
                    break
                if status in {"FAILED", "CANCELLED"}:
                    return ToolResult(
                        success=False,
                        error=f"fal.ai Gemini Omni generation {status.lower()}",
                    )
            result_response = requests.get(
                queued["response_url"], headers=headers, timeout=30
            )
            result_response.raise_for_status()
            result_json = result_response.json()
            video_url = result_json["video"]["url"]
            download = requests.get(video_url, timeout=120)
            download.raise_for_status()
            output_path = Path(inputs.get("output_path", "gemini_omni_fal_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(download.content)
        except Exception as exc:
            return ToolResult(
                success=False, error=f"fal.ai Gemini Omni generation failed: {exc}"
            )
        return ToolResult(
            success=True,
            data={
                "provider": "gemini_omni",
                "gateway": "fal.ai",
                "model": endpoint,
                "operation": operation,
                "resolution": resolution,
                # The edit endpoint returns one; fal accepts no interaction id as
                # input, so this is for traceability, not for multi-turn resume.
                "interaction_id": result_json.get("interaction_id"),
                "output": str(output_path),
                **probe_output(output_path),
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - started, 2),
            model=endpoint,
        )
