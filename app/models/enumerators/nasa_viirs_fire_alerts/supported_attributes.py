from aenum import Enum

from ....application import db


def rule(aggregation_expression, label):
    return db.literal_column(aggregation_expression).label(label)


class SupportedAttribute(Enum, init="value aggregation_rule"):

    LATITUDE = ("latitude", rule("round(avg(latitude),4)", "latitude"))
    LONGITUDE = ("longitude", rule("round(avg(longitude),4)", "longitude"))
    ALERT_DATE = (
        "alert__date",
        rule("mode() WITHIN GROUP (ORDER BY alert__date)", "alert__date"),
    )
    ALERT_TIME_UTC = (
        "alert__time_utc",
        rule("mode() WITHIN GROUP (ORDER BY alert__time_utc)", "alert__time_utc"),
    )
    CONFIDENCE_CAT = (
        "confidence__cat",
        rule("mode() WITHIN GROUP (ORDER BY confidence__cat)", "confidence__cat"),
    )
    BRIGHT_TI4_K = (
        "bright_ti4__K",
        rule('round(avg("bright_ti4__K"),3)', "bright_ti4__K"),
    )
    BRIGHT_TI5_K = (
        "bright_ti5__K",
        rule('round(avg("bright_ti5__k"),3)', "bright_ti5__K"),
    )
    FRP_MW = ("frp__MW", rule('sum("frp__MW")', "frp__MW"))
    UMD_TREE_COVER_DENSITY_2000__THRESHOLD = (
        "umd_tree_cover_density_2000__threshold",
        rule(
            'max("umd_tree_cover_density_2000__threshold")',
            "umd_tree_cover_density_2000__threshold",
        ),
    )
    UMD_TREE_COVER_DENSITY__THRESHOLD = (
        "umd_tree_cover_density__threshold",
        rule(
            'max("umd_tree_cover_density__threshold")',
            "umd_tree_cover_density__threshold",
        ),
    )

    def __str__(self):
        return self.value
