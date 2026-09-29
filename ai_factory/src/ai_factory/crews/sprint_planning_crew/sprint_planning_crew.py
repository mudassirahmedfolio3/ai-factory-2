from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class SprintPlanningCrew:
    """Sprint scope selection and task breakdown."""

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
    def flutter_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["flutter_engineer"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def select_sprint_scope(self) -> Task:
        return Task(config=self.tasks_config["select_sprint_scope"])  # type: ignore[index]

    @task
    def break_into_tasks(self) -> Task:
        return Task(config=self.tasks_config["break_into_tasks"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
