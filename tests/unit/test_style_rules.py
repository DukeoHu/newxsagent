from xsagent.domain.common.style_rules import style_rules_prompt_text


def test_style_rules_prompt_text_orders_by_priority():
    text = style_rules_prompt_text(
        [
            {
                "id": "sr_1",
                "category": "tone",
                "title": "偏爱冷幽默",
                "description": "适度自嘲即可",
                "priority": "prefer",
            },
            {
                "id": "sr_2",
                "category": "perspective",
                "title": "第三人称限知",
                "description": "紧贴主角感知",
                "priority": "must",
            },
            {
                "id": "sr_3",
                "category": "dialogue",
                "title": "对话口语化",
                "description": "少用书面腔",
                "priority": "should",
            },
        ]
    )
    assert "必须/视角" in text
    assert "应当/对话" in text
    assert "偏好/基调" in text
    assert text.index("第三人称限知") < text.index("对话口语化")
    assert text.index("对话口语化") < text.index("偏爱冷幽默")


def test_style_rules_prompt_text_empty():
    assert style_rules_prompt_text([]) == "（无结构化风格规则）"
    assert style_rules_prompt_text(None) == "（无结构化风格规则）"
