"""Vancouver Yacht Group yacht management app workflow demo.

This lightweight module models the core workflow for a yacht-management
owner portal:
- monthly maintenance tasks are generated from each yacht's plan,
- field staff complete checklist items and upload before/after photos,
- owners are notified and can review service history and monthly reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class ChecklistItem:
    """A repeatable maintenance step for a yacht service task."""

    description: str
    completed: bool = False

    def mark_complete(self) -> "ChecklistItem":
        return ChecklistItem(description=self.description, completed=True)


@dataclass
class ServiceTask:
    """A monthly field-service task assigned to a staff member."""

    title: str
    checklist: list[ChecklistItem]
    assigned_to: str
    before_photos: list[str] = field(default_factory=list)
    after_photos: list[str] = field(default_factory=list)
    submitted_on: date | None = None

    @property
    def is_complete(self) -> bool:
        return all(item.completed for item in self.checklist) and self.submitted_on is not None

    def complete_checklist(self) -> None:
        self.checklist = [item.mark_complete() for item in self.checklist]

    def upload_photo(self, stage: str, photo_url: str) -> None:
        if stage == "before":
            self.before_photos.append(photo_url)
        elif stage == "after":
            self.after_photos.append(photo_url)
        else:
            raise ValueError("stage must be 'before' or 'after'")

    def submit(self, submitted_on: date) -> None:
        if not all(item.completed for item in self.checklist):
            raise ValueError("all checklist items must be complete before submission")
        self.submitted_on = submitted_on


@dataclass
class Yacht:
    """A managed yacht with an owner-facing service history."""

    name: str
    owner_name: str
    maintenance_plan: dict[str, list[str]]
    service_history: list[ServiceTask] = field(default_factory=list)

    def generate_monthly_tasks(self, assigned_to: str) -> list[ServiceTask]:
        tasks = [
            ServiceTask(
                title=task_name,
                checklist=[ChecklistItem(step) for step in checklist],
                assigned_to=assigned_to,
            )
            for task_name, checklist in self.maintenance_plan.items()
        ]
        self.service_history.extend(tasks)
        return tasks

    def completed_services_for_month(self, year: int, month: int) -> list[ServiceTask]:
        return [
            task
            for task in self.service_history
            if task.submitted_on
            and task.submitted_on.year == year
            and task.submitted_on.month == month
        ]


class OwnerPortal:
    """Owner-facing service progress, photos, history, and report tools."""

    def __init__(self, yachts: Iterable[Yacht]) -> None:
        self.yachts = {yacht.name: yacht for yacht in yachts}
        self.notifications: list[str] = []

    def notify_service_finished(self, yacht_name: str, task: ServiceTask) -> str:
        message = f"{yacht_name}: {task.title} service completed on {task.submitted_on}"
        self.notifications.append(message)
        return message

    def photos_by_task(self, yacht_name: str) -> dict[str, dict[str, list[str]]]:
        yacht = self.yachts[yacht_name]
        return {
            task.title: {
                "before": task.before_photos,
                "after": task.after_photos,
            }
            for task in yacht.service_history
        }

    def monthly_report(self, yacht_name: str, year: int, month: int) -> str:
        yacht = self.yachts[yacht_name]
        completed_services = yacht.completed_services_for_month(year, month)
        lines = [
            f"Vancouver Yacht Group Monthly Service Report",
            f"Yacht: {yacht.name}",
            f"Owner: {yacht.owner_name}",
            f"Period: {year}-{month:02d}",
            "",
            "Completed Work:",
        ]

        for task in completed_services:
            lines.append(f"- {task.title} by {task.assigned_to} on {task.submitted_on}")
            lines.append(f"  Before photos: {len(task.before_photos)}")
            lines.append(f"  After photos: {len(task.after_photos)}")

        if not completed_services:
            lines.append("- No completed services for this period")

        lines.append("")
        lines.append("PDF export ready: use this report body with the PDF renderer.")
        return "\n".join(lines)


def run_demo() -> None:
    yacht = Yacht(
        name="Pacific Horizon",
        owner_name="Vancouver Yacht Group Owner",
        maintenance_plan={
            "Hull Washdown": ["Inspect hull", "Wash waterline", "Polish stainless trim"],
            "Engine Room Check": ["Check fluids", "Inspect belts", "Record engine hours"],
        },
    )
    portal = OwnerPortal([yacht])

    monthly_tasks = yacht.generate_monthly_tasks(assigned_to="Field Team A")
    for task in monthly_tasks:
        task.upload_photo("before", f"/photos/{task.title.lower().replace(' ', '-')}-before.jpg")
        task.complete_checklist()
        task.upload_photo("after", f"/photos/{task.title.lower().replace(' ', '-')}-after.jpg")
        task.submit(date(2026, 7, 19))
        portal.notify_service_finished(yacht.name, task)

    print(portal.notifications[-1])
    print()
    print(portal.monthly_report("Pacific Horizon", 2026, 7))


if __name__ == "__main__":
    run_demo()
