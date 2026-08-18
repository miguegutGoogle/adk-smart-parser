# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Literal, Any
from pydantic import BaseModel, Field
from google.adk import Agent, Context, Workflow
from google.adk.workflow import FunctionNode, JoinNode, Edge, DEFAULT_ROUTE

from data.cases import UNSTRUCTURED_CASES
from data.bugs import UNSTRUCTURED_BUGS

MODEL_NAME = "gemini-flash-latest"

# =====================================================================
# 1. PYDANTIC SCHEMAS FOR SMART PARSING (STRUCTURED OUTPUTS)
# =====================================================================

class CaseDetails(BaseModel):
    case_id: int = Field(..., description="Support case ID number (e.g., 10241)")
    subject: str = Field(..., description="One-line summary of the support case")
    escalated: bool = Field(..., description="True if the case has been escalated, otherwise False")
    done: str = Field(..., description="Key troubleshooting actions already completed")
    bugs: List[int] = Field(default_factory=list, description="Internal bug IDs linked to this case")
    next: str = Field(..., description="Next recommended action step to take")

class CasesReport(BaseModel):
    cases: List[CaseDetails] = Field(..., description="List of all structured cases")

class BugDetails(BaseModel):
    id: int = Field(..., description="Internal bug ID number")
    title: str = Field(..., description="Short summary of the bug")
    status: str = Field(..., description="Current bug status (e.g. Triaged, In Progress, Resolved)")
    next_step: str = Field(..., description="Next logical step to resolve this bug")

class BugsReport(BaseModel):
    bugs: List[BugDetails] = Field(..., description="List of all structured bugs")


# =====================================================================
# 2. AGENTS WITH NATIVE SMART PARSING & FAN-IN BARRIER
# =====================================================================

greeter = Agent(
    name="greeter",
    model=MODEL_NAME,
    instruction=(
        "You are a helpful support coordinator.\n"
        "Greet the user warmly and introduce this Case and Bug Analyzer.\n"
        "State clearly that you are kicking off parallel support case and bug log analysis.\n"
        "DO NOT ASK QUESTIONS INSTEAD STATE THAT YOU ARE STARTING ANALYSIS"
    ),
)

# Parallel Branch A: Native Smart Parsing via output_schema
case_analyzer = Agent(
    name="case_analyzer",
    model=MODEL_NAME,
    instruction=(
        "Analyze these unstructured support cases and map every case strictly to the schema:\n\n"
        f"{UNSTRUCTURED_CASES}\n\n"
        "IMPORTANT: ONLY parse support cases that actually appear in the text above. "
        "DO NOT invent, hallucinate, or add any extra case numbers."
    ),
    output_schema=CasesReport,
    mode="single_turn",
)

# Parallel Branch B: Native Smart Parsing via output_schema
bug_analyzer = Agent(
    name="bug_analyzer",
    model=MODEL_NAME,
    instruction=(
        "Analyze these internal bug logs and map every bug strictly to the schema:\n\n"
        f"{UNSTRUCTURED_BUGS}\n\n"
        "IMPORTANT: ONLY parse bugs that actually appear in the text above. "
        "Include links to PRs (internal.pr.tracker/...)"
        "DO NOT invent, hallucinate, or add any extra bug IDs."
    ),
    output_schema=BugsReport,
    mode="single_turn",
)

# Fan-in synchronization barrier
results_join = JoinNode(
    name="results_join",
    description="Synchronization barrier waiting for parallel case and bug analyzers to complete.",
)

report_presenter = Agent(
    name="report_presenter",
    model=MODEL_NAME,
    instruction=(
        "You are the lead support coordinator.\n"
        "Take the structured output from case_analyzer and bug_analyzer provided in your input.\n"
        "Present the EXACT cases and bugs found in your input data in two clean markdown tables:\n"
        "1. **Structured Support Cases** (columns: Case ID, Subject, Escalated, Actions Taken, Linked Bugs, Next Step)\n"
        "2. **Structured Internal Bugs** (columns: Bug ID, Title, Status, Next Step)\n"
        "IMPORTANT: You MUST ONLY include cases and bugs that are present in your input data. "
        "DO NOT hallucinate, guess, or add any extra case numbers or bug IDs that do not appear in the input."
    ),
    mode="single_turn",
)


# =====================================================================
# 3. CONDITIONAL QA LOOP (LOOP EXECUTION DEMO)
# =====================================================================

def check_need_refinement(ctx: Context, node_input: Any) -> Any:
    """Inspects report content for confidential internal links and required executive alert banner."""
    content_str = str(node_input)
    attempts = ctx.state.get("refine_attempts", 0)

    has_internal_link = "internal.pr.tracker/" in content_str
    missing_alert = "EXECUTIVE ESCALATION ALERT" not in content_str

    # If QA checks fail and we haven't hit the 3-attempt safety ceiling, route to refiner
    if (has_internal_link or missing_alert) and attempts < 3:
        ctx.state["refine_attempts"] = attempts + 1
        ctx.route = "refine"
        return node_input

    # All QA conditions passed (or safety ceiling reached): exit loop
    ctx.route = DEFAULT_ROUTE
    return node_input

loop_gate = FunctionNode(
    name="loop_gate",
    func=check_need_refinement,
)

report_refiner = Agent(
    name="report_refiner",
    model=MODEL_NAME,
    instruction=(
        "You are an Executive Support Quality Refiner.\n"
        "Your input contains a draft support report with markdown tables.\n"
        "1. Executive Alert: Prepend a prominent banner at the very top:\n"
        "   ### 🚨 EXECUTIVE ESCALATION ALERT 🚨\n"
        "   Summarize the escalated cases found in the tables below with their Case IDs.\n"
        "2. Confidentiality Redaction: Remove or redact all references to internal URLs or "
        "trackers (such as 'internal.pr.tracker/...') from the tables so the report is safe for sharing.\n"
        "3. Output the final report starting with the banner, followed by the cleaned tables."
    ),
    mode="single_turn",
)


# =====================================================================
# 4. ADK 2.0 WORKFLOW GRAPH (Sequential, Parallel & Loop Execution)
# =====================================================================

root_agent = Workflow(
    name="root_agent",
    edges=[
        # 1. Sequential Execution
        ("START", greeter),
        
        # 2. Parallel Execution (Branching)
        (greeter, (case_analyzer, bug_analyzer)),
        
        # 3. Fan-in Synchronization Barrier
        ((case_analyzer, bug_analyzer), results_join),
        
        # 4. Sequential Aggregation
        (results_join, report_presenter),
        (report_presenter, loop_gate),

        # 5. Loop Execution (Conditional Cycle with Route)
        Edge(from_node=loop_gate, to_node=report_refiner, route="refine"),
        (report_refiner, loop_gate),  # Loops back to loop_gate
    ]
)
