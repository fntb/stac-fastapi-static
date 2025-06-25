
from stac_fastapi.static.core.lib.geometries_intersect import bbox_intersect


def test_bbox_intersect():

    ref_bbox = (2, 2, 5, 5)

    window = (
        (0, 1),
        (1, 3),
        (3, 4),
        (4, 6),
        (6, 7)
    )

    test_bboxes = set(
        (x[0], y[0], x[1], y[1])
        for x in window
        for y in window
    )

    expected_not_to_intersect = set(
        bbox
        for bbox in test_bboxes
        if bbox[0] == 0 or bbox[2] == 7 or bbox[1] == 0 or bbox[3] == 7
    )

    expected_to_intersect = test_bboxes - expected_not_to_intersect

    for bbox in expected_to_intersect:
        assert bbox_intersect(bbox, ref_bbox)

    for bbox in expected_not_to_intersect:
        assert not bbox_intersect(bbox, ref_bbox)
