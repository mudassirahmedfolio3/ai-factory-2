from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class DesignCrew:
    """Architecture and Flutter scaffold planning."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def technical_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_architect"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @agent
    def flutter_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["flutter_engineer"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def recommend_backend_scope(self) -> Task:
        return Task(config=self.tasks_config["recommend_backend_scope"])  # type: ignore[index]

    @task
    def mobile_architecture(self) -> Task:
        return Task(config=self.tasks_config["mobile_architecture"])  # type: ignore[index]

    @task
    def sprint_zero_setup(self) -> Task:
        return Task(config=self.tasks_config["sprint_zero_setup"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
