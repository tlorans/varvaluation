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
        "ValuationModel",
        "isolate_channels",
        "news_decomposition",
        "treasury_test",
        "NewsResult",
        "NewsShares",
        "ValuationResult",
        "ResidualIncome",
        "CCAPMSpec",
        "TermStructureModel",
        "ResidualIncomeModel",
        "paper_state_spec",
        "flat_annuity_value",
        "valuation_discrepancy",
        "TermStructureError",
        "simulate_paper_state",
        "INSURANCE",
        "prepare_industry_state",
        "capm_tests",
        "slope_tests",
    ):
        assert hasattr(v, name), name
    assert v.ValuationModel is v.AngLiuModel
