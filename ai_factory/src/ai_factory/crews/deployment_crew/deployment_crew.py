from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class DeploymentCrew:
    """CI/CD pipeline generation, deploy runbook, and SRE verification."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def devops_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["devops_engineer"],  # type: ignore[index]
            llm=get_llm("fast"),
        )

    @agent
    def sre_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["sre_engineer"],  # type: ignore[index]
            llm=get_llm("fast"),
        )

    @task
    def generate_pipeline(self) -> Task:
        return Task(config=self.tasks_config["generate_pipeline"])  # type: ignore[index]

    @task
    def execute_deploy_plan(self) -> Task:
        return Task(config=self.tasks_config["execute_deploy_plan"])  # type: ignore[index]

    @task
    def post_deploy_verification(self) -> Task:
        return Task(config=self.tasks_config["post_deploy_verification"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
