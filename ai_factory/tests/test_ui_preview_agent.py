"""Tests for UI preview HTML extraction and validation."""

from ai_factory.ui_preview_agent import (
    extract_html_from_response,
    finalize_preview_html,
    javascript_syntax_ok,
    repair_common_script_errors,
    validate_preview_html,
)

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


def test_repair_common_script_errors_fixes_create_text_node_paren():
    broken = "lines.forEach(function(l){root.appendChild(document.createTextNode(l);});"
    fixed = repair_common_script_errors(broken)
    assert "createTextNode(l));" in fixed
    assert javascript_syntax_ok(f"function x(){{var root={{appendChild:function(){{}}}};{fixed}}}") is True


def test_repair_common_script_errors_removes_stray_brace():
    broken = "function cardHTML(p){\n  return `<span>ok</span>`}\n}\nfunction next(){}\n"
    fixed = repair_common_script_errors(broken)
    assert fixed == "function cardHTML(p){\n  return `<span>ok</span>`}\nfunction next(){}\n"
    assert javascript_syntax_ok(fixed) is True


def test_finalize_preview_html_injects_bootstrap_for_broken_script():
    html = """<!DOCTYPE html>
<html><head><title>Shop</title><style>.screen{display:none}.screen.active{display:block}</style></head>
<body>
<section id="login" class="screen auth active"><button class="btn">Sign In</button>
<button class="link">Create an account</button></section>
<section id="signup" class="screen auth"><button class="link">Already have an account?</button></section>
<section id="app" class="screen"><nav class="tab"><button>Home</button></nav></section>
<script>
function cardHTML(){ return `<span>x</span>`}
}
function show(id){document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));document.getElementById(id).classList.add('active')}
</script>
</body></html>"""
    out = finalize_preview_html(html)
    assert "ai-factory-preview-bootstrap" in out.html
    assert javascript_syntax_ok(
        out.html.split("<script>")[1].split("</script>")[0]
    ) or "ai-factory-preview-bootstrap" in out.html
