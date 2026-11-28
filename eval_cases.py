#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:33:01 2026

@author: walidajalil
"""

import csv
import json
from agent import run_agent
import anyio


def load_labels():
    labels = {}

    with open("datasets/loghub/hadoop/full/hadoop_labels.csv") as f:
        reader = csv.DictReader(f)

        for row in reader:
            labels[row["application_id"]] = row["label"]

    return labels


results = load_labels()


async def evaluate_case(application_id, expected_label):
    user_prompt = """Investigate Hadoop application "[APPLICATION_ID]" using the Hadoop log-search tool.

Classify it as exactly one of:
Normal | Machine down | Network disconnection | Disk full

Use only evidence from this application. Tools and runbooks for synthetic API incidents are not relevant.

INVESTIGATION

1. Make separate, short searches for storage, node availability, and network transport failures. Useful initial queries are:
   - "FSError"
   - "lost node"
   - "NoRouteToHostException"

   These are search starting points, not classification rules.

2. Inspect the actual returned log text. BM25 ranks matching words; a returned chunk does not guarantee that the requested phrase or event is present. A "No matches found" tool message is not a log event.

3. If the findings are ambiguous, follow up on the affected host/IP and a different symptom. Useful queries include:
   - "unusable node"
   - "Retrying connect"
   - "Failed to renew lease"
   - "ERROR IN CONTACTING RM"
   - "not enough space"

   Search for observed log wording rather than category names such as "network disconnection".

4. Examine INFO messages and nested "Caused by" lines. Identify who cannot reach whom, which service is affected, and what happened before and after the failure.

5. Prefer complementary searches over repeated copies of the same evidence. An empty search or a shortened result does not establish that a failure category is absent.

INTERPRETATION

- Machine down:
  Favor this when multiple observations support loss of a particular worker across its tasks/services. A lost or unusable node supports unavailability but does not prove power loss.

- Network disconnection:
  Favor this when observations support disrupted communication paths, considering the source, destination, and activity on the affected host. NoRouteToHostException is relevant but can also occur during a machine failure. Continued local logging alone is not decisive.

- Disk full:
  Look for an explicit filesystem capacity error, possibly nested under ShuffleError, Spill failed, or another task failure. "Lack of space for maps" alone does not establish disk exhaustion.

- Normal:
  Use this when targeted checks and the observed workflow provide no convincing failure-specific sequence. Isolated connection closures and ordinary container cleanup do not establish an injected fault. Successful completion alone is insufficient.

Additional distinctions:
- A job may succeed after recovering from a failure.
- "Resource Manager doesn't recognize AttemptId" reports an application-attempt/state problem. It is not by itself proof of a network transport outage.
- Do not classify from a single keyword, application ID, timestamp prefix, or hostname.
- Do not invent missing events or assume an unexamined service was healthy.

EXAMPLES

These are selected, genuine log-message fragments from other applications. They are not consecutive full logs and are not evidence for the application requested above. Context notes describe relationships established in those example applications.

Example 1

Log fragments:
"An existing connection was forcibly closed by the remote host"
"Job Transitioned from COMMITTING to SUCCEEDED"

Context:
Task progress and completion continue. Targeted inspection establishes no corroborating node-loss, routing-failure, or disk-capacity sequence.

Answer:
{
  "label": "Normal",
  "explanation": "The connection closure is not accompanied by a failure-specific sequence in the reviewed evidence. The observed workflow supports Normal; job success alone would not establish that conclusion."
}

Example 2

Log fragments:
"Retrying connect to server: 04DN8IQ.fareast.corp.microsoft.com/10.86.164.9:64484"
"Bad connect ack with firstBadLink as 10.86.164.9:50010"
"Excluding datanode 10.86.164.9:50010"
"Container released on a *lost* node"

Context:
The NodeManager and DataNode endpoints belong to the same worker. Its task logs stop while other workers continue.

