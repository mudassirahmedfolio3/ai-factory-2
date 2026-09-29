from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class BuildCrew:
    """Feature implementation and architecture review."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def flutter_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["flutter_engineer"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @agent
    def technical_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_architect"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def implement_features(self) -> Task:
        return Task(config=self.tasks_config["implement_features"])  # type: ignore[index]

    @task
    def architecture_review(self) -> Task:
        return Task(config=self.tasks_config["architecture_review"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
