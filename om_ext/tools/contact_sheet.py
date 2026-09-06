"""Build a labelled contact sheet from reference images.

Reference stills are useless for a decision if the human cannot tell which
image is which. Filenames are not visible when images are viewed side by side,
and the agent's labels live only in chat. This renders the labels into the
picture itself.

Pillow rather than ffmpeg on purpose: ffmpeg's `drawtext` needs libfreetype,
which the Homebrew build on this machine was compiled without (measured
2026-09-05, `ffmpeg -filters` lists no drawtext). Pillow is already a
dependency and needs no system font support beyond a .ttf path.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

# Ordered by preference; the first that exists wins. macOS ships both.
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _find_font() -> str | None:
    return next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)


class ContactSheet(BaseTool):
    name = "contact_sheet"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "analysis"
    provider = "openmontage"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:PIL"]
    install_instructions = "Pillow ships with OpenMontage; no configuration needed."

    capabilities = ["contact_sheet"]
    supports = {"labelled_rows": True, "per_image_captions": True}
    best_for = [
        "presenting a set of reference stills for a human pick",
        "mood boards where the viewer must be able to name what they chose",
    ]
    not_good_for = ["video input", "more than ~40 images in one sheet"]

    input_schema = {
        "type": "object",
        "required": ["rows", "output_path"],
        "properties": {
            "rows": {
                "type": "array",
                "minItems": 1,
                "description": "One labelled row per group of related images.",
                "items": {
                    "type": "object",
                    "required": ["label", "images"],
                    "properties": {
                        "label": {"type": "string"},
                        "images": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string"},
                            "description": "Image paths; the basename becomes the caption.",
                        },
                    },
                },
            },
            "output_path": {"type": "string"},
            "cell_width": {"type": "integer", "default": 620, "minimum": 200},
            "title": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, network_required=False)
    idempotency_key_fields = ["rows", "cell_width", "title"]
    side_effects = ["writes an image to output_path"]
    user_visible_verification = [
        "Open the sheet and confirm every image carries a readable caption"
    ]

    def get_status(self) -> ToolStatus:
        try:
            import PIL  # noqa: F401
        except ImportError:
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE if _find_font() else ToolStatus.DEGRADED

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        n = sum(len(r.get("images", [])) for r in inputs.get("rows", []))
        return 0.5 + 0.1 * n

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from PIL import Image, ImageDraw, ImageFont

        started = time.time()
        font_path = _find_font()
        if font_path is None:
            return ToolResult(
                success=False,
                error="No usable TrueType font found; cannot render labels.",
            )

        rows = inputs["rows"]
        missing = [
            p for r in rows for p in r["images"] if not Path(p).exists()
        ]
        if missing:
            return ToolResult(
                success=False, error=f"image(s) not found: {missing[:5]}"
            )

        cw = int(inputs.get("cell_width", 620))
        title = inputs.get("title")
        pad, hdr, cap = 16, 40, 30
        title_h = 46 if title else 0

        # One shared cell height keeps rows aligned; derive it from the first
        # image so mixed aspect ratios letterbox consistently rather than
        # producing a ragged grid.
        with Image.open(rows[0]["images"][0]) as probe:
            ch = round(cw * probe.height / probe.width)

        cols = max(len(r["images"]) for r in rows)
        width = pad + cols * (cw + pad)
        height = title_h + pad + len(rows) * (hdr + ch + cap + pad)

        sheet = Image.new("RGB", (width, height), (18, 20, 24))
        draw = ImageDraw.Draw(sheet)
        f_title = ImageFont.truetype(font_path, 28)
        f_hdr = ImageFont.truetype(font_path, 22)
        f_cap = ImageFont.truetype(font_path, 17)

        y = pad
        if title:
            draw.text((pad, y), title, font=f_title, fill=(240, 240, 240))
            y += title_h

        for row in rows:
            draw.text((pad, y + 9), row["label"], font=f_hdr, fill=(232, 163, 61))
            y += hdr
            x = pad
            for path in row["images"]:
                with Image.open(path) as im:
                    im = im.convert("RGB").resize((cw, ch), Image.LANCZOS)
                    sheet.paste(im, (x, y))
                draw.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(70, 78, 88))
                draw.text(
                    (x + 4, y + ch + 6),
                    Path(path).name,
                    font=f_cap,
                    fill=(178, 188, 198),
                )
                x += cw + pad
            y += ch + cap + pad

        out = Path(inputs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, quality=92)

        return ToolResult(
            success=True,
            data={
                "output": str(out),
                "width": sheet.width,
                "height": sheet.height,
                "rows": len(rows),
                "images": sum(len(r["images"]) for r in rows),
            },
            artifacts=[str(out)],
            cost_usd=0.0,
            duration_seconds=round(time.time() - started, 2),
        )
