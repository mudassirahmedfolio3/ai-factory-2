from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from ai_factory.llm_config import get_llm


@CrewBase
class SecurityCrew:
    """AppSec worker agent — SCA, SAST, secrets, mobile OWASP."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def security_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["security_engineer"],  # type: ignore[index]
            llm=get_llm("strong"),
        )

    @task
    def security_scan(self) -> Task:
        return Task(config=self.tasks_config["security_scan"])  # type: ignore[index]

    @task
    def remediate_findings(self) -> Task:
        return Task(config=self.tasks_config["remediate_findings"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
