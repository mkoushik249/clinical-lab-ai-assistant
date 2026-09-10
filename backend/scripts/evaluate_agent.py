import json
from pathlib import Path

from app.agent import run_agent


EVAL_FILE = (
    Path(__file__).resolve().parents[1]
    / "evaluation"
    / "eval_cases.json"
)


def normalize(text: str) -> str:
    return text.casefold()


def evaluate_case(case: dict) -> tuple[bool, list[str]]:
    failures = []

    try:
        result = run_agent(
            case["question"],
            [],
        )
    except Exception as exc:
        return False, [
            f"Agent error: {type(exc).__name__}: {exc}"
        ]

    answer = result.get("answer", "")
    sources = result.get("sources", [])

    normalized_answer = normalize(answer)

    for expected_text in case.get("must_contain", []):
        if normalize(expected_text) not in normalized_answer:
            failures.append(
                f'Missing expected text: "{expected_text}"'
            )

    for forbidden_text in case.get("must_not_contain", []):
        if normalize(forbidden_text) in normalized_answer:
            failures.append(
                f'Contains forbidden text: "{forbidden_text}"'
            )

    expected_sources = case.get(
        "expected_sources",
        [],
    )

    if set(sources) != set(expected_sources):
        failures.append(
            f"Sources expected={expected_sources}, actual={sources}"
        )

    return len(failures) == 0, failures


def main() -> None:
    with EVAL_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    passed = 0
    failed = 0

    print("\nClinical Laboratory AI Assistant Evaluation")
    print("=" * 55)

    for case in cases:
        success, failures = evaluate_case(case)

        status = "PASS" if success else "FAIL"

        print(
            f"\n[{status}] "
            f"{case['id']} | "
            f"{case['category']}"
        )

        print(
            f"Question: {case['question']}"
        )

        if success:
            passed += 1
        else:
            failed += 1

            for failure in failures:
                print(f"  - {failure}")

    total = passed + failed

    print("\n" + "=" * 55)
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if total:
        pass_rate = (passed / total) * 100
        print(f"Pass rate: {pass_rate:.1f}%")


if __name__ == "__main__":
    main()
