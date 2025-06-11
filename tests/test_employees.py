
def test_employee_crud(utils_module):
    utils, fake = utils_module
    assert utils.add_employee('John Doe', 'Red', 'john@example.com', 'proj')
    emp = fake.tables['employees'][0]
    emp_id = emp['id']
    assert utils.get_employee_by_name('John Doe', 'proj')['email'] == 'john@example.com'
    assert utils.get_employee_by_email('john@example.com', 'proj')['full_name'] == 'John Doe'
    assert utils.update_employee(emp_id, 'John Doe', 'Blue', 'john@example.com', 'proj')
    assert fake.tables['employees'][0]['raic_color'] == 'Blue'
    assert utils.deactivate_employee(emp_id, 'proj')
    assert fake.tables['employees'][0]['is_active'] is False
    assert utils.reactivate_employee(emp_id, 'proj')
    assert fake.tables['employees'][0]['is_active'] is True
    employees = utils.get_all_employees('proj')
    assert len(employees) == 1 and employees[0]['full_name'] == 'John Doe'
