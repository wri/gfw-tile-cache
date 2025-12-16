from app.models.enumerators.wmts import WmtsRequest


def test_WmtsRequest_f_string_equals_enum_value():
    class_under_test = WmtsRequest

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
