from app.agent.planner import AgentPlanner


def test_next_stage():

    planner = AgentPlanner()

    result = planner.next_stage(
        "REQUIREMENTS"
    )

    assert result == "DOCUMENTS"


def test_final_stage():

    planner = AgentPlanner()

    result = planner.next_stage(
        "PROOF"
    )

    assert result is None