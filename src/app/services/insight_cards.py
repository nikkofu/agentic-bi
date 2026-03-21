from app.domain.insight_models import AnomalyEvent


def build_insight_card(*, event: AnomalyEvent, attribution: dict, trace_id: str) -> dict:
    metric_label = {
        "gross_margin_rate": "毛利率",
        "revenue": "销售额",
        "gross_profit": "毛利额",
    }.get(event.metric, event.metric)

    summary = (
        f"检测到{metric_label}异常（当前{event.current_value:.2%}，"
        f"基线{event.baseline_value:.2%}，变化{event.delta:.2%}）"
    )
    suggested_next_question = f"请分析{attribution.get('key', '')}在该异常中的主要驱动因素"

    return {
        "trace_id": trace_id,
        "metric": event.metric,
        "scope": event.scope,
        "severity": event.severity,
        "summary": summary,
        "attribution": attribution,
        "suggested_next_question": suggested_next_question,
    }
