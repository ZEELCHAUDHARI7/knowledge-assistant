# Tasks Module

The Tasks module is the core of TaskTrail. Field workers use it to see and complete their work, and supervisors use it to plan and assign work.

## Creating a task

A task has these fields:

| Field | Rules |
|---|---|
| Title | Required, maximum **120 characters** |
| Description | Optional, maximum 2,000 characters |
| Due date | Required; cannot be in the past |
| Priority | Low, Medium or High (default: Medium) |
| Assignee | One field worker |
| Location | Optional map pin |
| Checklist | Up to **10 checklist items** |

Only **Supervisors and Admins** can create and assign tasks.

## Task status flow

**To Do → In Progress → Done**

- Field workers can move their own tasks forward.
- Only Supervisors can **Reopen** a task that is Done. A reopened task goes back to In Progress.
- A task cannot be marked Done while checklist items are still unticked.

## Visibility

- **Field Workers** only see tasks assigned to them.
- **Supervisors** see all tasks in their team.
- **Admins** see all tasks in the organisation.

## Recurring tasks

Tasks can repeat **daily, weekly or monthly**. A new copy is created at midnight in the organisation's time zone. Editing a recurring task asks whether to change "this task only" or "all future tasks".

## Due dates and reminders

- A reminder notification is sent **1 hour before** the due time.
- Overdue tasks are shown in **red** at the top of the list.

## Offline behaviour

Tasks can be created and updated offline. Changes are saved in the offline sync queue and sent when the device is back online. If two people edit the same task, **the last edit wins**, and the other person sees a "This task was updated" banner.

## Key test areas

- Title length limit (120 and 121 characters)
- Checklist limit (10 and 11 items)
- Role permissions for create, assign and reopen
- Recurring task creation at midnight across time zones
- Offline edits and conflict banner
- Sorting and filtering with 500 tasks on the low-end device
