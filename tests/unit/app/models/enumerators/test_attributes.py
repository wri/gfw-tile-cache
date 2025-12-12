from app.models.enumerators.attributes import TcdEnum, TcdStyleEnum


def test_TcdEnum():
    class_under_test = TcdEnum

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value


def test_TcdStyleEnum():
    class_under_test = TcdStyleEnum

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
