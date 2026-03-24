"""
AEGIS Boardroom — Structured Multi-Agent Governance Engine.

Orchestrates structured discussions where AI agents with distinct roles
debate, review, challenge, and vote on decisions.

Usage:
    from aegis_gov.council.boardroom import Boardroom

    boardroom = Boardroom(api_key="sk-...")
    result = await boardroom.convene(
        topic="Should we adopt microservices?",
        category="STRATEGIC",
        context={"current_arch": "monolith", "team_size": 5},
    )
    print(result.synthesis)
    print(result.vote_summary)
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agents import get_roster
from .schemas import (
    AgentRole,
    BoardroomSession,
    DecisionCategory,
    ReviewResult,
    ReviewVerdict,
    Vote,
    VotePosition,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class BoardroomConfig:
    """Configuration for a boardroom session."""
    # LLM settings
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"  # anthropic | openai
    base_url: str | None = None

    # Session settings
    max_debate_rounds: int = 2
    require_red_team: bool = True
    require_human_approval: bool = True
    synthesis_language: str = "en"  # en | ja

    # Agent roster
    custom_agents: list[AgentRole] | None = None


class Boardroom:
    """
    Structured multi-agent governance engine.

    Runs a 6-phase boardroom meeting:
      1. CEO Opening — classify topic, set format
      2. Executive Council — each C-level presents perspective
      3. Advisory Input — specialists contribute domain expertise
      4. Critical Review — red team challenges consensus
      5. Open Debate — cross-agent discussion
      6. CEO Synthesis — final decision with vote tally and confidence
    """

    def __init__(self, config: BoardroomConfig | None = None, **kwargs):
        self.config = config or BoardroomConfig(**kwargs)
        self.roster = get_roster(self.config.custom_agents)
        self._client = None

    def _get_client(self):
        """Lazy-initialize LLM client."""
        if self._client is not None:
            return self._client

        if self.config.provider == "anthropic":
            try:
                import anthropic
                kwargs = {"api_key": self.config.api_key}
                if self.config.base_url:
                    kwargs["base_url"] = self.config.base_url
                self._client = anthropic.Anthropic(**kwargs)
            except ImportError:
                raise ImportError("pip install anthropic")
        elif self.config.provider == "openai":
            try:
                import openai
                kwargs = {"api_key": self.config.api_key}
                if self.config.base_url:
                    kwargs["base_url"] = self.config.base_url
                self._client = openai.OpenAI(**kwargs)
            except ImportError:
                raise ImportError("pip install openai")
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

        return self._client

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt template from the prompts directory."""
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text()
        return ""

    def _load_manifesto(self) -> str:
        """Load the governance manifesto."""
        path = PROMPTS_DIR / "manifesto.md"
        if path.exists():
            return path.read_text()
        return ""

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call the LLM with a system prompt and user message."""
        client = self._get_client()

        if self.config.provider == "anthropic":
            response = client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text

        elif self.config.provider == "openai":
            response = client.chat.completions.create(
                model=self.config.model,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content

        return ""

    def _build_agent_prompt(self, agent: AgentRole, phase: str, context: str) -> str:
        """Build a system prompt for an agent in a specific phase."""
        manifesto = self._load_manifesto()
        role_prompt = ""
        if agent.prompt_file:
            role_prompt = self._load_prompt(agent.prompt_file)

        return f"""You are {agent.name} ({agent.role}) in an AEGIS Council boardroom meeting.

## Your Expertise
{agent.expertise}

## Governance Framework
{manifesto[:2000] if manifesto else "Follow structured governance principles."}

{f"## Role-Specific Instructions{chr(10)}{role_prompt[:3000]}" if role_prompt else ""}

