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

import os
from google.genai import types
from google.adk.runners import InMemoryRunner
try:
    from case_analyzer.agent import root_agent
except ImportError:
    from agent import root_agent

def run_pipeline():
    print("🚀 Initializing ADK 2.0 Support Case & Bug Analyzer Workflow...")
    print("Graph Nodes:", [n.name for n in root_agent.graph.nodes])
    print("-" * 75)

    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ NOTE: Please make sure GEMINI_API_KEY environment variable is set to execute live Gemini model calls.")

    runner = InMemoryRunner(node=root_agent)
    
    print("\nStarting execution session 'demo_session'...")
    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text("Start analysis")]
    )

    try:
        for event in runner.run(
            user_id="demo_user",
            session_id="demo_session",
            new_message=user_msg
        ):
            node_name = getattr(event, "name", getattr(event, "path", "system"))
            route = getattr(event, "route", None)
            route_info = f" [ROUTE: {route}]" if route else ""
            
            output_text = ""
            if hasattr(event, "content") and event.content and event.content.parts:
                output_text = event.content.parts[0].text
            elif hasattr(event, "output") and event.output:
                output_text = str(event.output)

            print(f"\n[⚡ NODE COMPLETED: {node_name}]{route_info}")
            if output_text:
                preview = output_text if len(output_text) < 400 else output_text[:400] + "\n... [truncated]"
                print(preview)
                print("-" * 75)
    except Exception as e:
        print(f"\n❌ Execution stopped: {e}")

if __name__ == "__main__":
    run_pipeline()
