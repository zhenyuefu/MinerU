"""行内公式框写进 docvortex_layout 页面几何，并随批次合并与页号重映射保留。"""

from docvortex.document.pdf.layout import merge_layout_extensions, remap_layout_geometry

from mineru.backend.analysis.pdf.formulas import collect_inline_formula_boxes
from mineru.backend.analysis.pdf.pipeline import attach_inline_formulas


def test_inline_formula_boxes_are_unit_boxes_with_score_and_latex() -> None:
    formulas = [
        {"label": "inline_formula", "bbox": [612.0, 396.0, 918.0, 792.0], "score": 0.9187, "latex": " M _ { t } "},
        {"label": "inline_formula", "bbox": [10.0, 10.0, 10.0, 20.0], "score": 0.5, "latex": "x"},  # 退化框
        {"label": "inline_formula", "bbox": None, "score": 0.5, "latex": "y"},
    ]
    assert collect_inline_formula_boxes(formulas, (1224, 1584)) == [
        {"bbox": [0.5, 0.25, 0.75, 0.5], "score": 0.919, "latex": "M _ { t }"}
    ]
    assert collect_inline_formula_boxes(formulas, (0, 1584)) == []


def test_inline_formulas_ride_on_page_geometry_through_remap_and_merge() -> None:
    geometry = {"version": 1, "pages": [{"page_idx": idx, "width_pt": 612, "height_pt": 792} for idx in (0, 1)]}
    box = {"bbox": [0.1, 0.2, 0.3, 0.25], "score": 0.9, "latex": "x"}
    attach_inline_formulas(geometry, {0: [box], 1: []})
    assert geometry["pages"][0]["inline_formulas"] == [box]
    assert geometry["pages"][1]["inline_formulas"] == []  # 跑过版面模型但没检出

    flash = {"version": 1, "pages": [{"page_idx": 0, "width_pt": 612, "height_pt": 792}]}
    attach_inline_formulas(flash, {})
    assert "inline_formulas" not in flash["pages"][0]  # 没跑版面模型

    remapped = remap_layout_geometry(geometry, [4, 7])
    assert [page["page_idx"] for page in remapped["pages"]] == [4, 7]
    assert remapped["pages"][0]["inline_formulas"] == [box]
    merged = merge_layout_extensions({"docvortex_layout": remapped}, {"docvortex_layout": flash}, [0])
    pages = {page["page_idx"]: page for page in merged["docvortex_layout"]["pages"]}
    assert pages[4]["inline_formulas"] == [box]
    assert "inline_formulas" not in pages[0]
