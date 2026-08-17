import varvaluation as v


def test_public_names():
    for name in (
        "StateSpec",
        "ExpectedReturnSpec",
        "state_schema",
        "returns_schema",
        "estimate_var",
        "estimate_var_panel",
        "VARFit",
        "AngLiuModel",
        "isolate_channels",
        "news_decomposition",
        "treasury_test",
        "NewsResult",
        "NewsShares",
        "ValuationResult",
    ):
        assert hasattr(v, name), name