## Phase: {phase}
Provide your perspective concisely (2-4 sentences). Be authentic to your role.
Focus on evidence and frameworks, not opinions. Flag disagreements directly.
"""

    def convene(
        self,
        topic: str,
        category: str = "TACTICAL",
        context: dict[str, Any] | None = None,
        on_event: "callable | None" = None,
    ) -> BoardroomSession:
        """
        Run a full boardroom meeting.

        Args:
            topic: The decision or question to discuss
            category: CRITICAL | STRATEGIC | TACTICAL | OPERATIONAL
            context: Additional context for the discussion
            on_event: Optional callback invoked at each phase milestone.
                Receives a dict with keys: type, phase, and optional data.

        Returns:
            BoardroomSession with full meeting record
        """
        def _emit(event_type: str, phase: str, **kwargs):
            if on_event:
                on_event({"type": event_type, "phase": phase, **kwargs})

        cat = DecisionCategory(category)
        session = BoardroomSession(topic=topic, category=cat)
        ctx_str = json.dumps(context or {}, indent=2)

        logger.info(f"Boardroom convened: {topic} [{category}]")

        # Phase 1: CEO Opening
        _emit("phase_start", "opening")
        ceo = next((a for a in self.roster if a.name == "CEO"), None)
        if ceo is None:
            raise ValueError("Roster must include an agent named 'CEO'. Add one or use the default roster.")
        opening = self._run_phase(
            "Phase 1: CEO Opening",
            [ceo],
            f"Topic: {topic}\nCategory: {category}\nContext: {ctx_str}\n\n"
            "Open the meeting: restate topic, classify importance, "
            "identify key stakeholders, set debate format.",
            on_event=on_event,
        )
        session.phases.append({"phase": "opening", "content": opening})
        _emit("phase_complete", "opening")

        # Phase 2: Executive Council
        _emit("phase_start", "executive_council")
        executives = [a for a in self.roster if a.tier == "executive"]
        exec_input = self._run_phase(
            "Phase 2: Executive Council",
            executives,
            f"Topic: {topic}\nContext: {ctx_str}\n\n"
            "Present your perspective on this topic (2-3 sentences). "
            "Focus on your domain expertise.",
            on_event=on_event,
        )
        session.phases.append({"phase": "executive_council", "content": exec_input})
        _emit("phase_complete", "executive_council")

        # Phase 3: Advisory & Specialist Input
        _emit("phase_start", "advisory")
        advisors = [a for a in self.roster if a.tier == "specialist"]
        advisory_input = self._run_phase(
            "Phase 3: Advisory Input",
            advisors,
            f"Topic: {topic}\nContext: {ctx_str}\n"
            f"Executive perspectives:\n{exec_input[:2000]}\n\n"
            "Contribute your domain expertise (2-3 sentences).",
            on_event=on_event,
        )
        session.phases.append({"phase": "advisory", "content": advisory_input})
        _emit("phase_complete", "advisory")

        # Phase 4: Critical Review (Red Team)
        if self.config.require_red_team:
            _emit("phase_start", "critical_review")
            red_team = [a for a in self.roster if a.tier == "red_team"]
            reviewers = [a for a in self.roster if a.tier == "reviewer"]
            critical = self._run_phase(
                "Phase 4: Critical Review",
                red_team + reviewers,
                f"Topic: {topic}\nContext: {ctx_str}\n"
                f"Discussion so far:\n{exec_input[:1500]}\n{advisory_input[:1500]}\n\n"
                "Challenge the emerging consensus. Find risks, gaps, and flaws. "
                "You MUST challenge even if you agree.",
                on_event=on_event,
            )
            session.phases.append({"phase": "critical_review", "content": critical})
            _emit("phase_complete", "critical_review")

        # Phase 5: Open Debate (exclude CEO to avoid duplication with Phase 1)
        _emit("phase_start", "debate")
        debate_agents = [a for a in self.roster if a.name != "CEO"]
        all_perspectives = "\n".join(
            p.get("content", "") for p in session.phases
        )
        debate = self._run_phase(
            "Phase 5: Open Debate",
            debate_agents,
            f"Topic: {topic}\n"
            f"All perspectives so far:\n{all_perspectives[:4000]}\n\n"
            "Respond to other agents' points. Flag agreements and disagreements. "
            "Red team must challenge at least one consensus point.",
            on_event=on_event,
        )
        session.phases.append({"phase": "debate", "content": debate})
        _emit("phase_complete", "debate")

        # Phase 6: CEO Synthesis
        _emit("phase_start", "synthesis")
        synthesis_prompt = self._build_synthesis_prompt(topic, category, session, ctx_str)
        synthesis = self._call_llm(
            "You are AI_CEO synthesizing a boardroom meeting. "
            f"Output language: {self.config.synthesis_language}. "
            "Be decisive. Include vote tally, risk assessment, and clear recommendation. "
            "You MUST include a structured vote tally in the format: "
            "VOTE_TALLY: approve=N, conditional=N, reject=N, abstain=N "
            "and a CONFIDENCE: 0.X line based on consensus strength.",
            synthesis_prompt,
        )
        session.synthesis = synthesis

        # Parse confidence from synthesis
        conf_match = re.search(r"CONFIDENCE:\s*(0\.\d+|1\.0)", synthesis)
        if conf_match:
            session.confidence = float(conf_match.group(1))
        else:
            logger.warning("Could not parse CONFIDENCE from synthesis; defaulting to 0.0")

        # Parse vote tally from synthesis
        vote_match = re.search(
            r"VOTE_TALLY:\s*approve=(\d+),\s*conditional=(\d+),\s*reject=(\d+),\s*abstain=(\d+)",
            synthesis,
        )
        if vote_match:
            for position, count in zip(
                [VotePosition.APPROVE, VotePosition.CONDITIONAL, VotePosition.REJECT, VotePosition.ABSTAIN],
                vote_match.groups(),
            ):
                for i in range(int(count)):
                    session.votes.append(Vote(agent=f"agent_{position.value}_{i}", position=position))

        _emit("phase_complete", "synthesis")
        logger.info(f"Boardroom concluded: {topic}")
        return session

    def _run_phase(
        self, phase_name: str, agents: list[AgentRole], user_msg: str,
        on_event: "callable | None" = None,
    ) -> str:
        """Run a phase with multiple agents and collect responses."""
        responses = []
        for agent in agents:
            try:
                system = self._build_agent_prompt(agent, phase_name, user_msg)
                response = self._call_llm(system, user_msg)
                responses.append(f"**{agent.name}** ({agent.role}):\n{response}")
                logger.debug(f"  {agent.name}: responded")
                if on_event:
                    on_event({
                        "type": "agent_response",
                        "phase": phase_name,
                        "agent": agent.name,
                        "role": agent.role,
                        "content": response,
                    })
            except Exception as e:
                logger.warning(f"  {agent.name}: failed — {e}")
                responses.append(f"**{agent.name}**: [No response — {e}]")
                if on_event:
                    on_event({
                        "type": "agent_error",
                        "phase": phase_name,
                        "agent": agent.name,
                        "error": str(e),
                    })

        return "\n\n---\n\n".join(responses)

    def _build_synthesis_prompt(
        self, topic: str, category: str, session: BoardroomSession, context: str
    ) -> str:
        """Build the synthesis prompt from all meeting phases."""
        phases_text = ""
        for p in session.phases:
            phases_text += f"\n## {p['phase'].upper()}\n{p.get('content', '')[:2000]}\n"

        lang_instruction = ""
        if self.config.synthesis_language == "ja":
            lang_instruction = (
                "Write the synthesis in Japanese (ですます調). "
                "Use clear, professional Japanese. "
                "Technical terms may remain in English."
            )

        return f"""Synthesize this boardroom meeting into a final decision.

