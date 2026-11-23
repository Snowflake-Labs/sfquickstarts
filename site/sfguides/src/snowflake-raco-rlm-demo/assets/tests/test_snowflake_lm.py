import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def engine_module(monkeypatch):
    import sys
    from types import ModuleType

    lm15 = ModuleType('dspy.lm15')
    lm15.Message = SimpleNamespace(assistant=lambda text: SimpleNamespace(text=text))
    lm15.Response = lambda **kwargs: SimpleNamespace(**kwargs)
    lm15.Usage = lambda: SimpleNamespace()
    monkeypatch.setitem(sys.modules, 'dspy', ModuleType('dspy'))
    monkeypatch.setitem(sys.modules, 'dspy.lm15', lm15)
    spec = importlib.util.spec_from_file_location(
        'snowflake_lm_under_test', Path(__file__).resolve().parents[1] / 'snowflake_lm.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(text='Summarize', max_tokens=100, role='user'):
    return SimpleNamespace(
        model='custom/snowflake-ai-complete', tools=(), system='Be concise',
        messages=(SimpleNamespace(role=role, text=text),),
        config=SimpleNamespace(max_tokens=max_tokens),
    )


def test_sql_uses_binding_and_caps_output(engine_module):
    session = Mock()
    session.sql.return_value.collect.return_value = [('Snowflake result',)]
    response = engine_module.SnowflakeCompleteEngine(session, max_tokens=150).complete(request(max_tokens=999))
    sql, _ = session.sql.call_args.args, session.sql.call_args.kwargs
    assert "AI_COMPLETE('openai-gpt-6-luna', ?, OBJECT_CONSTRUCT" in sql[0]
    assert 'Summarize' not in sql[0]
    assert session.sql.call_args.kwargs['params'][1] == 150
    assert response.message.text == 'Snowflake result'


def test_rejects_unrepresentable_and_empty_responses(engine_module):
    session = Mock()
    engine = engine_module.SnowflakeCompleteEngine(session)
    with pytest.raises(ValueError):
        engine.complete(request(role='tool'))
    with pytest.raises(ValueError):
        engine.complete(request(text='x' * 40001))
    assert not session.sql.called
    session.sql.return_value.collect.return_value = [(None,)]
    with pytest.raises(RuntimeError):
        engine.complete(request())