import numpy as np
import pandas as pd
import time
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


def generate_random_matrices_and_labels(num_matrices, matrix_size):
    matrices = [np.random.randint(0, 100, size=(matrix_size, matrix_size)).flatten() for _ in range(num_matrices)]
    labels = np.random.randint(0, 2, size=num_matrices)  # Assuming binary classification
    return np.array(matrices), labels


def measure_execution_time(matrix_size):
    # Generate random data
    X, y = generate_random_matrices_and_labels(1000, matrix_size)  # Generate 1000 random matrices
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

    clf = DecisionTreeClassifier(criterion="entropy", max_depth=20, min_samples_leaf=1, min_samples_split=2)

    start_time = time.time()
    clf = clf.fit(x_train, y_train)
    training_time = time.time() - start_time

    start_time = time.time()
    y_pred = clf.predict(x_test)
    prediction_time = time.time() - start_time

    training_accuracy = clf.score(x_train, y_train)
    testing_accuracy = clf.score(x_test, y_test)

    return training_time, prediction_time, training_accuracy, testing_accuracy


results = []
matrix_sizes = range(10, 101, 10)  
for size in matrix_sizes:
    training_time, prediction_time, train_acc, test_acc = measure_execution_time(size)
    results.append((size, training_time, prediction_time, train_acc, test_acc))
    print(f"Размер матрицы: {size}x{size}, Время обучения: {training_time:.4f}s, Время предсказывания: {prediction_time:.4f}s, f"Точность на обучении: {train_acc:.4f}, Точность на тестировании: {test_acc:.4f}")

results_df = pd.DataFrame(results, columns=["Размер матрицы", "Время обучения (s)", " Время предсказывания(s)", "Точность на обучении","Точность на тестировании"])

print(results_df)

fig, ax1 = plt.subplots()

ax1.set_xlabel('Matrix Size')
ax1.set_ylabel('Time (s)')
ax1.plot(results_df["Matrix Size"], results_df["Training Time (s)"], label='Training Time', color='tab:blue')
ax1.plot(results_df["Matrix Size"], results_df["Prediction Time (s)"], label='Prediction Time', color='tab:orange')
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
ax2.set_ylabel('Accuracy')
ax2.plot(results_df["Matrix Size"], results_df["Training Accuracy"], label='Training Accuracy', color='tab:green')
ax2.plot(results_df["Matrix Size"], results_df["Testing Accuracy"], label='Testing Accuracy', color='tab:red')
ax2.legend(loc='upper right')

fig.tight_layout()
plt.title("Performance of Decision Tree Classifier with Different Matrix Sizes")
plt.show()
