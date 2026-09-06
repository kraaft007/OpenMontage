"""Contract tests for the om_ext contact_sheet tool.

Also pins the isolation property the package exists for: om_ext must be
loadable through registry.discover's package_name argument, so that no upstream
file has to be edited to reach it.
"""

import pytest
from PIL import Image

from om_ext.tools.contact_sheet import ContactSheet
from tools.base_tool import ToolStatus


@pytest.fixture
def images(tmp_path):
    """Three 1024x572 stills, the shape Gemini returns for a 16:9 prompt."""
    paths = []
    for i, colour in enumerate([(120, 40, 40), (40, 120, 40), (40, 40, 120)], start=1):
        p = tmp_path / f"shot-{i}.jpg"
        Image.new("RGB", (1024, 572), colour).save(p)
        paths.append(str(p))
    return paths


def test_discoverable_without_touching_the_core_package():
    # The whole point of om_ext: a second discover() call reaches it, and the
    # default "tools" sweep does not, so upstream stays unmodified.
    from tools.tool_registry import ToolRegistry

    reg = ToolRegistry()
    reg.discover("tools")
    assert "contact_sheet" not in reg._tools

    added = reg.discover("om_ext")
    assert "contact_sheet" in added
    assert reg._tools["contact_sheet"].capability == "analysis"


def test_builds_a_sheet_with_expected_geometry(images, tmp_path):
    out = tmp_path / "sheet.jpg"
    result = ContactSheet().execute(
        {
            "title": "Formation scout",
            "rows": [
                {"label": "F1 canopy", "images": images},
                {"label": "F2 deck", "images": images[:2]},
            ],
            "output_path": str(out),
            "cell_width": 300,
        }
    )
    assert result.success, result.error
    assert out.exists()
    assert result.data["rows"] == 2
    assert result.data["images"] == 5

    # Width is driven by the widest row, not the last one — a short row must not
    # shrink the sheet and crop the row above it.
    with Image.open(out) as im:
        assert im.width == 16 + 3 * (300 + 16)
        assert im.height == result.data["height"]


def test_cost_is_zero_and_local():
    tool = ContactSheet()
    assert tool.estimate_cost({}) == 0.0
    assert tool.runtime.value == "local"


def test_missing_image_fails_cleanly(tmp_path):
    result = ContactSheet().execute(
        {
            "rows": [{"label": "x", "images": [str(tmp_path / "absent.jpg")]}],
            "output_path": str(tmp_path / "out.jpg"),
        }
    )
    assert not result.success
    assert "not found" in result.error


def test_status_is_available_when_pillow_and_a_font_exist():
    assert ContactSheet().get_status() in {ToolStatus.AVAILABLE, ToolStatus.DEGRADED}
