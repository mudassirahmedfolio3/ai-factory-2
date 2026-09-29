"""Tests for UI preview HTML extraction and validation."""

from ai_factory.ui_preview_agent import extract_html_from_response, validate_preview_html

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Shop</title><style>body{margin:0}.nav{display:flex}</style></head>
<body>
<section id="login"><h1>Login</h1><form><input type="email"><input type="password"><button>Log in</button></form>
<a href="#signup">Sign Up</a></section>
<section id="signup" hidden><h1>Sign Up</h1></section>
<nav class="bottom tab-bar"><button>Home</button><button>Cart</button></nav>
<img src="https://picsum.photos/seed/coffee-blend/400/300" alt="Coffee">
<script>document.querySelector('button').addEventListener('click',()=>{});</script>
</body>
</html>"""


def test_extract_html_from_fence():
    wrapped = f"Here is the app:\n```html\n{SAMPLE_HTML}\n```"
    assert extract_html_from_response(wrapped).startswith("<!DOCTYPE html>")


def test_validate_preview_html_accepts_complete_document():
    assert validate_preview_html(SAMPLE_HTML) is True


def test_validate_preview_html_rejects_short_fragment():
    assert validate_preview_html("<html><body>login sign up</body></html>") is False
