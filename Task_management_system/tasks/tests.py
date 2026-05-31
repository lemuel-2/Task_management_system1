from datetime import timedelta

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


# Tests for Task model behavior and task-related views.
# These tests exercise both core logic and page rendering in the Task app.


class TaskModelTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create a sample task once for the model tests.
        cls.today = timezone.localdate()
        cls.task = Task.objects.create(
            title='Sample task',
            description='A simple test task.',
            priority=Task.PRIORITY_MEDIUM,
            due_date=cls.today + timedelta(days=2),
            completed=False,
        )

    def test_task_str_returns_title(self) -> None:
        # The string representation should return the task title.
        self.assertEqual(str(self.task), 'Sample task')

    def test_is_overdue_returns_false_for_future_due_date(self) -> None:
        # A future due date should not be considered overdue.
        self.assertFalse(self.task.is_overdue)

    def test_due_status_returns_open_when_not_completed(self) -> None:
        # Open tasks should report 'Open' status.
        self.assertEqual(self.task.due_status, 'Open')

    def test_due_status_returns_completed_when_completed(self) -> None:
        # Completed tasks should report 'Completed' status.
        self.task.completed = True
        self.task.save()
        self.assertEqual(self.task.due_status, 'Completed')

    def test_due_status_returns_overdue_when_past_due(self) -> None:
        # A task with a past due date and not completed should report 'Overdue'.
        task = Task(
            title='Overdue task',
            due_date=self.today - timedelta(days=1),
            completed=False,
        )
        self.assertEqual(task.due_status, 'Overdue')

    def test_clean_raises_validation_error_for_past_due_date(self) -> None:
        # Validation should reject a due date that is before today.
        task = Task(
            title='Invalid due date',
            due_date=self.today - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            task.full_clean()


class TaskViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create a task to use in view tests.
        cls.task = Task.objects.create(
            title='View test task',
            description='Task used for view tests.',
            due_date=timezone.localdate() + timedelta(days=3),
        )

    def test_task_list_view_status_code(self) -> None:
        # Task list page should load successfully and show the task title.
        response: HttpResponse = self.client.get(reverse('tasks:task-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_list.html')
        self.assertContains(response, 'View test task')

    def test_task_detail_view_status_code(self) -> None:
        # Task detail page should load successfully for an existing task.
        response: HttpResponse = self.client.get(reverse('tasks:task-detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_detail.html')
        self.assertContains(response, 'View test task')

    def test_task_create_view_status_code(self) -> None:
        # The task creation form page should be reachable.
        response: HttpResponse = self.client.get(reverse('tasks:task-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_form.html')

    def test_task_update_view_status_code(self) -> None:
        # The task edit form should be reachable for an existing task.
        response: HttpResponse = self.client.get(reverse('tasks:task-edit', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_form.html')

    def test_task_delete_view_status_code(self) -> None:
        # The task delete confirmation page should be reachable.
        response: HttpResponse = self.client.get(reverse('tasks:task-delete', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_confirm_delete.html')
