from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import make_scorer, accuracy_score
from sklearn.model_selection import train_test_split

import numpy as np
import pandas
import ast

data = pandas.read_csv("dataset.csv", sep=';')

#print(data.head())

x = data["Matrix"].apply(ast.literal_eval)
x = x.apply(lambda row: [list(map(int, sublist)) for sublist in row])

flattened_matrices = [np.array(matrix).flatten() for matrix in x]
X = np.array(flattened_matrices)
y = data['Res']

x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

clf = DecisionTreeClassifier(criterion="entropy", max_depth=20, min_samples_leaf=1, min_samples_split=2)
clf = clf.fit(x_train, y_train)

y_pred = clf.predict(x_test)

print("Accuracy on training set: {:.3f}".format(clf.score(x_train, y_train)))
print("Accuracy on test set: {:.3f}".format(clf.score(x_test, y_test)))


data = pandas.read_csv("dataset.csv", sep=';')

print(data.head())

x = data["Matrix"].apply(ast.literal_eval)

x = x.apply(lambda row: [list(map(int, sublist)) for sublist in row])

flattened_matrices = [np.array(matrix).flatten() for matrix in x]

X = np.array(flattened_matrices)

y = data['Res']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

dt = DecisionTreeClassifier(random_state=42)

parameters = {
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

scorer = make_scorer(accuracy_score)

grid_obj = GridSearchCV(dt, parameters, scoring=scorer)

grid_fit = grid_obj.fit(X_train, y_train)

best_dt = grid_fit.best_estimator_

predictions = best_dt.predict(X_test)

acc = accuracy_score(y_test, predictions)

print(f'Лучшие параметры: {grid_fit.best_params_}')
print(f'Точность лучшей модели: {acc}')



