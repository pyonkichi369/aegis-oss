"""AEGIS CLI — Command-line interface for AI governance council."""

import argparse
import json
import os
import sys
import textwrap

# ANSI color helpers (no dependencies)
_NO_COLOR = os.environ.get("NO_COLOR", "") != ""


def _c(code: str, text: str) -> str:
    if _NO_COLOR or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def green(t: str) -> str: return _c("32", t)
def red(t: str) -> str: return _c("31", t)
def yellow(t: str) -> str: return _c("33", t)
def cyan(t: str) -> str: return _c("36", t)
def dim(t: str) -> str: return _c("2", t)
def bold(t: str) -> str: return _c("1", t)


_VERDICT_FN = {"PASS": green, "FLAG": yellow, "BLOCK": red,
               "ESCALATE": yellow, "ESCALATE_TO_HUMAN": yellow, "HALT": red}

def _color_verdict(v: str) -> str: return _VERDICT_FN.get(v, str)(v)


def _get_api_key(provider: str) -> str:
    if provider == "ollama":
        return ""  # Ollama doesn't require an API key
    env_var = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
    key = os.environ.get(env_var, "")
    if not key:
        print(red(f"Error: {env_var} not set."), file=sys.stderr)
        print(dim(f"  export {env_var}=sk-..."), file=sys.stderr)
        sys.exit(1)
    return key

