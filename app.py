from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import json
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    salary = Column(Float, nullable=False)

engine = create_engine('sqlite:///employees.db')
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        emp_id = request.form.get('id')
        name = request.form.get('name')
        position = request.form.get('position')
        try:
            salary = float(request.form.get('salary'))
        except ValueError:
            flash('Invalid salary.')
            return redirect(url_for('add_employee'))

        session = Session()
        if session.query(Employee).filter_by(id=emp_id).first():
            flash('Employee already exists.')
            Session.remove()
            return redirect(url_for('add_employee'))

        new_employee = Employee(id=emp_id, name=name, position=position, salary=salary)
        session.add(new_employee)
        session.commit()
        flash('Employee Added Successfully')
        Session.remove()
        return redirect(url_for('index'))

    return render_template('add_employee.html')

@app.route('/remove_employee', methods=['GET', 'POST'])
def remove_employee():
    if request.method == 'POST':
        emp_id = request.form.get('id')
        session = Session()
        employee = session.query(Employee).filter_by(id=emp_id).first()
        if not employee:
            flash('Employee does not exist.')
            Session.remove()
            return redirect(url_for('remove_employee'))

        session.delete(employee)
        session.commit()
        flash('Employee Removed Successfully')
        Session.remove()
        return redirect(url_for('index'))

    return render_template('remove_employee.html')

@app.route('/promote_employee', methods=['GET', 'POST'])
def promote_employee():
    if request.method == 'POST':
        emp_id = request.form.get('id')
        try:
            amount = float(request.form.get('amount'))
        except ValueError:
            flash('Invalid amount.')
            return redirect(url_for('promote_employee'))

        session = Session()
        employee = session.query(Employee).filter_by(id=emp_id).first()
        if not employee:
            flash('Employee does not exist.')
            Session.remove()
            return redirect(url_for('promote_employee'))

        employee.salary += amount
        session.commit()
        flash('Employee Promoted Successfully')
        Session.remove()
        return redirect(url_for('index'))

    return render_template('promote_employee.html')

@app.route('/display_employees')
def display_employees():
    session = Session()
    employees = session.query(Employee).all()
    Session.remove()
    return render_template('display_employees.html', employees=employees)

@app.route('/find_employee', methods=['GET', 'POST'])
def find_employee():
    if request.method == 'POST':
        emp_id = request.form.get('id')
        if not emp_id:
            flash('Employee ID is required.')
            return redirect(url_for('find_employee'))

        session = Session()
        employee = session.query(Employee).filter_by(id=emp_id).first()
        Session.remove()
        if not employee:
            flash('Employee does not exist.')
            return redirect(url_for('find_employee'))

        return render_template('find_employee.html', employee=employee)

    return render_template('find_employee.html')

@app.route('/edit_employee/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    session = Session()
    employee = session.query(Employee).filter_by(id=emp_id).first()

    if request.method == 'POST':
        if not employee:
            flash('Employee does not exist.')
            Session.remove()
            return redirect(url_for('find_employee'))

        name = request.form.get('name')
        position = request.form.get('position')
        try:
            salary = float(request.form.get('salary'))
        except ValueError:
            flash('Invalid salary.')
            return render_template('edit_employee.html', employee=employee)

        employee.name = name
        employee.position = position
        employee.salary = salary
        session.commit()
        flash('Employee Updated Successfully')
        Session.remove()
        return redirect(url_for('display_employees'))

    return render_template('edit_employee.html', employee=employee)

@app.route('/filter_employees', methods=['GET', 'POST'])
def filter_employees():
    employees = []
    employees_json = None
    if request.method == 'POST':
        position = request.form.get('position')
        order_by = request.form.get('order_by')
        salary_gt = request.form.get('salary_gt')
        salary_lt = request.form.get('salary_lt')

        session = Session()
        query = session.query(Employee)

        if position:
            query = query.filter(Employee.position == position)

        if salary_gt:
            try:
                salary_gt = float(salary_gt)
                query = query.filter(Employee.salary > salary_gt)
            except ValueError:
                flash('Invalid salary for greater than filter.')
        
        if salary_lt:
            try:
                salary_lt = float(salary_lt)
                query = query.filter(Employee.salary < salary_lt)
            except ValueError:
                flash('Invalid salary for less than filter.')

        if order_by:
            if order_by == 'asc':
                query = query.order_by(Employee.salary.asc())
            elif order_by == 'desc':
                query = query.order_by(Employee.salary.desc())

        employees = query.all()
        Session.remove()

        # Store filtered data in JSON format
        employees_json = json.dumps([{
            'id': emp.id,
            'name': emp.name,
            'position': emp.position,
            'salary': emp.salary
        } for emp in employees])

    return render_template('filter_employees.html', employees=employees, employees_json=employees_json)

@app.route('/export_filtered_employees', methods=['POST'])
def export_filtered_employees():
    employees_json = request.form.get('employees')
    if not employees_json:
        flash('No data to export.')
        return redirect(url_for('filter_employees'))

    employees = json.loads(employees_json)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Position', 'Salary'])
    for emp in employees:
        writer.writerow([emp['id'], emp['name'], emp['position'], emp['salary']])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=filtered_employees.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

if __name__ == "__main__":
    app.run(debug=True)
