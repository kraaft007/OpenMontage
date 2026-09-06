"""Lock gemini_omni_fal's request shape to Gemini Omni 1.1 on fal.

The tool previously pointed at the unversioned `google/gemini-omni-flash/*`
slugs, which still resolve to the pre-1.1 preview model, and priced every
resolution at a flat $0.13/s. These key sets were verified on 2026-09-05
against fal's live OpenAPI documents at
`https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<slug>`; the
assertions below are the offline copy so a later edit cannot silently drift
off-contract or back onto the old model.
"""

import pytest
import requests

from tools.video.gemini_omni_fal import _ENDPOINTS, GeminiOmniFalVideo

# Exact Input-schema property names published by fal for each v1.1 endpoint.
LIVE_SCHEMA_KEYS = {
    "text_to_video": {"prompt", "aspect_ratio", "resolution", "duration"},
    "image_to_video": {
        "prompt",
        "image_url",
        "end_image_url",
        "aspect_ratio",
        "resolution",
        "duration",
    },
    "reference_to_video": {
        "prompt",
        "image_urls",
        "reference_video_urls",
        "aspect_ratio",
        "resolution",
        "duration",
    },
    # The edit endpoint inherits framing and length from the source clip.
    "edit_video": {"prompt", "video_url", "resolution"},
}

CASES = {
    "text_to_video": {"prompt": "a bridge"},
    "image_to_video": {
        "prompt": "he turns",
        "image_url": "https://x/a.jpg",
        "end_image_url": "https://x/b.jpg",
    },
    "reference_to_video": {
        "prompt": "same man",
        "reference_image_urls": ["https://x/a.jpg"],
        "reference_video_urls": ["https://x/c.mp4"],
    },
    "edit_video": {"prompt": "swap the patch", "video_url": "https://x/in.mp4"},
}


@pytest.fixture
def sent(monkeypatch):
    """Capture the outbound request without letting it leave the machine."""
    box = {}

    def fake_post(url, **kw):
        box["url"] = url
        box["json"] = kw.get("json")
        raise RuntimeError("intercepted")

    monkeypatch.setenv("FAL_KEY", "test")
    monkeypatch.setattr(requests, "post", fake_post)
    return box


@pytest.mark.parametrize("operation", sorted(CASES))
def test_payload_matches_fal_v11_schema(operation, sent, tmp_path):
    GeminiOmniFalVideo().execute(
        {
            **CASES[operation],
            "operation": operation,
            "output_path": str(tmp_path / "out.mp4"),
        }
    )
    assert sent["url"] == f"https://queue.fal.run/{_ENDPOINTS[operation]}"
    assert "/v1.1/" in sent["url"], "must target Omni 1.1, not the preview model"
    unknown = set(sent["json"]) - LIVE_SCHEMA_KEYS[operation]
    assert not unknown, f"{operation} sends fields fal will reject: {sorted(unknown)}"


def test_edit_omits_framing_and_length(sent, tmp_path):
    # Sending these to /edit is a 422 — the endpoint takes neither.
    GeminiOmniFalVideo().execute(
        {
            **CASES["edit_video"],
            "operation": "edit_video",
            "aspect_ratio": "9:16",
            "duration": 10,
            "output_path": str(tmp_path / "out.mp4"),
        }
    )
    assert "aspect_ratio" not in sent["json"]
    assert "duration" not in sent["json"]


@pytest.mark.parametrize(
    "resolution, expected",
    [("360p", 0.24), ("720p", 0.80), ("1080p", 1.20), ("4k", 2.40)],
)
def test_cost_follows_resolution_tier(resolution, expected):
    # fal bills per output second by tier; the old flat 0.13/s over-reported
    # 720p by 30% and under-reported 4k by 3x.
    cost = GeminiOmniFalVideo().estimate_cost(
        {"duration": 8, "resolution": resolution}
    )
    assert cost == pytest.approx(expected)


def test_cost_defaults_to_720p():
    tool = GeminiOmniFalVideo()
    assert tool.estimate_cost({"duration": 8}) == tool.estimate_cost(
        {"duration": 8, "resolution": "720p"}
    )
