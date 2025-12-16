from app.models.enumerators.titiler import (
    AlertConfidence, IntegratedAlertConfidence, RenderType, TCLTreeCoverDensityThreshold, TreeCoverDensityThreshold
)


def test_AlertConfidence_f_string_equals_enum_value():
    class_under_test = AlertConfidence

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value


def test_IntegratedAlertConfidence_f_string_equals_enum_value():
    class_under_test = IntegratedAlertConfidence

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value


def test_RenderType_f_string_equals_enum_value():
    class_under_test = RenderType

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value


def test_TCLTreeCoverDensityThreshold_f_string_equals_enum_value():
    class_under_test = TCLTreeCoverDensityThreshold

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value


def test_TreeCoverDensityThreshold_f_string_equals_enum_value():
    class_under_test = TreeCoverDensityThreshold

    # Get an arbitrary (the first) element
    val = list(iter(class_under_test))[0]
    assert f"{val}" == getattr(class_under_test, val.name).value