def cmd_convene(args):
    """Run a boardroom meeting."""
    from aegis_gov.council.boardroom import Boardroom, BoardroomConfig

    key = _get_api_key(args.provider)
    config = BoardroomConfig(
        api_key=key,
        model=args.model,
        provider=args.provider,
        max_debate_rounds=args.rounds,
    )
    boardroom = Boardroom(config=config)

    sep = cyan("=" * 60)
    print(f"\n{sep}\n{cyan(f'  AEGIS BOARDROOM — {args.category}')}\n{sep}")
    print(bold(f"  Topic: {args.topic}"))
    print(dim(f"  Model: {args.model} | Provider: {args.provider} | Rounds: {args.rounds}"))
    print(f"{sep}\n")

    # Monkey-patch _run_phase to show progress
    orig_run_phase = boardroom._run_phase

    def _patched_run_phase(phase_name, agents, user_msg):
        print(cyan(f"\n>> {phase_name}"), dim(f"({len(agents)} agent{'s' if len(agents) != 1 else ''})"))
        result = orig_run_phase(phase_name, agents, user_msg)
        print(green("   done"))
        return result

    boardroom._run_phase = _patched_run_phase

    session = boardroom.convene(
        topic=args.topic,
        category=args.category,
    )

    if args.output == "json":
        print(json.dumps(session.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"\n{sep}\n{cyan('  SYNTHESIS')}\n{sep}")
        print(session.synthesis)
        print(dim(f"\nSession: {session.session_id} | Votes: {session.vote_summary}"))


def cmd_review(args):
    """Run a standalone red team review."""
    from aegis_gov.council.boardroom import Boardroom, BoardroomConfig
    key = _get_api_key(args.provider)
    boardroom = Boardroom(config=BoardroomConfig(api_key=key, model=args.model, provider=args.provider))
    preview = args.artifact[:80] + ("..." if len(args.artifact) > 80 else "")
    print(cyan("\n>> Red Team Review"))
    print(dim(f"   Artifact: {preview}"))
    for r in boardroom.review(artifact=args.artifact):
        print(f"\n  {bold(r.reviewer)}: {_color_verdict(r.verdict.value)}")
        for f in r.findings:
            print(textwrap.fill(f, width=76, initial_indent="    ", subsequent_indent="    "))


def cmd_check(args):
    """Evaluate an action against governance rules."""
    from aegis_gov.council.rule_engine import RuleEngine

    engine = RuleEngine()

    # Parse key=value context pairs
    context = {}
    for pair in (args.context or []):
        if "=" not in pair:
            print(red(f"Invalid context format: '{pair}' (expected key=value)"))
            sys.exit(1)
        k, v = pair.split("=", 1)
        # Coerce booleans and numbers
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            try:
                v = float(v) if "." in v else int(v)
            except ValueError:
                pass
        context[k] = v

    result = engine.evaluate(agent=args.agent, action=args.action, context=context)

    verdict_str = _color_verdict(result.final_verdict.name)
    print(f"\n  Agent:   {bold(result.agent)}")
    print(f"  Action:  {result.action}")
    print(f"  Verdict: {verdict_str}")
    if context:
        print(dim(f"  Context: {context}"))
    print()

    for r in result.results:
        v = _color_verdict(r.verdict.name)
        print(f"    [{v}] {r.rule_name}: {r.message}")
    print()


def cmd_agents(args):
    """List the agent roster."""
    from aegis_gov.council.agents import DEFAULT_ROSTER

    agents = DEFAULT_ROSTER
    if args.tier:
        agents = [a for a in agents if a.tier == args.tier]

    tier_order = {"executive": 0, "reviewer": 1, "red_team": 2, "specialist": 3}
    agents = sorted(agents, key=lambda a: tier_order.get(a.tier, 9))

    current_tier = None
    for a in agents:
        if a.tier != current_tier:
            current_tier = a.tier
            print(cyan(f"\n  [{current_tier.upper()}]"))
        print(f"    {bold(a.name):.<28s} {a.role}")
        print(dim(f"    {'':.<28s} {a.expertise}"))

    print(dim(f"\n  Total: {len(agents)} agents\n"))


def cmd_rules(args):
    """List active governance rules."""
    from aegis_gov.council.rule_engine import DEFAULT_RULES

    print(cyan(f"\n  AEGIS Governance Rules ({len(DEFAULT_RULES)})\n"))
    for rid, rule in DEFAULT_RULES.items():
        v = _color_verdict(rule["verdict"])
        print(f"    {bold(rule['name'])}")
        print(f"    {dim(rid)} -> {v}")
        print(f"    {rule['description']}")
        print()


def cmd_init(args):
    """Generate a starter aegis.yaml config."""
    output = args.output
    if os.path.exists(output):
        print(yellow(f"  {output} already exists. Overwrite? [y/N] "), end="")
        if input().strip().lower() != "y":
            print(dim("  Aborted."))
            return

    content = textwrap.dedent("""\
        # AEGIS Council Configuration
        # See: https://github.com/pyonkichi369/aegis-oss
        #
        # Quick start:
        #   1. Set your API key:  export ANTHROPIC_API_KEY=sk-...
        #   2. Edit this file to match your needs
        #   3. Run:  aegis convene "your topic" --category TACTICAL

        boardroom:
          provider: anthropic          # anthropic | openai | ollama
          model: claude-sonnet-4-6
          max_debate_rounds: 2
          require_red_team: true
          require_human_approval: true
          synthesis_language: en       # en | ja

        # ---------------------------------------------------------------
        # Custom Rules
        # ---------------------------------------------------------------
        # Each rule needs: name, verdict, and optionally a condition.
        # Condition is a Python expression with access to:
        #   agent (str), action (str), context (dict), rule (dict)
        #
        # Verdicts: PASS | FLAG | BLOCK | ESCALATE_TO_HUMAN | HALT
        rules:
          low_confidence_flag:
            name: Low Confidence Flag
            description: Flag actions with confidence below threshold
            condition: "context.get('confidence', 1.0) < rule.get('threshold', 0.6)"
            verdict: FLAG
            threshold: 0.6

          # Example: require approval for large spending
          # budget_gate:
          #   name: Budget Approval
          #   condition: "context.get('amount', 0) > 10000"
          #   verdict: ESCALATE_TO_HUMAN
          #   message: "Spending over $10K needs CFO approval"

          # Example: block after-hours deployments
          # after_hours_block:
          #   name: After Hours Deploy Block
          #   condition: "action == 'deploy' and context.get('hour', 12) >= 22"
          #   verdict: BLOCK
          #   message: "No deployments after 10pm"

        # ---------------------------------------------------------------
        # Custom Agents
        # ---------------------------------------------------------------
        # Add domain-specific agents to the boardroom.
        # Tiers: executive | reviewer | specialist | red_team
        #
        # custom_agents:
        #   - name: HIPAAOfficer
        #     role: Compliance Officer
        #     expertise: "HIPAA, PHI, healthcare data protection"
        #     tier: reviewer
        #
        #   - name: DomainExpert
        #     role: Domain Specialist
        #     expertise: "Your domain expertise here"
        #     tier: specialist
    """)
    with open(output, "w") as f:
        f.write(content)
    print(green(f"  Created {output}"))
    print(dim("  Edit this file then run: aegis convene \"topic\" --config aegis.yaml"))


def cmd_version(args):
    """Print version."""
    from aegis_gov import __version__
    print(f"aegis {__version__}")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegis",
        description="AEGIS — AI Governance & Multi-Agent Council CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # convene
    p = sub.add_parser("convene", help="Run a boardroom meeting")
    p.add_argument("topic", help="Topic or question to discuss")
    p.add_argument("--category", default="TACTICAL",
                   choices=["STRATEGIC", "TACTICAL", "OPERATIONAL", "CRITICAL"])
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--provider", default="anthropic", choices=["anthropic", "openai", "ollama"])
    p.add_argument("--rounds", type=int, default=2, help="Debate rounds")
    p.add_argument("--output", default="text", choices=["json", "text"])
    p.set_defaults(func=cmd_convene)

    # review
    p = sub.add_parser("review", help="Run red team review on an artifact")
    p.add_argument("artifact", help="Artifact description to review")
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--provider", default="anthropic", choices=["anthropic", "openai", "ollama"])
    p.set_defaults(func=cmd_review)

    # check
    p = sub.add_parser("check", help="Evaluate action against governance rules")
    p.add_argument("agent", help="Agent name")
    p.add_argument("action", help="Action type (deploy, review, implement, ...)")
    p.add_argument("--context", nargs="*", metavar="key=value",
                   help="Context as key=value pairs")
    p.set_defaults(func=cmd_check)

    # agents
    p = sub.add_parser("agents", help="List the agent roster")
    p.add_argument("--tier", choices=["executive", "reviewer", "specialist", "red_team"],
                   help="Filter by tier")
    p.set_defaults(func=cmd_agents)

    # rules
    p = sub.add_parser("rules", help="List active governance rules")
    p.set_defaults(func=cmd_rules)

    # init
    p = sub.add_parser("init", help="Create starter aegis.yaml config")
    p.add_argument("--output", default="aegis.yaml", help="Output file path")
    p.set_defaults(func=cmd_init)

    # version
    p = sub.add_parser("version", help="Print version")
    p.set_defaults(func=cmd_version)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
