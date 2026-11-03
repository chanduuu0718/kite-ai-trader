from app.indianapi import parse_intraday_values


def test_parse_intraday_values_sorts_and_normalizes_ist_points():
    payload = [
        {
            "tickerId": "RELIANCE",
            "values": [
                {"timeStamp": "2026-11-02 09:25:00", "price": 1425.5},
                {"timeStamp": "2026-11-02 09:20:00", "price": 1424.0},
                {"timeStamp": "2026-11-02 09:25:00", "price": 1426.0},
            ],
        }
    ]

    points = parse_intraday_values(payload)

    assert len(points) == 2
    assert points[0]["price"] == 1424.0
    assert points[1]["price"] == 1426.0
    assert points[0]["timestamp_ist"].endswith("+05:30")
    assert points[0]["time"] < points[1]["time"]


def test_parse_intraday_values_ignores_invalid_rows():
    payload = [{"values": [
        {"timeStamp": "not-a-date", "price": 100},
        {"timeStamp": "2026-11-02 09:25:00", "price": "bad"},
        {"timeStamp": "2026-11-02 09:30:00", "price": 100},
    ]}]

    points = parse_intraday_values(payload)

    assert len(points) == 1
    assert points[0]["price"] == 100.0
