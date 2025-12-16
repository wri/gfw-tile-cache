from app.models.enumerators.geostore import GeostoreOrigin


def test_GeostoreOrigin_f_string_equals_enum_value():
    class_under_test = GeostoreOrigin

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