Topic: {topic}
Category: {category}
Context: {context}

{phases_text}

## Instructions
1. Summarize the recommendation with confidence score (0.0-1.0)
2. List consensus points with real-world impact (「つまり」)
3. List contested points with CEO judgment
4. Risk assessment table with severity (🔴🟠🟡🟢)
5. Vote tally from all participating agents
6. Action items with timeline

{lang_instruction}
"""

    def review(
        self,
        artifact: str,
        reviewer_tiers: list[str] | None = None,
    ) -> list[ReviewResult]:
        """
        Run a standalone review (without full boardroom meeting).

        Useful for quick red-team reviews of code, proposals, or decisions.
        """
        tiers = reviewer_tiers or ["reviewer", "red_team"]
        reviewers = [a for a in self.roster if a.tier in tiers]
        results = []

        for agent in reviewers:
            system = self._build_agent_prompt(agent, "Review", artifact)
            try:
                response = self._call_llm(
                    system,
                    f"Review this artifact and end with exactly one of: "
                    f"VERDICT: PASS, VERDICT: FLAG, VERDICT: BLOCK, VERDICT: ESCALATE, or VERDICT: HALT\n\n{artifact}",
                )
                # Parse verdict from response
                verdict = ReviewVerdict.FLAG  # default: conservative
                for v in ReviewVerdict:
                    if f"VERDICT: {v.value}" in response:
                        verdict = v
                        break

                result = ReviewResult(
                    reviewer=agent.name,
                    verdict=verdict,
                    findings=[response],
                    reasoning=response,
                )
                results.append(result)
            except Exception as e:
                logger.warning("Review failed for %s: %s", agent.name, e)

        return results
