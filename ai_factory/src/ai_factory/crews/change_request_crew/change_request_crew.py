from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class ChangeRequestCrew:
    """Mid-project change request handling."""

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

    @agent
    def simulated_client(self) -> Agent:
        return Agent(
            config=self.agents_config["simulated_client"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def analyze_change_impact(self) -> Task:
        return Task(config=self.tasks_config["analyze_change_impact"])  # type: ignore[index]

    @task
    def update_backlog(self) -> Task:
        return Task(config=self.tasks_config["update_backlog"])  # type: ignore[index]

    @task
    def client_confirm_change(self) -> Task:
        return Task(config=self.tasks_config["client_confirm_change"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
