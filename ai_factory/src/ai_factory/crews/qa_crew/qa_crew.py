from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class QACrew:
    """Quality assurance and release readiness."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def qa_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["qa_engineer"],  # type: ignore[index]
            llm=get_llm("fast"),
        )

    @task
    def test_plan(self) -> Task:
        return Task(config=self.tasks_config["test_plan"])  # type: ignore[index]

    @task
    def release_readiness(self) -> Task:
        return Task(config=self.tasks_config["release_readiness"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
