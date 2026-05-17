from src.risk_filter.assembler import RiskAssembler


def test_risk_assembler_returns_trade_ok_when_all_conditions_pass():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["signal valid"],
    )

    assert result.trade_ok is True
    assert result.lot == 0.1
    assert result.stop_loss == 1.0
    assert result.take_profit == 1.2
    assert "fixed_sl_tp" in result.risk_reason
    assert "placeholder_fixed_lot" in result.risk_reason
    assert result.filter_reason == "all risk filters passed"


def test_risk_assembler_returns_false_when_entry_signal_is_false():
    result = RiskAssembler.assemble(
        entry_signal=False,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal invalid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["signal invalid"],
    )

    assert result.trade_ok is False
    assert "risk_contract_invalid" in result.filter_reason
    assert result.risk_reason


def test_risk_assembler_returns_false_when_event_risk_flag_is_true():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=True,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["event risk active"],
    )

    assert result.trade_ok is False
    assert "event_risk" in result.filter_reason
    assert result.risk_reason


def test_risk_assembler_returns_false_when_spread_ok_is_false():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=False,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["spread bad"],
    )

    assert result.trade_ok is False
    assert "spread_too_wide" in result.filter_reason
    assert result.risk_reason


def test_risk_assembler_returns_false_when_limit_ok_is_false():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=False,
        max_trade_reached_flag=True,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
        sub_reasons=["limit exceeded"],
    )

    assert result.trade_ok is False
    assert "trade_limit_reached" in result.filter_reason
    assert result.risk_reason


def test_risk_assembler_returns_false_when_lot_or_sl_tp_missing():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=None,
        stop_loss=None,
        take_profit=None,
        sub_reasons=["missing risk values"],
    )

    assert result.trade_ok is False
    assert "risk_contract_invalid" in result.filter_reason
    assert "invalid_lot" in result.risk_reason
    assert "invalid_stop_loss" in result.risk_reason
    assert "invalid_take_profit" in result.risk_reason
    assert result.risk_reason


def test_risk_assembler_returns_false_when_lot_non_positive():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="long_entry",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.0,
        stop_loss=1.0,
        take_profit=1.2,
    )

    assert result.trade_ok is False
    assert "invalid_lot" in result.risk_reason


def test_risk_assembler_rejects_invalid_lot_nan_inf_bool():
    for lot in [float("nan"), float("inf"), True]:
        result = RiskAssembler.assemble(
            entry_signal=True,
            exit_signal=False,
            signal_type="long_entry",
            signal_reason="signal valid",
            event_risk_flag=False,
            spread_ok=True,
            limit_ok=True,
            max_trade_reached_flag=False,
            lot=lot,  # type: ignore[arg-type]
            stop_loss=1.0,
            take_profit=1.2,
        )
        assert result.trade_ok is False
        assert "invalid_lot" in result.risk_reason


def test_risk_assembler_rejects_invalid_stop_loss_nan_or_bool():
    for stop_loss in [float("nan"), True]:
        result = RiskAssembler.assemble(
            entry_signal=True,
            exit_signal=False,
            signal_type="long_entry",
            signal_reason="signal valid",
            event_risk_flag=False,
            spread_ok=True,
            limit_ok=True,
            max_trade_reached_flag=False,
            lot=0.1,
            stop_loss=stop_loss,  # type: ignore[arg-type]
            take_profit=1.2,
        )
        assert result.trade_ok is False
        assert "invalid_stop_loss" in result.risk_reason


def test_risk_assembler_rejects_invalid_take_profit_inf_or_bool():
    for take_profit in [float("inf"), True]:
        result = RiskAssembler.assemble(
            entry_signal=True,
            exit_signal=False,
            signal_type="long_entry",
            signal_reason="signal valid",
            event_risk_flag=False,
            spread_ok=True,
            limit_ok=True,
            max_trade_reached_flag=False,
            lot=0.1,
            stop_loss=1.0,
            take_profit=take_profit,  # type: ignore[arg-type]
        )
        assert result.trade_ok is False
        assert "invalid_take_profit" in result.risk_reason


def test_risk_assembler_rejects_exit_signal_type_for_entry_contract():
    result = RiskAssembler.assemble(
        entry_signal=True,
        exit_signal=False,
        signal_type="exit",
        signal_reason="signal valid",
        event_risk_flag=False,
        spread_ok=True,
        limit_ok=True,
        max_trade_reached_flag=False,
        lot=0.1,
        stop_loss=1.0,
        take_profit=1.2,
    )

    assert result.trade_ok is False
    assert "risk_contract_invalid" in result.filter_reason
