from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime, date
import numpy as np
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    employee = db.relationship('Employee', backref='user', uselist=False)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    department = db.relationship('Department', backref='employees', lazy=True)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    employees = db.relationship('Employee', backref='team', lazy=True, foreign_keys='Employee.team_id')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    team_lead_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    team_lead = db.relationship('Employee', foreign_keys=[team_lead_id], uselist=False, backref='led_team')


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    team = db.relationship('Team', backref=db.backref('projects', lazy=True))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee = db.relationship('Employee', backref='tasks')
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='created_tasks')
    project = db.relationship('Project', backref='tasks')
    priority = db.Column(db.String(10), nullable=False)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    level = db.Column(db.Integer, nullable=False)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teams = db.relationship('Team', backref='department', lazy=True)


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in roles:
                flash("You do not have access to this page.")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user if user else None


@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role and current_user.employee:
            return redirect(url_for('index'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role_name = request.form.get('role')
        department_name = request.form.get('department')  # Теперь это имя департамента

        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('register'))

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Invalid role selected', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Choose another one.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            role_id=role.id,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(new_user)
        db.session.flush()

        department = None
        if department_name:
            department = Department.query.filter_by(name=department_name).first()
            if not department:
                flash(f"Department '{department_name}' does not exist", 'error')
                return redirect(url_for('register'))

        new_employee = Employee(
            name=username,
            user_id=new_user.id,
            department_id=department.id if department else None,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(new_employee)

        try:
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    assignable_employees = get_assignable_employees(current_user)
    managers = User.query.join(Role).filter(Role.name == 'Manager').all()
    departments = Department.query.all()
    potential_members = Employee.query.join(User).join(Role).filter(Role.name == 'Employee',
                                                                    Employee.team_id == None).all()
    department = current_user.employee.department if (current_user.role.name == 'Manager'
                                                      and current_user.employee) else None
    potential_leads = Employee.query.join(User).join(Role).filter(Role.name == 'TeamLead',
                                                                  Employee.team_id == None).all()

    team_id = current_user.employee.team_id
    team_members = Employee.query.filter(Employee.team_id == team_id, Employee.user_id != current_user.id).all()


    if current_user.role.name == 'Manager':
        teams = Team.query.filter_by(department_id=current_user.employee.department_id).all()
    else:
        teams = Team.query.all()

    if current_user.role.name == 'Executive':
        projects = Project.query.all()
    elif current_user.role.name == 'Manager':
        if current_user.employee and current_user.employee.department_id:
            projects = Project.query.join(Team).filter(Team.department_id == current_user.employee.department_id).all()
        else:
            projects = []
    elif current_user.role.name == 'TeamLead' or current_user.role.name == 'Employee':
        if current_user.employee and current_user.employee.team_id:
            team_id = current_user.employee.team_id
            projects = Project.query.filter_by(team_id=team_id).all()
        else:
            projects = []
    else:
        projects = []

    current_project = projects[0] if projects else None

    if current_project:
        return redirect(url_for('project_tasks', project_id=current_project.id))

    if current_user.role and current_user.employee:
        for department in departments:
            department.show_add_team_button = (
                    current_user.employee.department_id == department.id and current_user.role.name == 'Manager')
    else:
        for department in departments:
            department.show_add_team_button = False

    for department in departments:
        department.show_add_team_button = (current_user.employee and
                                           current_user.employee.department_id == department.id and
                                           current_user.role.name == 'Manager')
        department.teams = Team.query.filter_by(department_id=department.id).all()
        for team in department.teams:
            team.members = Employee.query.filter_by(team_id=team.id).all()


    role = None
    if current_user.is_authenticated:
        role = current_user.role.name

    return render_template('index.html', employees=assignable_employees, managers=managers,
                           departments=departments, potential_members=potential_members, role=role,
                           department=department,potential_leads=potential_leads, projects=projects,
                           teams=teams, current_project=current_project,team_members=team_members)


@app.route('/project/<int:project_id>', methods=['GET'])
@login_required
def project_tasks(project_id):
    project = Project.query.get_or_404(project_id)
    now = datetime.now()
    query = request.args.get('query', '')
    priority_filter = request.args.get('priority', '')
    assignee_filter = request.args.get('assignee', '')

    assignable_employees = get_assignable_employees(current_user, project)
    managers = User.query.join(Role).filter(Role.name == 'Manager').all()
    departments = Department.query.all()
    potential_members = Employee.query.join(User).join(Role).filter(Role.name == 'Employee',
                                                                    Employee.team_id == None).all()
    department = current_user.employee.department if current_user.role.name == 'Manager' and current_user.employee else None
    potential_leads = Employee.query.join(User).join(Role).filter(Role.name == 'TeamLead',
                                                                  Employee.team_id == None).all()

    team_id = current_user.employee.team_id
    team_members = Employee.query.filter(Employee.team_id == team_id, Employee.user_id != current_user.id).all()

    unassigned_tasks = Task.query.filter_by(employee_id=None).all()

    if current_user.role.name == 'Manager':
        teams = Team.query.filter_by(department_id=current_user.employee.department_id).all()
    else:
        teams = Team.query.all()

    if current_user.role.name == 'Executive':
        projects = Project.query.all()
    elif current_user.role.name == 'Manager':
        if current_user.employee and current_user.employee.department_id:
            projects = Project.query.join(Team).filter(Team.department_id == current_user.employee.department_id).all()
        else:
            projects = []
    elif current_user.role.name == 'TeamLead' or current_user.role.name == 'Employee':
        if current_user.employee and current_user.employee.team_id:
            team_id = current_user.employee.team_id
            projects = Project.query.filter_by(team_id=team_id).all()
        else:
            projects = []
    else:
        projects = []

    if current_user.role and current_user.employee:
        for department in departments:
            department.show_add_team_button = (
                    current_user.employee.department_id == department.id and current_user.role.name == 'Manager')
    else:
        for department in departments:
            department.show_add_team_button = False


    tasks = {
        'to_do': Task.query.filter(Task.status == 'to_do', Task.project_id == project.id,
                                   Task.name.like(f'%{query}%') if query else True,
                                   Task.priority == priority_filter if priority_filter else True,
                                   Task.employee_id == int(assignee_filter) if assignee_filter else True).all(),
        'doing': Task.query.filter(Task.status == 'doing', Task.project_id == project.id,
                                   Task.name.like(f'%{query}%') if query else True,
                                   Task.priority == priority_filter if priority_filter else True,
                                   Task.employee_id == int(assignee_filter) if assignee_filter else True).all(),
        'done': Task.query.filter(Task.status == 'done', Task.project_id == project.id,
                                  Task.name.like(f'%{query}%') if query else True,
                                  Task.priority == priority_filter if priority_filter else True,
                                  Task.employee_id == int(assignee_filter) if assignee_filter else True).all()
    }

    for task_list in tasks.values():
        for task in task_list:
            if isinstance(task.deadline, date):
                task.deadline = datetime.combine(task.deadline, datetime.min.time())
            if isinstance(task.created_at, date):
                task.created_at = datetime.combine(task.created_at, datetime.min.time())

    for status, tasks_in_status in tasks.items():
        for task in tasks_in_status:
            if task.deadline:
                total_duration = task.deadline - task.created_at
                elapsed_time = now - task.created_at
                elapsed_percentage = (elapsed_time.total_seconds() / total_duration.total_seconds()) * 100
                if elapsed_percentage < 50:
                    task.deadline_class = 'text-success'
                elif elapsed_percentage < 75:
                    task.deadline_class = 'text-warning'
                else:
                    task.deadline_class = 'text-danger'
            else:
                task.deadline_class = 'text-secondary'

    role = None
    if current_user.is_authenticated:
        role = current_user.role.name

    return render_template('index.html', tasks=tasks, current_project=project,
                           employees=assignable_employees, projects=projects,departments=departments,
                           managers=managers, potential_members=potential_members, role=role,
                           department=department, potential_leads=potential_leads, teams=teams,
                           search_query=query, team_members=team_members, unassigned_tasks=unassigned_tasks,
                           priority_filter=priority_filter, assignee_filter=assignee_filter)


@app.route('/create-project', methods=['POST'])
@login_required
@role_required('Manager')
def create_project():
    project_name = request.form.get('projectName')
    project_description = request.form.get('projectDescription')
    project_team_id = request.form.get('projectTeam')

    if project_team_id:
        team = Team.query.get(project_team_id)
        if team and team.department_id == current_user.employee.department_id:
            new_project = Project(
                name=project_name,
                description=project_description,
                team_id=project_team_id
            )
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
        else:
            flash('You can only assign teams from your own department.', 'danger')
    else:
        flash('Please select a valid team.', 'danger')

    return redirect(url_for('index'))


@app.route('/create-department', methods=['POST'])
@login_required
def create_department():
    department_name = request.form.get('departmentName')
    manager_id = request.form.get('manager')
    if not department_name or not manager_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('index'))

    department = Department.query.filter_by(name=department_name).first()
    if not department:
        department = Department(name=department_name)
        db.session.add(department)
    department.manager_id = manager_id
    db.session.commit()

    manager = Employee.query.filter_by(user_id=manager_id).first()
    if manager:
        manager.department_id = department.id
        db.session.commit()
    else:
        flash('No employee found for given manager ID', 'error')

    flash('Department successfully created/updated!', 'success')
    return redirect(url_for('index'))


@app.route('/create-team', methods=['POST'])
@login_required
def create_team():
    team_name = request.form['teamName']
    team_lead_id = request.form['teamLead']
    member_ids = request.form.getlist('teamMembers[]')
    department_id = request.form['department']

    new_team = Team(name=team_name, department_id=department_id)
    db.session.add(new_team)
    db.session.commit()

    lead = Employee.query.get(team_lead_id)
    lead.team_id = new_team.id
    db.session.commit()

    for member_id in member_ids:
        member = Employee.query.get(member_id)
        member.team_id = new_team.id
        db.session.commit()
    try:
        db.session.commit()
        flash('Team created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('index'))


@app.route('/delete-team/<int:team_id>', methods=['DELETE'])
@login_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)

    if current_user.role.name != 'Manager':
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    # Удаляем принадлежность работников к команде
    employees = Employee.query.filter_by(team_id=team_id).all()
    for employee in employees:
        employee.team_id = None

    # Удаляем проекты и связанные с ними задачи
    projects = Project.query.filter_by(team_id=team_id).all()
    for project in projects:
        tasks = Task.query.filter_by(project_id=project.id).all()
        for task in tasks:
            db.session.delete(task)
        db.session.delete(project)

    db.session.commit()

    # Удаляем саму команду
    db.session.delete(team)
    db.session.commit()

    return jsonify({'success': True, 'redirect_url': url_for('index')})


@app.route('/update-task/<int:task_id>/<string:new_status>', methods=['POST'])
def update_task(task_id, new_status):
    task = Task.query.get(task_id)
    if task:
        task.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404


@app.route('/add-task/<int:project_id>', methods=['POST'])
@login_required
def add_task(project_id):
    if request.method == 'POST':

        name = request.form['taskName']
        description = request.form['description']
        employee_id = request.form['assignee']
        unassigned = 'unassigned' in request.form
        deadline_str = request.form.get('deadline')
        priority = request.form['priority']
        assignee = User.query.get(employee_id)
        assigner = current_user
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

        if unassigned:
            employee_id = None
        else:
            employee_id = int(employee_id) if employee_id else None

        if employee_id:
            if assignee.role.level <= assigner.role.level:
                new_task = Task(
                    name=name,
                    description=description,
                    project_id=project_id,
                    employee_id=employee_id,
                    status='to_do',
                    deadline=deadline,
                    creator_id=current_user.id,
                    priority=priority
                )
                db.session.add(new_task)
                db.session.commit()
                flash('Task added successfully!', 'success')
            else:
                flash('You do not have permission to assign tasks to this user.', 'error')
        else:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
            new_task = Task(
                name=name,
                description=description,
                project_id=project_id,
                employee_id=employee_id,
                status='to_do',
                deadline=deadline,
                creator_id=current_user.id,
                priority=priority
            )
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully without assignee!', 'success')

        return redirect(url_for('project_tasks', project_id=project_id))

    return redirect(url_for('project_tasks', project_id=project_id))


def get_assignable_employees(user, project=None):
    if user.employee is None:
        return []

    if user.role.name == 'Executive':
        department_id = user.employee.department_id
        if project:
            department = Department.query.join(Team).filter(Team.id == project.team_id).first()
            if department:
                managers = (Employee.query.join(User, Employee.user_id == User.id)
                            .join(Role, User.role_id == Role.id)
                            .filter(Role.name == 'Manager', Employee.department_id == department.id).all())
            else:
                managers = []
            team_employees = (Employee.query.filter(Employee.team_id == project.team_id).all())
            return managers + team_employees
        else:
            managers = (Employee.query.join(User, Employee.user_id == User.id)
                        .join(Role, User.role_id == Role.id)
                        .filter(Role.name == 'Manager', Employee.department_id == department_id).all())
            return managers
    elif user.role.name == 'Manager':
        department_id = user.employee.department_id
        return Employee.query.join(Team, Employee.team_id == Team.id).filter(Team.department_id == department_id).all()
    elif user.role.name == 'TeamLead':
        team_id = user.employee.team_id
        return Employee.query.filter(Employee.team_id == team_id).all()
    else:
        return []


def can_assign_task(assigner, assignee_id):
    assignee = Employee.query.get(assignee_id)
    if assigner.role.name == 'Executive':
        return True
    elif assigner.role.name == 'Manager':
        return assignee.team.department_id == assigner.employee.department_id
    elif assigner.role.name == 'TeamLead':
        return assignee.team_id == assigner.employee.team_id
    return False


@app.route('/delete-task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    tasks = Task.query.filter(Task.name.like(f'%{query}%')).all()
    task_dict = {'to_do': [], 'doing': [], 'done': []}
    for task in tasks:
        task_dict[task.status].append(task)
    return render_template('index.html', tasks=task_dict, search_query=query)


class TaskAssignment:
    def __init__(self, n):
        self.n = n
        self.matrix_ef = np.zeros((n, n), dtype=int)
        self.xy_arr = np.full(n, -1)
        self.yx_arr = np.full(n, -1)
        self.vx_arr = np.zeros(n, dtype=int)
        self.vy_arr = np.zeros(n, dtype=int)
        self.max_row = np.zeros(n, dtype=int)
        self.min_col = np.zeros(n, dtype=int)

    def input_performance_levels(self, performance_levels):
        for i in range(self.n):
            for j in range(self.n):
                self.matrix_ef[i][j] = performance_levels[i][j]

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

    def get_assignments(self):
        return self.xy_arr


@app.route('/assign_tasks', methods=['POST'])
@login_required
def assign_tasks():
    data = request.get_json()
    employee_ids = data['employees']
    task_ids = data['tasks']
    performance_levels = data['performance_levels']

    if len(employee_ids) != len(task_ids):
        return jsonify(success=False, error="Количество сотрудников и задач должно совпадать.")
    n = len(employee_ids)
    levels_matrix = np.zeros((n, n), dtype=int)
    for perf in performance_levels:
        employee_index = employee_ids.index(perf['employee_id'])
        for level in perf['levels']:
            task_index = task_ids.index(level['task_id'])
            levels_matrix[employee_index][task_index] = level['level']

    task_assignment = TaskAssignment(n)
    task_assignment.input_performance_levels(levels_matrix)
    task_assignment.assign_tasks()

    assignments = task_assignment.get_assignments()
    for i, employee_id in enumerate(employee_ids):
        task_id = task_ids[assignments[i]]
        task = Task.query.get(task_id)
        task.employee_id = employee_id

    db.session.commit()
    return jsonify(success=True)


@app.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify({
            'name': task.name,
            'description': task.description,
            'creator': f"{task.creator.first_name} {task.creator.last_name[0]}.",
            'assignee_name': f"{task.employee.first_name} {task.employee.last_name[0]}." if task.employee else "Unassigned",
            'assignee': task.employee_id,
            'deadline': task.deadline.strftime('%d.%m.%Y') if task.deadline else None,
            'priority': task.priority,
            'can_edit': current_user.id == task.creator_id
        })
    return jsonify({'error': 'Task not found'}), 404


@app.route('/edit-task/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    task = Task.query.get(task_id)
    if task.creator_id != current_user.id:
        return jsonify({'error': 'You are not allowed to edit this task'}), 403

    if task:
        data = request.json
        name = data['taskName']
        description = data['description']
        priority = data['priority']
        deadline_str = data['deadline']
        employee_id = data['assignee']
        unassigned = 'unassigned' in request.form

        if unassigned:
            employee_id = None
        else:
            employee_id = int(employee_id) if employee_id else None

        task.name = name
        task.description = description
        task.priority = priority
        task.employee_id = employee_id
        task.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error updating task: {e}'})
    return jsonify({'error': 'Task not found'}), 404


@app.route('/team/<int:team_id>', methods=['GET'])
@login_required
def get_team(team_id):
    team = Team.query.get_or_404(team_id)
    available_employees = db.session.query(Employee).join(User).join(Role).filter(
        Role.name == 'Employee',
        or_(Employee.team == None, Employee.team_id == team_id)
    ).all()

    team_data = {
        'name': team.name,
        'members': [{'id': member.id, 'name': f"{member.user.first_name} {member.user.last_name}"} for member in
                    team.employees],
        'available_employees': [{'id': emp.id, 'name': f"{emp.user.first_name} {emp.user.last_name}"} for emp in
                                available_employees]
    }
    return jsonify(team_data)


@app.route('/team/<int:team_id>', methods=['PUT'])
@login_required
def update_team(team_id):
    team = Team.query.get_or_404(team_id)
    data = request.json

    # Обновление имени команды
    team.name = data.get('name', team.name)

    # Обновление состава команды
    member_ids = set(map(int, data.get('members', [])))  # Преобразуем в set с целыми числами
    current_member_ids = set(emp.id for emp in team.employees)

    # Определяем сотрудников, которые будут удалены из команды
    removed_member_ids = current_member_ids - member_ids
    new_member_ids = member_ids - current_member_ids


    # Удаляем сотрудников, которые больше не в команде
    for member_id in removed_member_ids:
        employee = Employee.query.get(member_id)
        if employee:
            # Убираем задачи сотрудника
            for task in employee.tasks:
                task.employee_id = None
            employee.team = None

    # Добавляем новых сотрудников в команду
    for member_id in new_member_ids:
        employee = Employee.query.get(member_id)
        if employee:
            employee.team = team

    db.session.commit()
    return jsonify({'success': True})


@app.route('/delete-project/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Удаляем все задачи, связанные с проектом
    for task in project.tasks:
        db.session.delete(task)

    # Удаляем проект
    db.session.delete(project)
    db.session.commit()

    return jsonify({'success': True, 'redirect_url': url_for('index')})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
