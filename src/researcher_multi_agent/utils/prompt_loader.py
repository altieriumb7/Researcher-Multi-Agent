from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.prompts_dir = prompts_dir or (base_dir / "prompts")

    def load(self, prompt_name: str) -> str:
        prompt_path = self.prompts_dir / f"{prompt_name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")
