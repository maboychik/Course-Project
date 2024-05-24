import unittest
import random
from scipy.optimize import linear_sum_assignment
import numpy as np
import itertools


class TestAlgorithm(unittest.TestCase):

    def setUp(self):
        pass

    @staticmethod
    def solve(matrix):
        max_performance = 0
        for permutation in itertools.permutations(list(range(len(matrix)))):
            performance = sum(matrix[i][permutation[i]] for i in range(len(matrix)))
            max_performance = max(max_performance, performance)
        return max_performance

    def test_Graph(self):
        for i in range(5, 10):
            matrix_ef = []
            for _ in range(i):
                matrix_ef.append([0] * i)

            for row in range(0, i):
                for col in range(0, i):
                    matrix_ef[row][col] = int(random.randint(1, 10))

            self.assertEqual(self.solve(matrix_ef), self.solve(matrix_ef))

if __name__ == '__main__':
    unittest.main()
