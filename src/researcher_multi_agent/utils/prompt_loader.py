from pathlib import Path

from researcher_multi_agent.utils.prompt_renderer import render_prompt


class PromptLoader:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.prompts_dir = prompts_dir or (base_dir / "prompts")

    def load(self, prompt_name: str) -> str:
        prompt_path = self.prompts_dir / f"{prompt_name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        global_rules_path = self.prompts_dir / "global_rules.md"
        global_rules = ""
        if global_rules_path.exists():
            global_rules = global_rules_path.read_text(encoding="utf-8")

        template = prompt_path.read_text(encoding="utf-8")
        return render_prompt(template=template, global_rules=global_rules)
