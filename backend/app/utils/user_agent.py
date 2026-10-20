"""What a request's User-Agent says about the caller's browser and operating system - for the audit
text the `admin` table's securityDetails column carries (services/admin_change_audit.py). Best effort:
an agent this doesn't recognise reads "Unknown" / "unknown", never an error."""

import re

# (name shown, version pattern), checked in this order: Edge, Opera and Samsung Internet also say
# "Chrome", and Chrome also says "Safari". The last two are the TOPS app itself - React Native's HTTP
# client on Android (okhttp) and on iOS (CFNetwork).
_BROWSERS = tuple(
    (name, re.compile(pattern))
    for name, pattern in (
        ("Microsoft Edge", r"Edg(?:e|A|iOS)?/([\d.]+)"),
        ("Opera", r"OPR/([\d.]+)"),
        ("Samsung Internet", r"SamsungBrowser/([\d.]+)"),
        ("Google Chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
        ("Mozilla Firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
        ("Safari", r"Version/([\d.]+).*Safari/"),
        ("okhttp", r"okhttp/([\d.]+)"),
        ("CFNetwork", r"CFNetwork/([\d.]+)"),
    )
)

# (text in the lower-cased agent, system shown), checked in this order: Android agents also say
# "Linux", and iPhone / iPad ones "Mac OS X".
_SYSTEMS = (
    ("windows", "windows"),
    ("android", "android"),
    ("iphone", "ios"),
    ("ipad", "ios"),
    ("macintosh", "mac"),
    ("linux", "linux"),
)


def describe(user_agent: str | None) -> tuple[str, str]:
    """(browser and its version, operating system), e.g. ("Google Chrome 124.0.0.0", "windows")."""
    agent = user_agent or ""
    browser = next(
        (f"{name} {match.group(1)}" for name, pattern in _BROWSERS if (match := pattern.search(agent))),
        "Unknown",
    )
    lowered = agent.lower()
    system = next((shown for marker, shown in _SYSTEMS if marker in lowered), "unknown")
    return browser, system
