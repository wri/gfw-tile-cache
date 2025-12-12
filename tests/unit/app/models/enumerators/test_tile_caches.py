from app.models.enumerators.tile_caches import TileCacheType


def test_TileCacheType():
    class_under_test = TileCacheType

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
