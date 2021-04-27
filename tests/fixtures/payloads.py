####################
# Raster Tile Cache payloads
####################


def umd_tree_cover_loss_payload():
    dataset = "umd_tree_cover_loss"
    version = "v1.8"
    tcd = 30
    x = 1
    y = 1
    z = 12
    start_year = 2001
    end_year = 2010
    over_zoom = 12

    params = {"start_year": start_year, "end_year": end_year, "tcd": tcd}

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": f"tcd_{tcd}",
        "x": x,
        "y": y,
        "z": z,
        "start_year": start_year,
        "end_year": end_year,
        "filter_type": "annual_loss",
        "over_zoom": over_zoom
        # "source": "tilecache",
    }

    return params, payload


def umd_glad_alerts_payload():
    dataset = "umd_glad_alerts"
    version = "v20210101"
    x = 1
    y = 1
    z = 12
    start_date = "2018-01-01"
    end_date = "2019-01-01"
    confirmed_only = True
    over_zoom = 14

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "confirmed_only": confirmed_only,
    }

    payload = {
        "dataset": dataset,
        "version": version,
        "implementation": "default",
        "x": x,
        "y": y,
        "z": z,
        "start_date": start_date,
        "end_date": end_date,
        "confirmed_only": confirmed_only,
        "filter_type": "deforestation_alerts",
        "source": "tilecache",
        "over_zoom": over_zoom,
    }

    return params, payload
