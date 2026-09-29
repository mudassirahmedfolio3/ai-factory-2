from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class ReleaseCrew:
    """Release preparation and client-facing notes."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def release_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["release_engineer"],  # type: ignore[index]
            llm=get_llm("fast"),
        )

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["product_manager"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def prepare_release(self) -> Task:
        return Task(config=self.tasks_config["prepare_release"])  # type: ignore[index]

    @task
    def release_notes(self) -> Task:
        return Task(config=self.tasks_config["release_notes"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