Answer:
{
  "label": "Machine down",
  "explanation": "Stopped work on one worker, repeated NodeManager connection failures, and a DataNode problem on the same IP support worker-wide unavailability. Lost-node and connection-error messages are symptoms; a network partition cannot be excluded with certainty."
}

Example 3

Log fragments:
"INFO [communication thread]"
"Communication exception: java.net.NoRouteToHostException"
"No Route to Host from  MININT-FNANLI5/127.0.0.1 to 10.190.173.170:29630"
"Container released on a *lost* node"

Context:
The transport errors are emitted by a running task on MININT-FNANLI5. The ApplicationMaster later reports that worker lost. The NoRoute errors occur before the lost-node notification.

Answer:
{
  "label": "Network disconnection",
  "explanation": "Explicit routing failures emitted by a local task support disrupted communication, while the later lost-node report shows Hadoop's response to unreachability. Lost-node wording does not override the transport evidence. The physical cause is not uniquely established."
}

Example 4

Log fragments from one exception chain:
"Shuffle$ShuffleError: error in shuffle in fetcher#1"
"Caused by: org.apache.hadoop.fs.FSError: java.io.IOException: There is not enough space on the disk"

Answer:
{
  "label": "Disk full",
  "explanation": "The nested exception explicitly identifies a local disk-capacity failure. ShuffleError is the higher-level symptom; the capacity error is the stronger diagnostic evidence."
}

SEARCH-BEHAVIOR EXAMPLE

Search query:
"network disconnection"

Tool response:
{"message": "No matches found for query: network disconnection"}

Appropriate next action:
Search for a concrete signature such as "NoRouteToHostException", or investigate the endpoint implicated by earlier logs. This tool response does not show that networking was healthy.

FINAL ANSWER

Now investigate "[APPLICATION_ID]".

Use only evidence retrieved for this application. Do not reuse observations from the examples as if they belonged to this application.

Before answering, compare the best-supported class with its strongest plausible alternative. Base the choice on distinguishing observations, not merely a generic symptom.

If the logs do not distinguish the causes confidently, still choose the most likely allowed label and briefly state the uncertainty.

Return only valid JSON with exactly two fields:
- "label": exactly "Normal", "Machine down", "Network disconnection", or "Disk full".
- "explanation": 1-3 concise sentences using evidence actually retrieved for this application. Include a source filename/line if available. Do not invent citations.
""".replace("[APPLICATION_ID]", application_id)

    prompt = [
        {
            "role": "system",
            "content": "Use the available tools when needed.",
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    raw_output = await run_agent(prompt)
    output = raw_output

    try:
        output = json.loads(output)
    except json.JSONDecodeError:
        print("Invalid JSON output:", repr(output))

        return {
            "application_id": application_id,
            "expected": expected_label,
            "predicted": output["label"],
            "correct": output["label"] == expected_label,
            "explanation": output["explanation"],
            "messages": prompt,
            "raw_output": raw_output,
        }

    return {
        "application_id": application_id,
        "expected": expected_label,
        "predicted": output["label"],
        "correct": output["label"] == expected_label,
        "explanation": output["explanation"],
        "messages": prompt,
        "raw_output": raw_output,
    }


async def main():
    for run_counter in range(1, 2):
        step_counter = 1
        evaluations = []

        for application_id, expected_label in results.items():
            print("\nRun: ", run_counter)
            print("Step: ", step_counter)

            result = await evaluate_case(application_id, expected_label)
            evaluations.append(result)

            with open(
                f"eval_results/eval_results_no_examples_debug_run{run_counter}.jsonl",
                "a",
            ) as f:
                f.write(json.dumps(result) + "\n")

            step_counter += 1

        correct = sum(result["correct"] for result in evaluations)
        total = len(evaluations)

        print(f"\nCorrect: {correct}/{total}")
        print(f"Accuracy: {correct / total:.1%}")

    return evaluations


evaluations = anyio.run(main)
