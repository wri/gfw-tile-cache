from app.models.enumerators.tile_caches import TileCacheType


def test_TileCacheType_f_string_equals_enum_value():
    class_under_test = TileCacheType

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
