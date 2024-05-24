import numpy as np


class TaskAssignment:
    def __init__(self, n):
        self.n = n
        self.name_arr = [input(f"Enter employee name {i + 1}: ") for i in range(n)]
        self.task_arr = [input(f"Enter task name {i + 1}: ") for i in range(n)]
        self.matrix_ef = np.zeros((n, n), dtype=int)
        self.xy_arr = np.full(n, -1)
        self.yx_arr = np.full(n, -1)
        self.vx_arr = np.zeros(n, dtype=int)
        self.vy_arr = np.zeros(n, dtype=int)
        self.max_row = np.zeros(n, dtype=int)
        self.min_col = np.zeros(n, dtype=int)

    def input_performance_levels(self):
        for i in range(self.n):
            for j in range(self.n):
                self.matrix_ef[i][j] = int(
                    input(f"Enter {self.name_arr[i]}'s performance level on {self.task_arr[j]}: "))

    def try_assign_task(self, i):
        if self.vx_arr[i] == 1:
            return False
        self.vx_arr[i] = 1
        for j in range(self.n):
            if self.matrix_ef[i][j] == self.max_row[i] + self.min_col[j]:
                self.vy_arr[j] = 1
        for j in range(self.n):
            if self.matrix_ef[i][j] == self.max_row[i] + self.min_col[j] and self.yx_arr[j] == -1:
                self.xy_arr[i] = j
                self.yx_arr[j] = i
                return True
        for j in range(self.n):
            if self.matrix_ef[i][j] == self.max_row[i] + self.min_col[j] and self.try_assign_task(self.yx_arr[j]):
                self.xy_arr[i] = j
                self.yx_arr[j] = i
                return True
        return False

    def assign_tasks(self):
        self.max_row = np.max(self.matrix_ef, axis=1)
        self.min_col = np.min(self.matrix_ef, axis=0)

        c = 0
        while c < self.n:
            self.vx_arr.fill(0)
            self.vy_arr.fill(0)
            k = 0
            for i in range(self.n):
                if self.xy_arr[i] == -1 and self.try_assign_task(i):
                    k += 1
            c += k
            if k == 0:
                z = np.inf
                for i in range(self.n):
                    if self.vx_arr[i]:
                        for j in range(self.n):
                            if not self.vy_arr[j]:
                                z = min(z, self.max_row[i] + self.min_col[j] - self.matrix_ef[i][j])
                for i in range(self.n):
                    if self.vx_arr[i]:
                        self.max_row[i] -= z
                    if self.vy_arr[i]:
                        self.min_col[i] += z

    def display_assignment(self):
        res = sum(self.matrix_ef[i][self.xy_arr[i]] for i in range(self.n))
        print(f"Total performance value: {res}")
        for i in range(self.n):
            print(f"{self.task_arr[self.xy_arr[i]]} is assigned to employee {self.name_arr[i]}")


n = int(input("Enter the number of employees: "))
task_assignment = TaskAssignment(n)
task_assignment.input_performance_levels()
task_assignment.assign_tasks()
task_assignment.display_assignment()