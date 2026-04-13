"""
Config schema validity tests.

For every eval in evals/evals.json:
1. Generate config from prompt via SmartConfigGenerator
2. Get the corresponding toolkit skill instance
3. Run skill.validate(config)
4. Assert validation passes

This catches cases where smart_config.py generates configs
that the toolkit's skills reject.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

EVALS_PATH = Path(__file__).resolve().parent.parent / "evals" / "evals.json"


class TestConfigSchemaValidity:
    """Validate all generated configs against toolkit skill schemas."""

    def test_all_evals_produce_valid_configs(self, config_generator, toolkit_skills):
        """Run schema validation for all evals."""
        with open(EVALS_PATH) as f:
            evals_data = json.load(f)

        failed = []
        skipped = 0

        for eval_case in evals_data["evals"]:
            prompt = eval_case["prompt"]
            config = config_generator.generate_config(prompt)

            # Skip meta-configs (help, wizard, error diagnosis)
            if "help" in config or "action" in config:
                skipped += 1
                continue

            skill_name = config.get("skill")
            if not skill_name:
                failed.append({
                    "id": eval_case["id"],
                    "prompt": prompt,
                    "reason": "no skill in config"
                })
                continue

            # Skip skills not yet in toolkit
            if skill_name not in toolkit_skills:
                skipped += 1
                continue

            skill = toolkit_skills[skill_name]
            validation = skill.validate(config)

            if not validation.valid:
                failed.append({
                    "id": eval_case["id"],
                    "prompt": prompt,
                    "skill": skill_name,
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                })

        if failed:
            msg = f"\nConfig validation failures ({len(failed)} failed, {skipped} skipped):\n"
            for f_item in failed:
                msg += f"\n  [{f_item['id']}] {f_item['prompt']}\n"
                msg += f"    Skill: {f_item.get('skill', 'N/A')}\n"
                if "errors" in f_item:
                    msg += f"    Errors: {f_item['errors']}\n"
                if "reason" in f_item:
                    msg += f"    Reason: {f_item['reason']}\n"
            pytest.fail(msg)
        else:
            print(f"All configs valid ({skipped} skipped - meta/missing toolkit skills)")

    def test_common_skills_have_valid_config(self, config_generator, toolkit_skills):
        """Explicitly test the most commonly used skills."""
        common_cases = [
            ("帮我跑个IEEE39的潮流计算", "power_flow"),
            ("对IEEE3做EMT暂态仿真，仿真5秒", "emt_simulation"),
            ("对IEEE39做N-1安全校核", "n1_security"),
            ("帮我跑个短路计算，IEEE39系统，三相短路", "short_circuit"),
            ("VSI弱母线分析IEEE39", "vsi_weak_bus"),
            ("串联执行潮流和N-1分析", "study_pipeline"),
        ]

        for prompt, expected_skill in common_cases:
            config = config_generator.generate_config(prompt)
            assert config["skill"] == expected_skill, (
                f"Expected '{expected_skill}' for '{prompt}', got '{config['skill']}'"
            )

            if expected_skill in toolkit_skills:
                skill = toolkit_skills[expected_skill]
                validation = skill.validate(config)
                assert validation.valid, (
                    f"Config validation failed for '{prompt}': {validation.errors}"
                )
