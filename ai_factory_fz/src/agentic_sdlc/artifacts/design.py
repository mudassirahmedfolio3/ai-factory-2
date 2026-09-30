"""UI/UX artifact: design tokens, screen specs and navigation."""

from pydantic import BaseModel, Field


class ColorToken(BaseModel):
    name: str
    light: str = Field(description="Hex, e.g. #1A73E8")
    dark: str = Field(description="Hex, e.g. #8AB4F8")


class TypeStyle(BaseModel):
    name: str
    size: float
    weight: int
    line_height: float


class SharedWidget(BaseModel):
    name: str
    description: str


class ScreenSpec(BaseModel):
    id: str = Field(description="SCR-01, ...")
    name: str
    route: str = Field(description="go_router path, e.g. /products/:id")
    purpose: str
    components: list[str]
    states: list[str] = Field(description="e.g. loading, empty, error, success")
    story_ids: list[str]


class NavigationLink(BaseModel):
    from_screen: str
    to_screen: str
    trigger: str


class DesignSystem(BaseModel):
    colors: list[ColorToken]
    typography: list[TypeStyle]
    spacing: list[int] = Field(description="Spacing scale in dp")
    corner_radii: list[int]
    shared_widgets: list[SharedWidget]
    screens: list[ScreenSpec]
    navigation: list[NavigationLink]
    accessibility: list[str]

    def uncovered_stories(self, must_have_story_ids: list[str]) -> list[str]:
        covered = {sid for s in self.screens for sid in s.story_ids}
        return [sid for sid in must_have_story_ids if sid not in covered]

    def to_markdown(self) -> str:
        lines = ["# Design system", "", "## Colors", "| Token | Light | Dark |", "|---|---|---|"]
        lines += [f"| {c.name} | {c.light} | {c.dark} |" for c in self.colors]
        lines += ["", "## Typography", "| Style | Size | Weight | Line height |", "|---|---|---|---|"]
        lines += [f"| {t.name} | {t.size} | {t.weight} | {t.line_height} |" for t in self.typography]
        lines += [
            "",
            f"Spacing scale: {', '.join(map(str, self.spacing))} dp. "
            f"Corner radii: {', '.join(map(str, self.corner_radii))} dp.",
            "",
            "## Shared widgets",
        ]
        lines += [f"- **{w.name}**: {w.description}" for w in self.shared_widgets]
        lines += ["", "## Screens"]
        for s in self.screens:
            lines += [
                f"### {s.id} {s.name} (`{s.route}`)",
                s.purpose,
                f"- Components: {', '.join(s.components)}",
                f"- States: {', '.join(s.states)}",
                f"- Stories: {', '.join(s.story_ids)}",
                "",
            ]
        lines += ["## Navigation"]
        lines += [f"- {n.from_screen} → {n.to_screen}: {n.trigger}" for n in self.navigation]
        lines += ["", "## Accessibility"] + [f"- {a}" for a in self.accessibility]
        return "\n".join(lines)
