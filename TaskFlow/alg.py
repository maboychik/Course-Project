import numpy as np
from queue import Queue

class TaskAssignment:
    def __init__(self, employee_names, task_names, performance_matrix, task_priorities, task_deadlines, max_tasks):
        self.employee_names = employee_names
        self.task_names = task_names
        self.n = len(employee_names)
        self.m = len(task_names)
        self.performance_matrix = np.array(performance_matrix)
        self.task_priorities = np.array(task_priorities)
        self.task_deadlines = np.array(task_deadlines)  # Дедлайны задач
        self.assignments = np.full(self.n, -1)
        self.task_to_employee = np.full(self.m, -1)
        self.max_row = np.zeros(self.n)
        self.min_col = np.zeros(self.m)
        self.vx_arr = np.zeros(self.n)
        self.vy_arr = np.zeros(self.m)
        self.max_tasks = max_tasks
        self.current_tasks = np.zeros(self.n, dtype=int)  # Текущая загрузка сотрудников
        self.unassigned_tasks_queue = Queue()  # Очередь неназначенных задач

    def adjust_performance(self):
        """
        Корректируем производительность задач с учетом приоритетов и дедлайнов.
        """
        adjusted_matrix = np.zeros((self.n, self.m))
        for i in range(self.n):
            for j in range(self.m):
                priority_factor = self.task_priorities[j] / 10
                deadline_factor = 1 / self.task_deadlines[j]  # Чем ближе дедлайн, тем выше фактор
                adjusted_matrix[i][j] = self.performance_matrix[i][j] * priority_factor * deadline_factor
        return adjusted_matrix

    def try_assign_task(self, employee, adjusted_matrix):
        if self.vx_arr[employee]:
            return False
        self.vx_arr[employee] = 1
        for task in range(self.m):
            if adjusted_matrix[employee][task] == self.max_row[employee] + self.min_col[task]:
                if self.vy_arr[task] or self.current_tasks[employee] >= self.max_tasks[employee]:
                    continue
                self.vy_arr[task] = 1
                if self.task_to_employee[task] == -1 or self.try_assign_task(self.task_to_employee[task], adjusted_matrix):
                    self.assignments[employee] = task
                    self.task_to_employee[task] = employee
                    self.current_tasks[employee] += 1  # Увеличиваем текущую загрузку сотрудника
                    return True
        return False

    def assign_tasks(self):
        adjusted_matrix = self.adjust_performance()
        self.max_row = np.max(adjusted_matrix, axis=1)
        self.min_col = np.min(adjusted_matrix, axis=0)

        while -1 in self.assignments:
            self.vx_arr.fill(0)
            self.vy_arr.fill(0)
            for employee in range(self.n):
                if self.assignments[employee] == -1 and self.current_tasks[employee] < self.max_tasks[employee]:
                    if self.try_assign_task(employee, adjusted_matrix):
                        break
            else:
                delta = float('inf')
                for i in range(self.n):
                    if self.vx_arr[i]:
                        for j in range(self.m):
                            if not self.vy_arr[j]:
                                delta = min(delta, self.max_row[i] + self.min_col[j] - adjusted_matrix[i][j])
                for i in range(self.n):
                    if self.vx_arr[i]:
                        self.max_row[i] -= delta
                for j in range(self.m):
                    if self.vy_arr[j]:
                        self.min_col[j] += delta

        # Проверка на неназначенные задачи
        for task in range(self.m):
            if self.task_to_employee[task] == -1:
                self.unassigned_tasks_queue.put(task)

    def reassign_unassigned_tasks(self):
        while not self.unassigned_tasks_queue.empty():
            task = self.unassigned_tasks_queue.get()
            self.vx_arr.fill(0)
            self.vy_arr.fill(0)
            assigned = False
            adjusted_matrix = self.adjust_performance()
            for employee in range(self.n):
                if self.current_tasks[employee] < self.max_tasks[employee]:
                    if self.try_assign_task(employee, adjusted_matrix):
                        assigned = True
                        break
            if not assigned:
                self.unassigned_tasks_queue.put(task)  # Если не удалось назначить, вернуть задачу в очередь

    def display_assignment(self):
        total_performance = sum(self.performance_matrix[emp][self.assignments[emp]] for emp in range(self.n) if self.assignments[emp] != -1)
        print(f"Общая производительность: {total_performance}")
        for emp in range(self.n):
            if self.assignments[emp] != -1:
                print(f"Задача {self.task_names[self.assignments[emp]]} назначена сотруднику {self.employee_names[emp]}")
            else:
                print(f"Сотруднику {self.employee_names[emp]} не назначена задача")

        if not self.unassigned_tasks_queue.empty():
            print("\nНеназначенные задачи:")
            while not self.unassigned_tasks_queue.empty():
                task = self.unassigned_tasks_queue.get()
                print(f"Задача {self.task_names[task]}")
                self.unassigned_tasks_queue.put(task)  # Вернуть задачу в очередь для последующих попыток назначения

# Пример использования:
employee_names = ["Алиса", "Боб", "Чарли"]
task_names = ["Задача1", "Задача2", "Задача3", "Задача4"]
performance_matrix = [
    [9, 2, 7, 6],
    [6, 4, 3, 8],
    [5, 8, 1, 5]
]
task_priorities = [10, 2, 5, 10]  # Приоритеты задач от 1 до 10
task_deadlines = [1, 5, 3, 2]  # Дедлайны задач в днях
max_tasks = [2, 2, 2]  # Максимальное количество задач, которые может взять каждый сотрудник

task_assignment = TaskAssignment(employee_names, task_names, performance_matrix, task_priorities, task_deadlines, max_tasks)
task_assignment.assign_tasks()
task_assignment.reassign_unassigned_tasks()  # Попытка перераспределения неназначенных задач
task_assignment.display_assignment()
