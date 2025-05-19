
import cql2


def test_basic_cql2_filter():
    assert cql2.Expr("test = 'test'").matches({
        "properties": {
            "test": "test"
        }
    })


def test_cql2_array_filter():
    assert cql2.Expr({
        "op": "a_contains",
        "args": [{"property": "keywords"}, ["test"]]
    }).matches({
        "properties": {
            "keywords": ["test"]
        }
    })
