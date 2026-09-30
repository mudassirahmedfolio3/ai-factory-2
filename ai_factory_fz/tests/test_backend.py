import pytest

from agentic_sdlc.llms.backend import Backend, CredentialsError, check_credentials, route_model, selected_backend


@pytest.mark.parametrize("value,expected", [
    ("true", Backend.CLAUDE_CODE), ("TRUE", Backend.CLAUDE_CODE), ("1", Backend.CLAUDE_CODE), ("yes", Backend.CLAUDE_CODE),
    ("false", Backend.API), ("0", Backend.API), ("", Backend.API), (None, Backend.API),
])
def test_claude_code_enable_values(value, expected):
    env = {} if value is None else {"CLAUDE_CODE_ENABLE": value}
    assert selected_backend(env) is expected


def test_unrecognised_value_is_an_error():
    with pytest.raises(CredentialsError, match="must be true or false"):
        selected_backend({"CLAUDE_CODE_ENABLE": "maybe"})


def test_route_model_only_touches_anthropic_on_claude_code():
    assert route_model("anthropic/claude-opus-5-5", Backend.CLAUDE_CODE) == "claude-code/claude-opus-5-5"
    assert route_model("anthropic/claude-opus-5-5", Backend.API) == "anthropic/claude-opus-5-5"
    assert route_model("openai/gpt-5", Backend.CLAUDE_CODE) == "openai/gpt-5"


def test_claude_code_path_requires_oauth_token():
    with pytest.raises(CredentialsError, match="CLAUDE_CODE_OAUTH_TOKEN is not set"):
        check_credentials(["claude-code/claude-opus-5-5"], env={"ANTHROPIC_API_KEY": "k"})
    check_credentials(["claude-code/claude-opus-5-5"], env={"CLAUDE_CODE_OAUTH_TOKEN": "t"})


def test_api_path_requires_api_key():
    with pytest.raises(CredentialsError, match="ANTHROPIC_API_KEY is not set"):
        check_credentials(["anthropic/claude-opus-5-5"], env={"CLAUDE_CODE_OAUTH_TOKEN": "t"})
    check_credentials(["anthropic/claude-opus-5-5"], env={"ANTHROPIC_API_KEY": "k"})


def test_other_providers_need_no_anthropic_credential():
    check_credentials(["openai/gpt-5"], env={})
