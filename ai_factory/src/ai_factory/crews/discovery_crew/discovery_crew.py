from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class DiscoveryCrew:
    """Requirements discovery and PRD creation."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["product_manager"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @agent
    def ecommerce_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["ecommerce_advisor"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def intake_client_brief(self) -> Task:
        return Task(config=self.tasks_config["intake_client_brief"])  # type: ignore[index]

    @task
    def write_prd(self) -> Task:
        return Task(config=self.tasks_config["write_prd"])  # type: ignore[index]

    @task
    def domain_review(self) -> Task:
        return Task(config=self.tasks_config["domain_review"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
