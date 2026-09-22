def calculate_skill_gaps(evaluations):
    """
    Calculate a skill profile from interview evaluations.

    Supports both:
    1. Flattened evaluation objects
    2. Objects containing a nested "evaluation" object
    """

    if not evaluations:
        return {
            "skill_gaps": [],
            "skill_profile": []
        }

    grouped = {}

    for item in evaluations:

        if not isinstance(item, dict):
            continue

        nested = item.get("evaluation")

        if isinstance(nested, dict):
            evaluation = nested
        else:
            evaluation = item

        skill = str(
            item.get("skill")
            or evaluation.get("skill")
            or "Unknown"
        ).strip()

        if not skill:
            skill = "Unknown"

        try:
            score = float(
                evaluation.get("score", 0)
            )
        except (TypeError, ValueError):
            score = 0.0

        score = max(0.0, min(10.0, score))

        missing_concepts = evaluation.get(
            "missing_concepts",
            []
        )

        strengths = evaluation.get(
            "strengths",
            []
        )

        feedback = evaluation.get(
            "feedback",
            ""
        )

        if not isinstance(missing_concepts, list):
            missing_concepts = [
                str(missing_concepts)
            ]

        if not isinstance(strengths, list):
            strengths = [
                str(strengths)
            ]

        if skill not in grouped:

            grouped[skill] = {
                "scores": [],
                "missing_concepts": [],
                "strengths": [],
                "feedback": []
            }

        grouped[skill]["scores"].append(score)

        for concept in missing_concepts:

            concept = str(concept).strip()

            if (
                concept
                and concept not in
                grouped[skill]["missing_concepts"]
            ):
                grouped[skill]["missing_concepts"].append(
                    concept
                )

        for strength in strengths:

            strength = str(strength).strip()

            if (
                strength
                and strength not in
                grouped[skill]["strengths"]
            ):
                grouped[skill]["strengths"].append(
                    strength
                )

        if feedback:

            grouped[skill]["feedback"].append(
                str(feedback).strip()
            )

    skill_profile = []

    for skill, data in grouped.items():

        scores = data["scores"]

        average_score = (
            sum(scores) / len(scores)
            if scores
            else 0.0
        )

        if average_score < 4:
            level = "Needs Improvement"

        elif average_score < 7:
            level = "Intermediate"

        else:
            level = "Strong"

        feedback_text = " ".join(
            data["feedback"][:2]
        )

        skill_profile.append({

            "skill": skill,

            "average_score":
                round(average_score, 1),

            "level": level,

            "missing_concepts":
                data["missing_concepts"],

            "strengths":
                data["strengths"],

            "feedback":
                feedback_text
        })

    skill_profile.sort(
        key=lambda item:
        item["average_score"]
    )

    return {
        "skill_gaps": skill_profile,
        "skill_profile": skill_profile
    }