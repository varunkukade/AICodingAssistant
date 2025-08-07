Here are the tools available to the agent.
<img width="1935" height="683" alt="Screenshot 2025-07-24 at 8 22 48 PM" src="https://github.com/user-attachments/assets/446e4905-4915-4a59-9d5a-22187b89665e" />

Here is the high level flow of agent
<img width="1594" height="692" alt="Screenshot 2025-07-31 at 11 02 00 PM" src="https://github.com/user-attachments/assets/c618d6d7-8b25-4ac9-93f9-2d600a37a638" />

How Agent works: 

1. Node Planner: Creates a plan of steps.
2. Node Executor: Executes those step one by one

Replanning: After executing each step, we decide whether to replan or not. If we need to replan, we return to Node Planner.

3. Node Workflow Completed: If no need of replanning but all steps commpleted, we navigate to Workflow Completed
4. Node Workflow Terminated: From any of the task, if we find that workflow should end, we navigate to Workflow Terminated

If we find that there is no need to replan, no need to complete workflow and also no need to terminate workflow, we again navigate to Node Executor to execute next step in the plan.
