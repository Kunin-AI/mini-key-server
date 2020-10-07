# coding: utf-8

import json
from random import randint, choice
from flask import url_for
from flask_sqlalchemy import BaseQuery
from kunin.exceptions import (RESOURCE_NOT_FOUND, PERMISSIONS_NOT_GRANTED, INCOMPLETE_REQUEST, BAD_POST_DATA,
                              WRONG_ROUTE_FOR_USE, DATA_MISMATCH_IN_REQUEST)
from tests.factories import DepartmentFactory, ClientFactory, UserFactory, UserProfileFactory, WorkCategorizationFactory
from tests import fake
from faker.providers import python
from kunin.taxonomy.workcategorization.serializers import activity_schema, activities_schema, \
    employees_activity_target_schema, activity_notes_schema, Work, WorkCategorization as Activity
from kunin.taxonomy.workcategorization.models import Allocation, Note
from kunin.taxonomy.department.serializers import employees_with_dept_div_schema

fake.add_provider(python)

########################################################################################################################
USER_LOGIN_ROUTE = 'user.login_user'
ERRORS_FOR_ACTIVITIES = {
    'not_logged_in': (401, 'Missing Authorization Header'),
    'logged_in_different_client': lambda resource: (404, RESOURCE_NOT_FOUND(resource)['message']),
    'non_existing_resource': lambda resource: (404, RESOURCE_NOT_FOUND(resource)['message']),
    'get_resource_for_bosses': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_resource_for_non_reports': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_resource_for_div_or_dept_not_mine': (401, PERMISSIONS_NOT_GRANTED['message']),
    'post_resource_for_div_or_dept_not_mine': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_resource_for_div_or_dept_not_managed_by_me': (401, PERMISSIONS_NOT_GRANTED['message']),
    'post_resource_for_div_or_dept_not_managed_by_me': (401, PERMISSIONS_NOT_GRANTED['message']),
    'post_resource_for_div_or_dept_with_bad_post_data': lambda resource: (400, INCOMPLETE_REQUEST(resource)['message']),
    'post_resource_for_div_or_dept_insufficient_access': (401, PERMISSIONS_NOT_GRANTED['message']),
    'post_resource_for_div_or_dept_bad_post_data': lambda resource: (400, BAD_POST_DATA(resource)['message']),
    'delete_resource_for_div_or_dept_not_mine': (401, PERMISSIONS_NOT_GRANTED['message']),
    'delete_resource_for_div_or_dept_not_managed_by_me': (401, PERMISSIONS_NOT_GRANTED['message']),
    'assign_work_for_div_or_dept_not_mine': (401, PERMISSIONS_NOT_GRANTED['message']),
    'assign_work_for_div_or_dept_not_managed_by_me': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_many_from_specific_department_format_aggregate_by_employee': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_many_for_all_departments_format_aggregate_by_employee': (401, PERMISSIONS_NOT_GRANTED['message']),
    'delete_resource_for_div_or_dept_insufficient_access': (401, PERMISSIONS_NOT_GRANTED['message']),
    'delete_employee_resource_in_div_or_dept': lambda cannot: (401, WRONG_ROUTE_FOR_USE(cannot)['message']),
    'delete_resource_for_dept_not_owned_by_div': lambda mismatch: (401, DATA_MISMATCH_IN_REQUEST(mismatch)['message']),
    'assign_work_for_div_or_dept_insufficient_access': (401, PERMISSIONS_NOT_GRANTED['message']),
    'assign_employee_work_in_div_or_dept': lambda cannot: (401, WRONG_ROUTE_FOR_USE(cannot)['message']),
    'assign_work_for_dept_not_owned_by_div': lambda mismatch: (401, DATA_MISMATCH_IN_REQUEST(mismatch)['message']),
    'assign_work_with_bad_post_data': lambda resource: (400, BAD_POST_DATA(resource)['message']),
    'get_allocations_for_div_or_dept_not_mine': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_allocations_for_div_or_dept_not_managed_by_me': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_allocations_for_div_or_dept_insufficient_access': (401, PERMISSIONS_NOT_GRANTED['message']),
    'get_allocations_for_dept_not_owned_by_div': lambda mismatch: (401, DATA_MISMATCH_IN_REQUEST(mismatch)['message']),
    'post_resource_for_div_or_dept_with_bad_regex': lambda resource: (400, BAD_POST_DATA(resource)['message']),
    'too_many_replies': lambda resource: (400, BAD_POST_DATA(resource)['message']),
    'post_notes_bad_post_data': lambda resource: (400, INCOMPLETE_REQUEST(resource)['message']),
}
LAMBDA_ERRORS = ('logged_in_different_client', 'non_existing_resource',
                 'post_resource_for_div_or_dept_with_bad_post_data', 'post_resource_for_div_or_dept_bad_post_data',
                 'delete_employee_resource_in_div_or_dept', 'delete_resource_for_dept_not_owned_by_div',
                 'assign_work_for_dept_not_owned_by_div', 'assign_employee_work_in_div_or_dept',
                 'assign_work_with_bad_post_data', 'get_allocations_for_dept_not_owned_by_div',
                 'post_resource_for_div_or_dept_with_bad_regex', 'too_many_replies', 'post_notes_bad_post_data')
RETURN_FOR_SINGLE_OR_MANY = {
    'get_single': (200, activity_schema.dump),
    'get_many': (200, activities_schema.dump),
    'post_create': (201, activity_schema.dump),
    'delete_activity': (200, activities_schema.dump),
    'get_many_from_specific_department_format_aggregate': (200, activities_schema.dump),
    'get_many_from_all_departments_format_aggregate': (200, activities_schema.dump),
    'get_user_activity_format_aggregate': (200, activity_schema.dump),
    'get_user_activities_format_aggregate': (200, activities_schema.dump),
    'get_single_from_specific_department_format_hourly_or_daily': (200, activity_schema.dump),
    'get_many_or_all_from_specific_department_format_hourly_or_daily': (200, activities_schema.dump),
    'get_user_activities_format_hourly_or_daily': (200, activities_schema.dump),
    'get_many_from_specific_activity_format_employee_targets_ids': (200, employees_activity_target_schema.dump),
    'get_single_format_aggregate_and_hourly_by_employee': (200, employees_activity_target_schema.dump),
    'get_departments_by_employee': (200, employees_with_dept_div_schema.dump),
    'get_department_employees_by_focus_ie_the_leaderboard': (200, employees_with_dept_div_schema.dump),
    'assign_single_no_previous': (200, activities_schema.dump),
    'get_allocations_from_all_activities': (200, activities_schema.dump),
    'get_focus_from_all_activities': (200, activities_schema.dump),
    'get_focus_from_all_departments': (200, activities_schema.dump),
    'post_create_allocation': (201, activity_schema.dump),
    'patch_update_activity': (201, activity_schema.dump),
    'put_focus': (200, activity_schema.dump),
    'post_note': (201, activity_schema.dump),
}
########################################################################################################################
# MINIMAL / BASE
MINIMAL_ACTIVITY_ATTRS = lambda r, extras, more=None: {
    'activity_id': r.uuid,
    'activity_name': r.activity_name,
    **extras
}
# ACTIVITY KEYS AND ATTRS
EMPLOYEE_TARGETS_ATTRS = lambda ee, extras, more=None: {
    'username': ee.username,
    'user_id': ee.user.uuid,
    'first_name': ee.user.first_name,
    'last_name': ee.user.last_name,
    # Everything Below will be calculated as part of MeasuredEvents & Measurers from YODA
    'general_target': {
        'assigned_time': 60,
        'assigned_percentage': 12.5
    },
    'unique_target': {
        'assigned_time': 120,
        'assigned_percentage': 25
    },
    **extras
}
EMPLOYEE_ACTIVITY_TARGET_ATTRS = lambda act, extras, ee=None: {
    'username': act.owner.user.username if act.type == 'Employee' else ee.user.username,
    'user_id': act.owner.user.uuid if act.type == 'Employee' else ee.user.uuid,
    'first_name': act.owner.user.first_name if act.type == 'Employee' else ee.user.first_name,
    'last_name': act.owner.user.last_name if act.type == 'Employee' else ee.user.last_name,
    # Everything Below will be calculated as part of MeasuredEvents & Measurers from YODA
    'general_target': {
        'assigned_time': act.assigned_time,
        'assigned_percentage': act.assigned_percent
    },
    'unique_target': {
        'assigned_time': act.assigned_time if act.type == 'Employee' else
        Work.query.filter(Work.workcategorization_id == act.id, Work.employee_id == ee.id).one().assigned_time,
        'assigned_percentage': act.assigned_percent if act.type == 'Employee' else
        Work.query.filter(Work.workcategorization_id == act.id, Work.employee_id == ee.id).one().assigned_percent
    },
    **extras
}
# USER ACTIVITIES
USER_PER_ACTIVITY_ATTRS = lambda r, extras, more=None: {
    'activity_id': r.uuid,
    'activity_name': r.activity_name,
    'assigned_percent': r.assigned_percent,
    'assigned_time': r.assigned_time,
    # Everything Below will be calculated as part of MeasuredEvents & Measurers from YODA
    'achieved_percentage': 43,
    'achieved_time': 120,
    'flow': [9, '10:05'],
    'total_focus': 120,
    'trends': [],
    **extras
}
# DEPARTMENT ACTIVITIES
DEPT_PER_ITEM_ATTRS = lambda r, extras, more=None: {  # use for EMPLOYEE_TARGET_IDS with extras == {'employees': payload}
    'activity_name': r.activity_name,
    'activity_id': r.uuid,
    'assigned_time': r.assigned_time,
    'assigned_percent': r.assigned_percent,
    'my_focus': r.my_focus,
    'all_employees': r.all_employees,
    **extras
}
DEPT_ALLOCATION_ATTRS = lambda a, extras, more=None: {
    'allocation_id': a.uuid,
    'allocation_name': a.name,
    'allocation_regex': a.rule,
    **extras
}
DEPT_ACTIVTIES_ALLOCATIONS_ATTRS = lambda a, extras, more=None: {
    'activity_name': a.activity_name,
    'activity_id': a.uuid,
    'allocations': [{'allocation_id': al.uuid, 'allocation_name': al.name, 'allocation_regex': al.rule} for al in
                    a.allocations],
    **extras
}
MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS = lambda r, extras, more=None: {
    "activity_name": r.activity_name,
    "activity_id": r.uuid,
    **extras
}
ACTIVITY_NOTE_ATTRS = lambda n, extras, more=None: {
    "date": n.updated_at if n.updated_at else n.created_at,
    "note": n.note,
    "submitter": {"first_name": n.author.user.first_name,
                  "last_name": n.author.user.last_name,
                  "user_id": n.author.user.uuid},
    **extras
}
ACTIVITIES_ALL_WITH_NOTES_ATTRS = lambda act, extras, more=None: {
    'notes': [{**ACTIVITY_NOTE_ATTRS(note, {})} for note in act.notes],
    **MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS(act, {}),
    **extras
}
DEPT_AGGREGATE_PER_ACTIVITY_ATTRS = lambda r, extras, more=None: {
    **MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS(r, {}),
    "assigned_time": r.assigned_time,
    "assigned_percent": r.assigned_percent,
    **extras  # i.e. 'periods': {<hour>: {'focus': [], 'working': []}}
}
EMPLOYEE_DIV_DEPT_ATTRS = lambda e, extras, more=None: {
    "user_id": e.user.uuid,
    "first_name": e.user.first_name,
    "last_name": e.user.last_name,
    **extras(e)  # i.e. 'divisions' and 'departments'
}

# Possible keys
CALCULATED_ACTIVITY_KEYS = ['achieved_time', 'achieved_percentage', 'trends', 'flow', 'total_focus',
                            'average_employee_hours', 'total_employees', 'periods']

ACTIVITY_LEVEL_1_KEYS = lambda pkey: ('activity_name', 'activity_id', 'assigned_time', 'assigned_percentage',
                                      'my_focus', 'all_employees', pkey)
USER_LEVEL_1_KEYS = lambda pkey: ('department_id', 'department_name', 'first_name', 'last_name', 'user_id', pkey)
USER_AGGREGATE_LEVEL_KEYS = USER_LEVEL_1_KEYS
DEPT_LEVEL_1_BASE_KEYS = lambda pkey=None: ('department_id', 'department_name', 'manager', 'division_name',
                                            'division_id') + ((pkey,) if pkey else ())
DIV_LEVEL_1_BASE_KEYS = lambda pkey=None: ('manager', 'division_name', 'division_id') + ((pkey,) if pkey else ())
DEPT_LEVEL_1_KEYS = lambda pkey: DEPT_LEVEL_1_BASE_KEYS + (pkey, )
DIV_LEVEL_1_KEYS = lambda pkey: DIV_LEVEL_1_BASE_KEYS() + (pkey, )
DEPT_ACTIVITY_LEVEL_1_KEYS = lambda pkey: DEPT_LEVEL_1_BASE_KEYS + ('activity_name', 'activity_id', pkey)

AGGREGATE_BASE_KEYS = ('division_name', 'division_id', 'my_focus')
PER_DEPT_KEYS = lambda extra: ('department_name', 'department_id', 'manager') + extra
DEPT_AGGREGATE_LEVEL_1_KEYS = lambda pkey: AGGREGATE_BASE_KEYS + PER_DEPT_KEYS(()) + (pkey,)
ALL_DEPT_AGGREGATE_LEVEL_1_KEYS = lambda pkey: ('departments',) + AGGREGATE_BASE_KEYS + (pkey,)
AGGREGATE_ACTIVITY_LEVEL1_KEYS = lambda pkey: ('division_name', 'division_id') + ((pkey,) if pkey else ())
EE_DIV_DEPT_REQUIRED_KEYS = lambda pkey: [] + [pkey]

########################################################################################################################
# HELPER METHODS
########################################################################################################################
#
def _register_user(testapp, **kwargs):
    return testapp.post_json(url_for('user.register_user'), {
          "user": {
              "email": 'foo@bar.com',
              "username": 'foobar',
              "password": 'myprecious',
              "bio": fake.sentence(),
              "first_name": "Mo",
              "last_name": "Om",
              "image": fake.url()
          }}, **kwargs)

def _expected_errors(testapp, test_name, method, url_to_test, user_password_tuple, url_param_values={},
                     query_params={}, post_data={}, resource_name='User', debug=False):
    if test_name != 'not_logged_in':
        resp1 = testapp.post_json(url_for(USER_LOGIN_ROUTE), {'user': {'email': user_password_tuple[0],
                                                                       'password': user_password_tuple[1]}})
        if method == 'GET':
            print('ENTRY POINT (logged in)')
            resp = testapp.get(url_for(url_to_test, **query_params, **url_param_values), headers={
                'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])}, expect_errors=True)
            print('WTF?!?!', resp)
        elif method == 'POST':
            resp = testapp.post_json(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
                'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])}, expect_errors=True)
        elif method == 'PATCH':
            resp = testapp.patch_json(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
                'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])}, expect_errors=True)
        elif method == 'DELETE':
            resp = testapp.delete(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
                'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])}, expect_errors=True)
        elif method == 'PUT':
            resp = testapp.put(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
                'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])}, expect_errors=True)
    else:
        if method == 'GET':
            print('ENTRY POINT (logged in)')
            resp = testapp.get(url_for(url_to_test, **query_params, **url_param_values), expect_errors=True)
            print('WTF?!?!', resp)
        elif method in ('POST', 'PATCH'):
            resp = testapp.post_json(url_for(url_to_test, **query_params, **url_param_values), post_data,
                                     expect_errors=True)
        elif method == 'DELETE':
            resp = testapp.delete(url_for(url_to_test, **query_params, **url_param_values), post_data,
                                  expect_errors=True)
        elif method == 'PUT':
            resp = testapp.put(url_for(url_to_test, **query_params, **url_param_values), post_data,
                                  expect_errors=True)

    # from pprint import pprint
    # print('THE TESTS IS: ', test_name, resp.status_code)
    # pprint(resp.json)
    # pprint(ERRORS_FOR_ACTIVITIES[test_name][1] if test_name not in LAMBDA_ERRORS else
    #         ERRORS_FOR_ACTIVITIES[test_name](resource_name)[1])
    assert resp.status_code == ERRORS_FOR_ACTIVITIES[test_name][0] if test_name not in LAMBDA_ERRORS else \
        ERRORS_FOR_ACTIVITIES[test_name](resource_name)[0]
    if 'message' in resp.json:
        assert resp.json['error'] == True
        assert resp.json['type'] == 'error'
        assert resp.json['message'] == resp.json['errors'] == (ERRORS_FOR_ACTIVITIES[test_name][1] if
                                                               test_name not in LAMBDA_ERRORS else
                                                               ERRORS_FOR_ACTIVITIES[test_name](resource_name)[1])
    else:
        assert resp.json['msg'] == ERRORS_FOR_ACTIVITIES[test_name][1] if test_name not in LAMBDA_ERRORS else \
            ERRORS_FOR_ACTIVITIES[test_name](resource_name)[1]
    assert False if debug else True

def _expected_successes(testapp, test_name, method, url_to_test, user_password_tuple, url_param_values={},
                        query_params={}, post_data={}, pkey1='activity', pkey2='', resource=None, api_message='Success',
                        expectations=None, attrs_extras={}, debug=False):
    resp1 = testapp.post_json(url_for(USER_LOGIN_ROUTE), {'user': {'email': user_password_tuple[0],
                                                                   'password': user_password_tuple[1]}})
    if method == 'GET':
        resp = testapp.get(url_for(url_to_test, **query_params, **url_param_values), headers={
            'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])})
    elif method == 'POST':
        resp = testapp.post_json(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
            'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])})
        resource = resource if not isinstance(resource, BaseQuery) else resource.one()
        if isinstance(resource, list) and isinstance(resource[0], BaseQuery):
            resource = [r.one() for r in resource]
    elif method == 'PATCH':
        resp = testapp.patch_json(url_for(url_to_test, **query_params, **url_param_values), post_data, headers={
            'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])})
        resource = resource if not isinstance(resource, BaseQuery) else resource.one()
        if isinstance(resource, list) and isinstance(resource[0], BaseQuery):
            resource = [r.one() for r in resource]
    elif method == 'DELETE':
        resp = testapp.delete(url_for(url_to_test, **query_params, **url_param_values), headers={
            'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])})
        resource = resource if not isinstance(resource, BaseQuery) else resource.all()
    elif method == 'PUT':
        resp = testapp.put(url_for(url_to_test, **query_params, **url_param_values), headers={
            'Authorization': 'Token {}'.format(resp1.json['user']['access_token'])})
        resource = resource if not isinstance(resource, BaseQuery) else resource.all()

    REQUIRED_KEYS, REQUIRED_ATTRS = expectations if expectations else (USER_LEVEL_1_KEYS, USER_PER_ACTIVITY_ATTRS)

    assert resp.status_code == RETURN_FOR_SINGLE_OR_MANY[test_name][0]
    assert resp.json['error'] == False
    assert resp.json['type'] == 'success'
    assert resp.json['message'] == api_message
    # check for all the keys we want per individual item
    from pprint import pprint
    # pprint(resp.json['data'])
    # print('*'*40)
    # print(pkey1,REQUIRED_KEYS)
    # pprint(REQUIRED_KEYS(pkey1))
    # pprint([(key, resp.json['data'][key]) for key in REQUIRED_KEYS(pkey1)])
    assert all([bool(resp.json['data'][key]) if not isinstance(resp.json['data'][key], bool) and
                                                resp.json['data'][key] != [] else
                resp.json['data'][key] is not None for key in REQUIRED_KEYS(pkey1)])
    if pkey1 and pkey1.endswith('s') or pkey2 and pkey2.endswith('s'):  # inferring "many"
        inner_pkey = pkey1 if not pkey2 else pkey2
        more_for_attrs = lambda id: None
        # print('-'*40)
        # print(inner_pkey)
        # pprint(resp.json['data'][inner_pkey.split('.')[0]])
        activity_list = [r[inner_pkey.split('.')[1]] for r in resp.json['data'][inner_pkey.split('.')[0]]] \
            if '.' in inner_pkey else resp.json['data'][inner_pkey]
        # print('*'*40)
        # pprint(activity_list)
        if pkey2.endswith('s'):
            for sub_activity_list in activity_list:
                assert all([k in activity for k in REQUIRED_ATTRS(resource[0], attrs_extras)] for activity in
                           sub_activity_list)
        else:
            # print('RESOURCE:', resource, 'KEY (inner): ', inner_pkey, ' PKEY1: ', pkey1, ' PKEY2: ', pkey2)
            # pprint(attrs_extras)
            # late in the game hack to account for PATCH:/activities/<ID>
            resource = resource if isinstance(resource, list) else [resource]
            if isinstance(resource[0], Activity) and resource[0].type != 'Employee' and method == 'PATCH':
                employees = {e.user.uuid: e for e in resource[0].employees()}
                more_for_attrs = lambda id: employees[id]
                # act = resource[0]
                # pprint({e.id:[(a.id, a.workcategorization_id, act.id==a.workcategorization_id, a.employee_id, e.id == a.employee_id, a.department_id) for a in e.assigned_work()] for id,e in employees.items()})
                # pprint(Work.query.filter(Work.workcategorization_id == act.id).all())
                # for _,ee in employees.items():
                #     print(Work.query.filter(Work.workcategorization_id == act.id, Work.employee_id == ee.id).one())
                assert all([k in activity for k in REQUIRED_ATTRS(
                    resource[0], attrs_extras, more_for_attrs(activity['user_id']))] for activity in activity_list)
            else:
                assert all([k in activity for k in REQUIRED_ATTRS(resource[0], attrs_extras)] for activity in
                           activity_list)
        for idx, res in enumerate(resource):
            # print('RESOURCE:', res, 'KEY (inner): ', inner_pkey, ' PKEY1: ', pkey1, ' PKEY2: ', pkey2)
            # pprint(activity_list)
            # print('*'*50)
            # pprint(REQUIRED_ATTRS(res, attrs_extras))
            if pkey2.endswith('s'):
                for sub_activity_list in activity_list:
                    # pprint(sub_activity_list)
                    # pprint([[(activity[k]==v, activity[k], v) for k,v in REQUIRED_ATTRS(res, attrs_extras, more_for_attrs(activity['user_id']) if 'user_id' in activity else None).items()] for
                    #         activity in sub_activity_list])
                    assert all([activity[k] == v for k,v in REQUIRED_ATTRS(res, attrs_extras, more_for_attrs(activity['user_id']) if 'user_id' in activity else None).items()] for activity in
                               sub_activity_list)
            else:
                # if not isinstance(res, Activity):
                #     assert all([activity_list[idx][k] == v for k, v in REQUIRED_ATTRS(res, attrs_extras).items()])
                # else:
                # pprint([[(activity[k]==v, activity[k], v) for k,v in REQUIRED_ATTRS(res, attrs_extras, more_for_attrs(activity['user_id']) if 'user_id' in activity else None).items()] for
                #         activity in activity_list])
                assert all([activity[k] == v for k,v in REQUIRED_ATTRS(res, attrs_extras, more_for_attrs(activity['user_id']) if 'user_id' in activity else None).items()] for activity in
                           activity_list)
    elif pkey1:
        # print('RESOURCE:')
        # pprint([(k, k in resp.json['data'][pkey1]) for k in REQUIRED_ATTRS(resource, attrs_extras)])
        assert all(k in resp.json['data'][pkey1] for k in REQUIRED_ATTRS(resource, attrs_extras))
        # print('-'*50)
        # pprint([(k, resp.json['data'][pkey1][k] == v, resp.json['data'][pkey1][k], v) for k, v in REQUIRED_ATTRS(resource, attrs_extras).items()])
        assert all(resp.json['data'][pkey1][k] == v for k, v in REQUIRED_ATTRS(resource, attrs_extras).items() if
                   k not in CALCULATED_ACTIVITY_KEYS)
    else:
        # print('RESOURCE:')
        pprint([(k, k in resp.json['data']) for k in REQUIRED_ATTRS(resource, attrs_extras)])
        assert all(k in resp.json['data'] for k in REQUIRED_ATTRS(resource, attrs_extras))
        # print('-'*50)
        # pprint([(k, resp.json['data'][k] == v, resp.json['data'][k], v) for k, v in REQUIRED_ATTRS(resource, attrs_extras).items()])
        assert all(resp.json['data'][k] == v for k, v in REQUIRED_ATTRS(resource, attrs_extras).items() if k not in
                   CALCULATED_ACTIVITY_KEYS)

    if debug:
        from pprint import pprint
        print('-'*80)
        print(resp.status_code)
        pprint(resp.json)
        print('-'*80)
    assert False if debug else True
    return resp.json

def _create_employee_department_client_with_activities(make_dept_wc=True, make_client_wc=True, client=None, notes=False,
                                                       all_employees=False, add_allocations=False, add_focus=False):
    client = ClientFactory().save() if not client else client
    department = DepartmentFactory.create(client=client).save()
    employee = UserProfileFactory()
    employee.client_id = client.id
    employee.department_id = department.id
    employee.save()

    all_employees = {'all_employees': True} if all_employees else {}
    myfocus = {'my_focus': True} if add_focus else {}
    dept_wc, client_wc = None, None
    ee_wc = WorkCategorizationFactory.create(owner_id=employee.id, type='Employee', **myfocus).save()
    ee_allocations, dept_allocations, client_allocations = [], [], []
    ee_notes, dept_notes, client_notes = [], [], []
    for i in range(add_allocations if isinstance(add_allocations, int) else randint(1,20)):
        ee_allocations += [Allocation(ee_wc, fake.word(), fake.word() + '|' + fake.word()).save()]
    for i in range(notes if isinstance(notes, int) else randint(1,20)):
        ee_notes += [Note(fake.sentence(), ee_wc.owner, ee_wc).save()]
    if make_dept_wc:
        dept_wc = WorkCategorizationFactory.create(owner_id=department.id, type='Department',
                                                   **all_employees, **myfocus).save()
        for i in range(add_allocations if isinstance(add_allocations, int) else randint(1,20)):
            dept_allocations += [Allocation(dept_wc, fake.word(), fake.word() + '|' + fake.word()).save()]
        for i in range(notes if isinstance(notes, int) else randint(1, 20)):
            dept_notes += [Note(fake.sentence(), choice(dept_wc.owner.staff.all()), dept_wc).save()]
    if make_client_wc:
        client_wc = WorkCategorizationFactory.create(owner_id=client.id, type='Client',
                                                     **all_employees, **myfocus).save()
        for i in range(add_allocations if isinstance(add_allocations, int) else randint(1,20)):
            client_allocations += [Allocation(client_wc, fake.word(), fake.word() + '|' + fake.word()).save()]
        for i in range(notes if isinstance(notes, int) else randint(1, 20)):
            client_notes += [Note(fake.sentence(), choice(client_wc.owner.staff.all()), client_wc).save()]

    if add_allocations:
        return (ee_wc, dept_wc, client_wc, ee_allocations, dept_allocations, client_allocations)
    if notes:
        return (ee_wc, dept_wc, client_wc, ee_notes, dept_notes, client_notes)
    return (ee_wc, dept_wc, client_wc)

def _add_client_and_dept():
    from kunin.user.models import User
    user = User.query.filter(User.username == 'foobar').one()
    employee = user.profile
    client = ClientFactory().save()
    employee.client = client
    user.client = client
    employee.department = DepartmentFactory.create(client=client)
    employee.save()
    return client, employee.department

def _create_ee_in_client_dept_with_password_possibly_staff(client, department, reportee=None):
    employee = UserFactory.create(client=client).save().profile
    employee.department = department
    employee.save()
    employee.user.set_password('secret_pwd')
    if reportee and isinstance(reportee, (list, tuple)):
        for report in reportee:
            report.parent_id = employee.id
            report.save()
    elif reportee:
        reportee.parent_id = employee.id
        reportee.save()
    return employee

def _create_division_atop_department(client, department):
    division = DepartmentFactory.create(client=client)
    department.parent_id = division.id
    department.save()
    return department, division

def _periods_generator(num_hrs=8):
    periods = [str(i+randint(0,23-num_hrs)) for i in range(num_hrs)]
    focus_or_working = lambda start: [start, randint(start+1,59)]
    return {p: {'focus': focus_or_working(randint(0,58)), 'working': focus_or_working(randint(0,58))} for p in periods}

########################################################################################################################
# THE TESTS
########################################################################################################################
class TestActivity:

    def test_get_user_activities_errors(self, testapp):
        url_to_test = 'activities.get_user_activities'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities(
            make_dept_wc=False, make_client_wc=False)
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={'user': ee_wc.owner.username}, post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'user': ee_wc.owner.username}, post_data={})
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'user': 'foobar'}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_bosses'
        boss_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        client = boss_wc.owner.client
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.save()
        employee.user.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': the_boss.user.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_non_reports'
        boss2 = UserFactory.create(client=client).save().profile
        employee2 = UserFactory.create(client=client).save().profile
        employee2.parent_id = boss2.id
        employee2.save()
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': employee2.user.id}, post_data={})

    def test_get_user_activities(self, testapp):
        url_to_test = 'activities.get_user_activities'
        # ============================================================================================================ #
        test_name = 'get_single'
        ee_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'user': ee_wc.owner.username}, post_data={}, pkey1='activity',
                            resource=ee_wc, api_message='Success')
        # ============================================================================================================ #
        test_name = 'get_many'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities(all_employees=True)
        ee_wc.owner.user.set_password('secret_pwd')
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'user': 'current'}, post_data={}, pkey1='activities',
                            resource=[ee_wc, dept_wc, client_wc], api_message='Success')
        # ============================================================================================================ #
        test_name = 'get_single'  #  Activity for Staff who REPORTS to me (my staff)
        ee_user_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        client = ee_user_wc.owner.client
        employee = ee_user_wc.owner
        the_boss = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.save()
        the_boss.user.set_password('secret_pwd')
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(the_boss.email, 'secret_pwd'),
                            url_param_values={'user': employee.user.id}, post_data={}, pkey1='activity',
                            resource=ee_user_wc, api_message='Success')
        # ============================================================================================================ #
        test_name = 'get_user_activity_format_aggregate'
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(the_boss.email, 'secret_pwd'),
                            url_param_values={'user': employee.user.id}, query_params={'format': 'aggregate'},
                            post_data={}, pkey1='activity', resource=ee_user_wc, api_message='Success')
        # ============================================================================================================ #
        test_name = 'get_user_activities_format_aggregate'
        ee_wc2 = WorkCategorizationFactory.create(type='Employee', owner_id=employee.id).save()
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(the_boss.email, 'secret_pwd'),
                            url_param_values={'user': employee.user.id}, query_params={'format': 'aggregate'},
                            post_data={}, pkey1='activities', resource=[ee_user_wc, ee_wc2], api_message='Success')
        # ============================================================================================================ #
        test_name = 'get_user_activities_format_hourly_or_daily'
        for fmt in ('hourly', 'daily'):
            attrs_extras = {'periods': _periods_generator(randint(4,12))}
            _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                user_password_tuple=(the_boss.email, 'secret_pwd'), attrs_extras=attrs_extras,
                                url_param_values={'user': employee.user.id}, query_params={'format': fmt},
                                post_data={}, pkey1='activities', resource=[ee_user_wc, ee_wc2], api_message='Success')

    def test_get_div_dept_activities_errors(self, testapp):
        url_to_test = 'activities.get_div_dept_activities'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={'division': dept_wc.owner.id,
                                                                         'department': dept2.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14}, post_data={}, resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14}, post_data={}, resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_resource_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id}, post_data={})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_many_from_specific_department_format_aggregate_by_employee'
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        # 10 department activities, 3 are my_focus
        all_activities = [dept_wc]
        all_my_focus = []
        for i in range(9):
            all_activities += [WorkCategorizationFactory.create(type='Department', owner_id=department.id)]
            if i % 3 == 0:
                all_activities[-1].my_focus = True
                all_activities[-1].save()
                all_my_focus += [all_activities[-1]]
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id},
                         query_params={'format': 'aggregate'}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_many_for_all_departments_format_aggregate_by_employee'
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), url_param_values=
                         {'division': division.id, 'department': 'all'}, query_params={'format': 'aggregate'})
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values=
                         {'division': division.id, 'department': 'all'}, query_params={'format': 'aggregate'})

    def test_get_div_dept_activities(self, testapp):
        url_to_test = 'activities.get_div_dept_activities'
        # ============================================================================================================ #
        test_name = 'get_single'
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activity', resource=dept_wc, api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activity', resource=dept_wc, api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activity', resource=dept_wc, api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many'
        co2_dept_wc = WorkCategorizationFactory.create(owner_id=department.id, type='Department').save()
        department.workcategorizations.append(co2_dept_wc)
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activities', resource=[dept_wc, co2_dept_wc], api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activities', resource=[dept_wc, co2_dept_wc], api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id}, post_data={},
                            pkey1='activities', resource=[dept_wc, co2_dept_wc], api_message='Success',
                            expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many_from_specific_department_format_aggregate'
        # 10 department activities, 3 are my_focus
        all_activities = [dept_wc, co2_dept_wc]
        all_my_focus = []
        for i in range(8):
            all_activities += [WorkCategorizationFactory.create(type='Department', owner_id=department.id)]
            if i % 3 == 0:
                all_activities[-1].my_focus = True
                all_activities[-1].save()
                all_my_focus += [all_activities[-1]]
        attrs_extras = {'trends': [], 'average_employee_hours': lambda r: 45 / len(r.owner.staff.all()),
                        'total_employees': lambda r: len(r.owner.staff()),
                        'achieved_time': lambda r: r.assigned_time*randint(0, r.assigned_time),
                        'achieved_percentage': lambda r: (r.assigned_percent/100)*randint(0,200),
                        'flow': [randint(0,24), randint(0,24)]}
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            query_params={'format': 'aggregate'}, post_data={}, pkey1='activities',
                            resource=all_activities, api_message='Success', attrs_extras=attrs_extras,
                            expectations=(DEPT_AGGREGATE_LEVEL_1_KEYS, DEPT_AGGREGATE_PER_ACTIVITY_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many_from_all_departments_format_aggregate'
        _, dept2_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        co2_dept = dept2_wc.owner
        co2_dept.parent_id = division.id
        co2_dept.save()
        # 10 department activities, 3 are my_focus
        all_activities2 = [dept2_wc]
        all_my_focus2 = []
        for i in range(3):
            all_activities2 += [WorkCategorizationFactory.create(type='Department', owner_id=co2_dept.id)]
            if i % 3 == 0:
                all_activities2[-1].my_focus = True
                all_activities2[-1].save()
                all_my_focus2 += [all_activities2[-1]]
        div_wc = WorkCategorizationFactory.create(type='Department', owner_id=division.id) # executive focus
        div_wc.my_focus = True
        div_wc.save()
        for activities in ({}, {'activity': 'all'}):
            _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                                {**{'division': division.id, 'department': 'all'}, **activities},
                                query_params={'format': 'aggregate'}, post_data={}, pkey1='executive',
                                pkey2='departments.activities', resource=all_activities2, api_message='Success',
                                expectations=(ALL_DEPT_AGGREGATE_LEVEL_1_KEYS, DEPT_AGGREGATE_PER_ACTIVITY_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_single_from_specific_department_format_hourly_or_daily'
        co2_ee_wc, co2_dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        co2_dept_wc.my_focus = True
        co2_dept_wc.save()
        co2_ee = co2_ee_wc.owner
        co2_ee.user.set_password('secret_pwd')
        co2_dept, co2_div = _create_division_atop_department(co2_ee.client, co2_ee.department)
        co2_boss = _create_ee_in_client_dept_with_password_possibly_staff(co2_ee.client, co2_dept, co2_ee)
        vp2 = _create_ee_in_client_dept_with_password_possibly_staff(co2_ee.client, co2_div)

        attrs_extras = {'trends': [], 'average_employee_hours': lambda r: 45 / len(r.owner.staff.all()),
                        'total_employees': lambda r: len(r.owner.staff()),
                        'achieved_time': lambda r: r.assigned_time*randint(0, r.assigned_time),
                        'achieved_percentage': lambda r: (r.assigned_percent/100)*randint(0,200),
                        'flow': [randint(0,24), randint(0,24)], 'periods': _periods_generator(randint(4,12))}
        for activities in ({}, {'activity': 'all'}):
            for fmt in ('hourly', 'daily'):
                _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                    user_password_tuple=(co2_boss.email, 'secret_pwd'), url_param_values=
                                    {**{'division': co2_div.id, 'department': co2_dept.id}, **activities},
                                    query_params={'format': fmt}, post_data={}, pkey1='activity',
                                    resource=co2_dept_wc, api_message='Success', attrs_extras=attrs_extras,
                                    expectations=(DEPT_AGGREGATE_LEVEL_1_KEYS, DEPT_AGGREGATE_PER_ACTIVITY_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many_or_all_from_specific_department_format_hourly_or_daily'
        co2_dept_wc2 = WorkCategorizationFactory.create(type='Department', owner_id=co2_dept.id).save()
        for activities in ({}, {'activity': 'all'}):
            for fmt in ('hourly', 'daily'):
                _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                    user_password_tuple=(co2_boss.email, 'secret_pwd'), url_param_values=
                                    {**{'division': co2_div.id, 'department': co2_dept.id}, **activities},
                                    query_params={'format': fmt}, post_data={}, pkey1='activities',
                                    resource=[co2_dept_wc, co2_dept_wc2], api_message='Success',
                                    attrs_extras=attrs_extras, expectations=
                                    (DEPT_AGGREGATE_LEVEL_1_KEYS, DEPT_AGGREGATE_PER_ACTIVITY_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many_from_specific_activity_format_employee_targets_ids'
        ee2_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        dept_wc.all_employees = True
        employee1, employee2 = ee_wc.owner, ee2_wc.owner
        employee2.department = department
        employee2.parent_id = boss.id
        employee2.save()
        # we remove pluralization and treat '_' and '+' as delimiters
        for spelling in ('employee_target_id', 'EMPLoyees+targets_ids', 'employee_taRgets_ID'):
            _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                user_password_tuple=(boss.email, 'secret_pwd'),
                                url_param_values={
                                    'division': division.id, 'department': department.id, 'activity': dept_wc.uuid},
                                post_data={}, pkey1='employees', query_params={'format': spelling},
                                resource=[employee1, employee2], api_message='Success',
                                expectations=(ACTIVITY_LEVEL_1_KEYS, EMPLOYEE_TARGETS_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_single_format_aggregate_and_hourly_by_employee'
        from kunin.taxonomy.workcategorization.serializers import EmployeeActivitySubSchema
        attrs_extras = EmployeeActivitySubSchema(many=True).dump([co2_ee])
        for activities in ({}, {'activity': 'all'}, {'activity': co2_dept_wc.id}):
            for fmt in ('hourly', 'daily'):
                _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                    user_password_tuple=(co2_boss.email, 'secret_pwd'), url_param_values=
                                    {**{'division': co2_div.id, 'department': co2_dept.id}, **activities},
                                    query_params={'format': 'aggregate+' + fmt, 'by': 'employee'}, pkey1='activities',
                                    resource=[co2_dept_wc, co2_dept_wc2], api_message='Success', attrs_extras=
                                    attrs_extras, expectations=
                                    (AGGREGATE_ACTIVITY_LEVEL1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS))
        # one with multiple employees...
        manager = co2_ee.department.manager()
        co2_ee2 = UserFactory.create(client=co2_ee.client, department=co2_ee.department).save().profile
        co2_ee2.department = co2_ee.department
        co2_ee2.parent_id = manager.id
        co2_ee2.save()
        attrs_extras = EmployeeActivitySubSchema(many=True).dump([co2_ee, co2_ee2])
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(co2_boss.email, 'secret_pwd'),
                            url_param_values={'division': co2_div.id, 'department': co2_dept.id},
                            query_params={'format': 'aggregate+hourly', 'by': 'employee'}, pkey1='activities',
                            resource=[co2_dept_wc, co2_dept_wc2], api_message='Success', attrs_extras=attrs_extras,
                            expectations=(AGGREGATE_ACTIVITY_LEVEL1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS))
        # JUST by=employee
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(co2_boss.email, 'secret_pwd'),
                            url_param_values={'division': co2_div.id, 'department': co2_dept.id},
                            query_params={'by': 'employee'}, pkey1='activities',
                            resource=[co2_dept_wc, co2_dept_wc2], api_message='Success', attrs_extras=attrs_extras,
                            expectations=(AGGREGATE_ACTIVITY_LEVEL1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_departments_by_employee'  # definitely NOT the right place for this
        from kunin.taxonomy.department.serializers import (departments_within_employees_schema,
                                                           divisions_within_employees_schema)
        attrs_extras = lambda ee: {**departments_within_employees_schema.dump([ee.department]),
            **divisions_within_employees_schema.dump([ee.department.path_to_root()[-1]])}
        for activities in ({}, {'activity': 'all'}):
            _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                user_password_tuple=(co2_boss.email, 'secret_pwd'),
                                url_param_values={**{'division': co2_div.id, 'department': 'all'}, **activities},
                                query_params={'by': 'employee'}, pkey1='employees',
                                resource=[co2_ee, co2_ee2], api_message='Success', attrs_extras=attrs_extras,
                                expectations=(EE_DIV_DEPT_REQUIRED_KEYS, EMPLOYEE_DIV_DEPT_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_department_employees_by_focus_ie_the_leaderboard'
        from kunin.profile.models import UserProfile as Employee
        from ..models.taxonomy.test_departments import TestDepartment
        # let's put EVERYONE in one client and department
        department = TestDepartment.create_client_with_one_dept_and_some_staff()
        manager = Employee.query.filter(Employee.client_id == department.client_id, Employee.level == 1).one()
        manager.user.set_password('secret_pwd')

        division = TestDepartment.create_client_with_one_dept_and_some_staff(client=department.client)
        department.parent_id = division.id
        department.save()

        # make a bunch of activities for this client
        for employee in [ee for ee in Employee.query.filter(Employee.client_id == department.client_id).all() if ee.employee_type == 'Employee']:
            for i in range(randint(1,3)):
                WorkCategorizationFactory.create(owner_id=employee.id, type='Employee').save()
        for i in range(randint(5,10)):
            WorkCategorizationFactory.create(owner_id=department.id, type='Department').save()
        for i in range(randint(5,10)):
            WorkCategorizationFactory.create(owner_id=department.client.id, type='Client').save()
        attrs_extras = lambda ee: {'total_focus': 1, 'flow': [2,3]}
        resources = department.contributors()
        for count in ({}, {'count': randint(1,len(resources))}):
            for by in ({'by': 'focus'}, {'by': 'flow'}):
                payload = _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                                              user_password_tuple=(manager.user.email, 'secret_pwd'),
                                              url_param_values={'division': division.id, 'department': department.uuid},
                                              query_params={**by,**count}, pkey1='employees', resource=resources,
                                              api_message='Success', attrs_extras=attrs_extras, expectations=
                                              (DEPT_LEVEL_1_KEYS, EMPLOYEE_DIV_DEPT_ATTRS))
                employees = payload['data']['employees']
                if by['by'] == 'flow':
                    by_what = by['by']
                    flow = lambda ee: float(str(ee[by_what][1]).replace(':', '.')) - \
                                      float(str(ee[by_what][0]).replace(':', '.'))
                    assert all(flow(employees[i]) >= flow(employees[i+1]) for i in range(len(employees) - 1))
                else:
                    by_what = 'total_' + by['by']
                    assert all(employees[i][by_what] >= employees[i+1][by_what] for i in range(len(employees) - 1))
                if count:
                    assert len(employees) == count['count']

        #####
        # FOCUS (in LEADERBOARD: )
        #####
        #
        # "department_name": employee.department.name,
        # "department_id": employee.department.uuid,
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "manager": {
        #   "first_name": manager.first_name,
        #   "last_name": manager.last_name,
        #   "user_id": manager.uuid
        # },
        # "employees": [
        #   {
        #   "user_id": employee.user.uuid,
        #   "first_name": employee.first_name,
        #   "last_name": employee.last_name,
        #    "total_focus", calculated.total_focus,
        #    "flow": calculated.flow
        #    },
        #  ]

        # BY=EMPLOYEE (in departments/all/activities?by=employee) TEMPORARY - it doesn't make sense here
        # BY=EMPLOYEE (in departments[,/all]?by=employee) SHOULD BE IN DEPARTMENTS  # TODO: put a route in departments
        # TODO: put a similar route in employees
        #####
        #
        # "employees": [
        #   {
        #   "user_id": employee.user.uuid,
        #   "first_name": employee.first_name,
        #   "last_name": employee.last_name,
        #   "divisions": [
        #       {
        #       "division_name": employee.department.path_to_root().all()[-1].name,
        #       "division_id": employee.department.path_to_root().all()[-1].uuid
        #       }
        #   ],
        #   "departments": [
        #       {
        #       "department_name": employee.department.name,
        #       "department_id": employee.department.uuid
        #       },
        #   ]
        #   },
        # ]
        #

        # AGGREGATE+(HOURLY OR DAILY) (in departments/<department_ID>/activities/all?format=aggregate+hourly)
        #   WITH BY=EMPLOYEE
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "employees": [
        #       {
        #           "user_id": employee.user.uuid,
        #           "first_name": employee.first_name,
        #           "last_name": employee.last_name,
        #           "assigned_time": activity1.assigned_time,
        #           "assigned_percentage": activity1.assigned_percent,
        #           "achieved_time": calculated.achieved_time,
        #           "achieved_percentage": calculated.achieved_percent,
        #           "trend": calculated.trends,
        #           "flow": calculated.flow
        #           "total_focus": calculated.total_focus,
        #           "notes": bool(activity1.notes),
        #           "periods": {
        #               "7": {"focus": calculated.focus, "working": calculated.working},
        #           },
        #    ]
        # ]
        #

        # AGGREGATE+(HOURLY OR DAILY) (in departments/<department_ID>/activities/<activity_ID>?format=aggregate+hourly&by=employee)
        #   WITH BY=EMPLOYEE
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "activities": [
        #       {
        #       "activity_name": activity1.name,
        #       "activity_id": activity1.uuid,
        #       "employees": [
        #           {
        #           "user_id": employee.user.uuid,
        #           "first_name": employee.first_name,
        #           "last_name": employee.last_name,
        #           "assigned_time": activity1.assigned_time,
        #           "assigned_percentage": activity1.assigned_percent,
        #           "achieved_time": calculated.achieved_time,
        #           "achieved_percentage": calculated.achieved_percent,
        #           "trend": calculated.trends,
        #           "flow": calculated.flow
        #           "total_focus": calculated.total_focus,
        #           "notes": bool(activity1.notes),
        #           "periods": {
        #               "7": {"focus": calculated.focus, "working": calculated.working},
        #           },
        #       ]
        #   ]
        # ]
        #

        # EMPLOYEE_TARGETS_IDS (in departments/<department_ID>/activities/<activity_ID>?format=employee_targets_ids)
        #####
        #
        #       "activity_name": activity.name,
        #       "activity_id": activity.uuid,
        #       "assigned_time": activity.assigned_time,
        #       "assigned_percentage": activity.assigned_percent,
        #       "my_focus": activity.my_focus,
        #       "all_employees": activity.all_employees,
        #       "employees": [
        #           {
        #           "username": employee.user.username,
        #           "user_id": employee.user.uuid,
        #           "first_name": employee.first_name,
        #           "last_name": employee.last_name,
        #           "general_target": {
        #               "assigned_time": employee.activity.assigned_time,
        #               "assigned_percentage": employee.activity.assigned_percent
        #               },
        #           "unique_target": {
        #               "assigned_time": employee.activity.assigned_time,
        #               "assigned_percentage": employee.activity.assigned_time
        #               }
        #           },
        #       ]
        #

        # HOURLY OR DAILY (in departments/<department_ID>/activities?format=hourly)
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "executive": {
        #                "first_name": executive.first_name,
        #                "last_name": executive.last_name,
        #                "user_id": executive.uuid
        #            },
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "my_focus": [
        #     {
        #         "activity_name": activity_focus.name,
        #         "activity_id": activity_focus.uuid,
        #         "achieved_time": calculated.achived_time,
        #         "target_time": activity_focus.assigned_time
        #     },
        # ],
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "activities": [
        #       {
        #       "activity_name": activity1.name,
        #       "activity_id": activity1.uuid,
        #       "trend": calculated.trends,
        #       "average_employee_hours": calculated.hours_total / len(activity1.department.staff),
        #       "total_employes": len(activity1.department.staff),
        #       "assigned_time": activity1.assigned_time,
        #       "assigned_percentage": activity1.assigned_percent,
        #       "achieved_time": calculated.achieved_time,
        #       "achieved_percentage": calculated.achieved_percent,
        #       "flow": calculated.flow,
        #       "periods": {
        #           "7": {"focus": calculated.focus, "working": calculated.working},
        #       },
        #   ]
        # ]
        #

        # AGGREGATE (in departments/all/activities?format=aggregate)
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "executive": {
        #                "first_name": executive.first_name,
        #                "last_name": executive.last_name,
        #                "user_id": executive.uuid
        #            },
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "my_focus": [
        #     {
        #         "activity_name": activity_focus.name,
        #         "activity_id": activity_focus.uuid,
        #         "achieved_time": calculated.achived_time,
        #         "target_time": activity_focus.assigned_time
        #     },
        # ],
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "activities": [
        #       {
        #       "activity_name": activity1.name,
        #       "activity_id": activity1.uuid,
        #       "trend": calculated.trends,
        #       "average_employee_hours": calculated.hours_total / len(activity1.department.staff),
        #       "total_employes": len(activity1.department.staff),
        #       "assigned_time": activity1.assigned_time,
        #       "assigned_percentage": activity1.assigned_percent,
        #       "achieved_time": calculated.achieved_time,
        #       "achieved_percentage": calculated.achieved_percent,
        #       "flow": calculated.flow
        #       },
        #   ]
        # ]
        #

        # HOURLY OR DAILY (in departments/<department_ID>/activities?format=hourly)
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "executive": {
        #                "first_name": executive.first_name,
        #                "last_name": executive.last_name,
        #                "user_id": executive.uuid
        #            },
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "my_focus": [
        #     {
        #         "activity_name": activity_focus.name,
        #         "activity_id": activity_focus.uuid,
        #         "achieved_time": calculated.achived_time,
        #         "target_time": activity_focus.assigned_time
        #     },
        # ],
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "activities": [
        #       {
        #       "activity_name": activity1.name,
        #       "activity_id": activity1.uuid,
        #       "trend": calculated.trends,
        #       "average_employee_hours": calculated.hours_total / len(activity1.department.staff),
        #       "total_employes": len(activity1.department.staff),
        #       "assigned_time": activity1.assigned_time,
        #       "assigned_percentage": activity1.assigned_percent,
        #       "achieved_time": calculated.achieved_time,
        #       "achieved_percentage": calculated.achieved_percent,
        #       "flow": calculated.flow,
        #       "periods": {
        #           "7": {"focus": calculated.focus, "working": calculated.working},
        #       },
        #   ]
        # ]

        # EMPLOYEE_TARGETS_IDS (in departments/<department_ID>/activities/<activity_ID>?format=employee_targets_ids)
        #####
        #
        #       "activity_name": activity.name,
        #       "activity_id": activity.uuid,
        #       "assigned_time": activity.assigned_time,
        #       "assigned_percentage": activity.assigned_percent,
        #       "my_focus": activity.my_focus,
        #       "all_employees": activity.all_employees,
        #       "employees": [
        #           {
        #           "username": employee.user.username,
        #           "user_id": employee.user.uuid,
        #           "first_name": employee.first_name,
        #           "last_name": employee.last_name,
        #           "general_target": {
        #               "assigned_time": employee.activity.assigned_time,
        #               "assigned_percentage": employee.activity.assigned_percent
        #               },
        #           "unique_target": {
        #               "assigned_time": employee.activity.assigned_time,
        #               "assigned_percentage": employee.activity.assigned_time
        #               }
        #           },
        #       ]

        # AGGREGATE (in departments/all/activities?format=aggregate)
        #####
        #
        # "division_name": division.name,
        # "division_id": division.uuid,
        # "executive": {
        #                "first_name": executive.first_name,
        #                "last_name": executive.last_name,
        #                "user_id": executive.uuid
        #            },
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "my_focus": [
        #     {
        #         "activity_name": activity_focus.name,
        #         "activity_id": activity_focus.uuid,
        #         "achieved_time": calculated.achived_time,
        #         "target_time": activity_focus.assigned_time
        #     },
        # ],
        # "departments": [
        #   "department_name": department.name,
        #   "department_id": department.uuid,
        #   "manager": {
        #       "first_name": manager.first_name,
        #       "last_name": manager.last_name,
        #       "user_id": manager.uuid
        #   },
        #   "activities": [
        #       {
        #       "activity_name": activity1.name,
        #       "activity_id": activity1.uuid,
        #       "trend": calculated.trends,
        #       "average_employee_hours": calculated.hours_total / len(activity1.department.staff),
        #       "total_employes": len(activity1.department.staff),
        #       "assigned_time": activity1.assigned_time,
        #       "assigned_percentage": activity1.assigned_percent,
        #       "achieved_time": calculated.achieved_time,
        #       "achieved_percentage": calculated.achieved_percent,
        #       "flow": calculated.flow
        #       },
        #   ]
        # ]

        # AGGREGATE (in department/<dept_ID>/activities?format=aggregate)
        #####
        #
        # "department_name": department.name,
        # "department_id": department.uuid,
        # "manager": {
        #                "first_name": manager.first_name,
        #                "last_name": manager.last_name,
        #                "user_id": manager.uuid
        #            },
        # "from_date": query_params.from_date,
        # "to_date": query_params.to_date,
        # "my_focus": [
        #     {
        #         "activity_name": activity_focus.name,
        #         "activity_id": activity_focus.uuid,
        #         "achieved_time": calculated.achived_time,
        #         "target_time": activity_focus.assigned_time
        #     },
        # ],
        # "activities": [
        #     {
        #     "activity_name": activity1.name,
        #     "activity_id": activity1.uuid,
        #     "trend": calculated.trends,
        #     "average_employee_hours": calculated.hours_total / len(activity1.department.staff),
        #     "total_employes": len(activity1.department.staff),
        #     "assigned_time": activity1.assigned_time,
        #     "assigned_percentage": activity1.assigned_percent,
        #     "achieved_time": calculated.achieved_time,
        #     "achieved_percentage": calculated.achieved_percent,
        #     "flow": calculated.flow
        #     },
        # ]

    def test_post_assign_div_dept_activity_to_user_errors(self, testapp):
        url_to_test = 'activities.post_assign_department_activity'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        method = 'POST'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'assign_work_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'assign_work_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'assign_work_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [(ee_wc.owner.email, dept_wc.id), (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id), (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'assign_work_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))
        # ============================================================================================================ #
        test_name = 'assign_employee_work_in_div_or_dept'
        error_message = 'assign Work for Activity {} owned by {} using the route for "post_assign_department_activity"'
        # employee activities should not be delete via this route
        for usr, actvt, err in [(boss.email, ee_wc, error_message.format(ee_wc, 'Employee: ' + ee_wc.owner.uuid)),
                                (vp.email, ee_wc, error_message.format(ee_wc, 'Employee: ' + ee_wc.owner.uuid)),
                                (vp.email, div_wc, error_message.format(div_wc, 'Department: ' + div_wc.owner.uuid)),
                                (vp.email, client_wc, error_message.format(client_wc, 'Client: ' + client_wc.owner.uuid)),
                                ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt.id}, resource_name=err)
        # ============================================================================================================ #
        test_name = 'assign_work_with_bad_post_data'
        future_ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        employee = future_ee_wc.owner
        employee.user.set_password('secret_pwd')
        future_ee_wc.owner_id = None
        future_ee_wc.type = None
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)

        post_data = lambda extras={}: {
            'user': {
                **extras
        }}
        error_message = 'the proper use is ' + json.dumps({'user': {
            'username': '<username> OR',
            'user_id': '<user_id>|<user_uuid> OR',
            'email': '<user_email>',
        }})
        for pex in ({'target': {'assigned_time': 111, 'assigned_percent': 1.5}}, {'usr': employee.uuid}):
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(boss.email, 'secret_pwd'), post_data=post_data(pex),
                             url_param_values={'division': division.id, 'department': department.id, 'activity':
                                 dept_wc.uuid}, resource_name=error_message)

    def test_post_assign_div_dept_activity_to_user(self, testapp):
        url_to_test = 'activities.post_assign_department_activity'
        method = 'POST'
        post_data = lambda extras={}: {
            'user': {
                **extras
        }}
        # ============================================================================================================ #
        test_name = 'assign_single_no_previous'
        """test that we can assign a dept or client wc to an employee or department"""

        future_ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        employee = future_ee_wc.owner
        employee.user.set_password('secret_pwd')
        future_ee_wc.owner_id = None
        future_ee_wc.type = None
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, division)

        target = {'assigned_time': 120, 'assigned_percent': 25}
        activities_extras = {
            'general_target': {'assigned_time': 60, 'assigned_percentage': 12.5},
            'unique_target': {'assigned_time': target['assigned_time'],
                              'assigned_percentage': target['assigned_percent']}
        }

        attrs_extras = lambda ee: {
            'username': ee.username,
            'activities': [MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS(a, activities_extras) for a in
                           [Activity.get_by_id(w.workcategorization_id) for w in ee.assigned_work()]]
        }
        for attr, value in (('username', 'username'), ('user_id', 'uuid'), ('user_id', 'id'), ('email', 'email')):
            for tgt in ({'target': target}, {}):
                post_extras = {attr: getattr(employee, value), **tgt}
                _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                    user_password_tuple=(boss.email, 'secret_pwd'),
                                    url_param_values={'division': division.id, 'department': department.id,
                                                      'activity': dept_wc.uuid}, post_data=post_data(post_extras),
                                    pkey1='employees', attrs_extras=attrs_extras, resource=[employee],
                                    api_message='Activity added', expectations=
                                    (DEPT_LEVEL_1_KEYS, EMPLOYEE_DIV_DEPT_ATTRS))
                # cleaning up
                [w.delete() for w in employee.assigned_work()]

    def test_create_div_dept_activities_errors(self, testapp):
        url_to_test = 'activities.post_create_department_activity'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={'division': dept_wc.owner.id,
                                                                         'department': dept2.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14}, post_data={}, resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14}, post_data={}, resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={}, resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id}, post_data={})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_with_bad_post_data'
        resource_name = json.dumps({'activity': {
                'rulename': '<activity_name>',
                'assigned_time': '<int>',
                'assigned_percent': '<int>',
                'my_focus': '<bool>',
                'assignee': '<employee_ID>|all <-- OPTIONAL',
                'all_employees': '<bool> <-- OPTIONAL',
                'owner': 'me|Department|Division|Client|Organization <-- OPTIONAL',
                'type': 'Employee|Department|Client|Organization <-- OPTIONAL'
            }})
        post_data = {
            'rulename': fake.sentence(),
            'assigned_time': fake.time(),
            'my_focus': fake.boolean(),
        }
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id},
                         post_data=post_data, resource_name=resource_name)
        post_data = {
            'activity': {
                'assigned_time': fake.time(),
                'my_focus': fake.boolean(),
            }
        }
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id},
                         post_data=post_data, resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_insufficient_access'
        post_data = lambda bad_extras: {
            'activity': {
                'rulename': fake.sentence(),
                'assigned_time': fake.pyint(min_value=30, max_value=60 * 12),
                'assigned_percent': 72,
                'my_focus': fake.pybool(),
                **bad_extras
            }
        }
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, extra in [(ee_wc.owner.email, {'type': 'Department'}), (ee_wc.owner.email, {'type': 'Organization'}),
                           (ee_wc.owner.email, {'type': 'Division'}), (ee_wc.owner.email, {'type': 'Client'}),
                           (ee_wc.owner.email, {'owner': 'Department'}), (ee_wc.owner.email, {'owner': 'Organization'}),
                           (ee_wc.owner.email, {'owner': 'Division'}), (ee_wc.owner.email, {'owner': 'Client'}),
                           (ee_wc.owner.email, {'assignee': 'all'}), (ee_wc.owner.email, {'assignee': 66}),  #  not me
                           (ee_wc.owner.email, {'all_employees': True}),
                           (boss.email, {'type': 'Organization'}), (boss.email, {'type': 'Division'}),
                           (boss.email, {'type': 'Client'}), (boss.email, {'owner': 'Organization'}),
                           (boss.email, {'owner': 'Division'}), (boss.email, {'owner': 'Client'}),
                           (boss.email, {'assignee': other_dept_ee.uuid}),  #  employee in another dept
                           ]:
            _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
            (usr, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id},
                             post_data=post_data(extra), resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_bad_post_data'
        for usr, ex, rs in [# bad combinations of post keys
                           (boss.email, {'assignee': 'all', 'all_employees': False},
                            "'assignee' = 'all' WITH 'all_employee' = false"),
                           (boss.email, {'assignee': 'all', 'owner': 'me'}, "'assignee' = 'all' WITH 'owner' = 'me'"),
                           (boss.email, {'assignee': 'all', 'type': 'Employee'},
                            "'assignee' = 'all' WITH 'type' = 'Employee'"),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'all_employees': True},
                            "'assignee' = '{}' WITH 'all_employees' = true".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'owner': 'Department'},
                            "'assignee' = '{}' WITH 'owner' = 'Department'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'owner': 'Division'},
                            "'assignee' = '{}' WITH 'owner' = 'Division'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'owner': 'Client'},
                            "'assignee' = '{}' WITH 'owner' = 'Client'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'owner': 'Organization'},
                            "'assignee' = '{}' WITH 'owner' = 'Organization'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'type': 'Department'},
                            "'assignee' = '{}' WITH 'type' = 'Department'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'type': 'Division'},
                            "'assignee' = '{}' WITH 'type' = 'Division'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'type': 'Client'},
                            "'assignee' = '{}' WITH 'type' = 'Client'".format(ee_wc.owner.uuid)),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'type': 'Organization'},
                            "'assignee' = '{}' WITH 'type' = 'Organization'".format(ee_wc.owner.uuid)),
                           (boss.email, {'owner': 'me', 'assignee': 'Department'},
                            "'owner' = 'me' WITH 'assignee' = 'Department'"),
                           (boss.email, {'owner': 'me', 'assignee': 'Division'},
                            "'owner' = 'me' WITH 'assignee' = 'Division'"),
                           (boss.email, {'owner': 'me', 'assignee': 'Client'},
                            "'owner' = 'me' WITH 'assignee' = 'Client'"),
                           (boss.email, {'owner': 'me', 'assignee': 'Organization'},
                            "'owner' = 'me' WITH 'assignee' = 'Organization'"),
                           (boss.email, {'type': 'Employee', 'owner': 'Department'},
                            "'type' = 'Employee' WITH 'owner' = 'Department'"),
                           (boss.email, {'type': 'Employee', 'owner': 'Division'},
                            "'type' = 'Employee' WITH 'owner' = 'Division'"),
                           (boss.email, {'type': 'Employee', 'owner': 'Client'},
                            "'type' = 'Employee' WITH 'owner' = 'Client'"),
                           (boss.email, {'type': 'Employee', 'owner': 'Organization'},
                            "'type' = 'Employee' WITH 'owner' = 'Organization'"),
                            ]:
            _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
            (usr, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id},
                             post_data=post_data(ex), resource_name=rs)

    def test_create_div_dept_activities(self, testapp):
        url_to_test = 'activities.post_create_department_activity'
        # ============================================================================================================ #
        test_name = 'post_create'
        method = 'POST'
        assigned_time = fake.pyint(min_value=30, max_value=60 * 12)
        assigned_percent = int(assigned_time/60*12)
        post_data = lambda activity_name, extras={}: {
            'activity': {
                'rulename': activity_name,
                'assigned_time': assigned_time,
                'assigned_percent': assigned_percent,
                **extras
        }}

        # tests setup
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        employee = ee_wc.owner
        employee.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, division)

        activity_name = fake.sentence()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(employee.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            post_data=post_data(activity_name), pkey1='activity',
                            resource=Activity.query.filter(Activity.activity_name == activity_name),
                            api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

        activity_name = fake.sentence()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            post_data=post_data(activity_name), pkey1='activity',
                            resource=Activity.query.filter(Activity.activity_name == activity_name),
                            api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        assert Activity.query.filter(Activity.activity_name == activity_name).one().type == 'Department'
        assert Activity.query.filter(Activity.activity_name == activity_name).one().owner == boss.department

        activity_name = fake.sentence()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            post_data=post_data(activity_name), pkey1='activity',
                            resource=Activity.query.filter(Activity.activity_name == activity_name),
                            api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        assert Activity.query.filter(Activity.activity_name == activity_name).one().type == 'Department'
        assert Activity.query.filter(Activity.activity_name == activity_name).one().owner == vp.department

        activity_name = fake.sentence()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            post_data=post_data(activity_name, {'all_employees': True}), pkey1='activity',
                            resource=Activity.query.filter(Activity.activity_name == activity_name),
                            api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        assert Activity.query.filter(Activity.activity_name == activity_name).one().type == 'Department'
        assert Activity.query.filter(Activity.activity_name == activity_name).one().owner == vp.department
        assert bool(Activity.query.filter(Activity.activity_name == activity_name).one().all_employees)

        activity_name = fake.sentence()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id},
                            post_data=post_data(activity_name, {'type': 'Client'}), pkey1='activity',
                            resource=Activity.query.filter(Activity.activity_name == activity_name),
                            api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
        assert Activity.query.filter(Activity.activity_name == activity_name).one().type == 'Client'
        assert Activity.query.filter(Activity.activity_name == activity_name).one().owner == vp.client
        assert not bool(Activity.query.filter(Activity.activity_name == activity_name).one().all_employees)

        for usr, ex, t in [(employee.email, {'type': 'Employee'}, [('type', 'Employee'), ('owner', employee)]),
                           (employee.email, {'owner': 'me'}, [('type', 'Employee'), ('owner', employee)]),
                           (employee.email, {'assignee': employee.user.uuid}, [('type', 'Employee'),
                                                                                ('owner', employee)]),

                           (boss.email, {'type': 'Department'}, [('type', 'Department'), ('owner', boss.department)]),
                           (boss.email, {'owner': 'Department'}, [('type', 'Department'), ('owner', boss.department)]),

                           (vp.email, {'type': 'Department'}, [('type', 'Department'), ('owner', department)]),
                           (vp.email, {'type': 'Division'}, [('type', 'Division'), ('owner', division)]),
                           (vp.email, {'type': 'Organization'}, [('type', 'Client'), ('owner', vp.client)]),
                           (vp.email, {'type': 'Client'}, [('type', 'Client'), ('owner', vp.client)]),
                           (vp.email, {'owner': 'Department'}, [('type', 'Department'), ('owner', department)]),
                           (vp.email, {'owner': 'Division'}, [('type', 'Division'), ('owner', division)]),
                           (vp.email, {'owner': 'Organization'}, [('type', 'Client'), ('owner', vp.client)]),
                           (vp.email, {'owner': 'Client'}, [('type', 'Client'), ('owner', vp.client)]),

                            # all kinds of good combinations!
                           (employee.email, {'assignee': employee.user.uuid, 'owner': 'me'},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', False)]),
                           (employee.email, {'assignee': employee.user.uuid, 'type': 'Employee'},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', False)]),
                           (employee.email, {'assignee': employee.user.uuid, 'owner': 'me', 'type': 'Employee'},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', False)]),
                           (employee.email, {'assignee': employee.user.uuid, 'owner': 'me', 'my_focus': True},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', True)]),
                           (employee.email, {'assignee': employee.user.uuid, 'type': 'Employee', 'my_focus': True},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', True)]),
                           (employee.email, {'assignee': employee.user.uuid, 'owner': 'me',
                                             'type': 'Employee', 'my_focus': True},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', True)]),

                           (boss.email, {'assignee': employee.user.uuid, 'type': 'Employee'},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', False)]),
                           (boss.email, {'assignee': employee.user.uuid, 'type': 'Employee', 'my_focus': True},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', True)]),
                           (boss.email, {'assignee': 'all', 'type': 'Department'},
                            [('type', 'Department'), ('owner', department), ('all_employees', True),
                             ('my_focus', False)]),
                           (boss.email, {'assignee': 'all', 'type': 'Department', 'my_focus': True},
                            [('type', 'Department'), ('owner', department), ('all_employees', True),
                             ('my_focus', True)]),

                           (vp.email, {'assignee': employee.user.uuid, 'type': 'Employee'},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', False)]),
                           (vp.email, {'assignee': employee.user.uuid, 'type': 'Employee', 'my_focus': True},
                            [('type', 'Employee'), ('owner', employee), ('all_employees', False), ('my_focus', True)]),
                           (vp.email, {'assignee': boss.user.uuid, 'type': 'Employee'},
                            [('type', 'Employee'), ('owner', boss), ('all_employees', False), ('my_focus', False)]),
                           (vp.email, {'assignee': boss.user.uuid, 'type': 'Employee', 'my_focus': True},
                            [('type', 'Employee'), ('owner', boss), ('all_employees', False), ('my_focus', True)]),
                           (vp.email, {'assignee': 'all', 'type': 'Department'},
                            [('type', 'Department'), ('owner', department), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Department', 'owner': 'Department'},
                            [('type', 'Department'), ('owner', department), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Department', 'my_focus': True},
                            [('type', 'Department'), ('owner', department), ('all_employees', True), ('my_focus', True)]),
                           (vp.email, {'assignee': 'all', 'type': 'Division'},
                            [('type', 'Division'), ('owner', division), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Division', 'owner': 'Division'},
                            [('type', 'Division'), ('owner', division), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Division', 'my_focus': True},
                            [('type', 'Division'), ('owner', division), ('all_employees', True), ('my_focus', True)]),
                           (vp.email, {'assignee': 'all', 'type': 'Client'},
                            [('type', 'Client'), ('owner', vp.client), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Client', 'owner': 'Client'},
                            [('type', 'Client'), ('owner', vp.client), ('all_employees', True), ('my_focus', False)]),
                           (vp.email, {'assignee': 'all', 'type': 'Client', 'my_focus': True},
                            [('type', 'Client'), ('owner', vp.client), ('all_employees', True), ('my_focus', True)]),
                           ]:
            activity_name = fake.sentence()
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(usr, 'secret_pwd'),
                                url_param_values={'division': division.uuid, 'department': department.uuid},
                                post_data=post_data(activity_name, ex), pkey1='activity',
                                resource=Activity.query.filter(Activity.activity_name == activity_name),
                                api_message='Activity created', expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))
            for test in t:
                assert getattr(Activity.query.filter(Activity.activity_name == activity_name).one(), test[0]) == test[1]

    def test_delete_div_dept_activities_errors(self, testapp):
        url_to_test = 'activities.delete_department_activity'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        method = 'DELETE'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'delete_resource_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'delete_resource_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'delete_resource_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [(ee_wc.owner.email, dept_wc.id), (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id), (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'delete_resource_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))
        # ============================================================================================================ #
        test_name = 'delete_employee_resource_in_div_or_dept'
        error_message = 'delete Activity {} owned by {} using the route for "delete_department_activity"'
        # employee activities should not be delete via this route
        for usr, actvt, err in [(boss.email, ee_wc, error_message.format(ee_wc, 'Employee: ' + ee_wc.owner.uuid)),
                                (vp.email, ee_wc, error_message.format(ee_wc, 'Employee: ' + ee_wc.owner.uuid)),
                                (vp.email, div_wc, error_message.format(div_wc, 'Department: ' + div_wc.owner.uuid)),
                                (vp.email, client_wc, error_message.format(client_wc, 'Client: ' + client_wc.owner.uuid)),
                                ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt.id}, resource_name=err)

    def test_delete_div_dept_activities(self, testapp):
        url_to_test = 'activities.delete_department_activity'
        # ============================================================================================================ #
        test_name = 'delete_activity'
        method = 'DELETE'
        api_message = 'Activity deleted'
        # tests setup
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        employee = ee_wc.owner
        employee.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, division)
        # need a second Activity to allow for some to return properly
        WorkCategorizationFactory.create(owner_id=department.id, type='Department').save()

        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': department.id, 'activity': dept_wc.id},
                            post_data={}, pkey1='activities',
                            resource=Activity.query.filter(
                                Activity.type == 'Department', Activity.owner_id == department.id),
                            api_message=api_message, expectations=(DEPT_LEVEL_1_KEYS, DEPT_PER_ITEM_ATTRS))

    def test_get_div_dept_allocations_errors(self, testapp):
        url_to_test = 'activities.get_div_dept_activities_allocations'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        method = 'GET'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
                           (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id),
                           (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))

    def test_get_div_dept_allocations(self, testapp):
        # get the rules for activities
        url_to_test = 'activities.get_div_dept_activities_allocations'
        # ============================================================================================================ #
        test_name = 'get_single'
        ee_wc, dept_wc, client_wc, ee_alcs, dept_alcs, client_alcs = _create_employee_department_client_with_activities(
            add_allocations=1)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity':
                                ee_wc.id}, pkey1='allocations', resource=ee_alcs, api_message='Success',
                            expectations=(DEPT_ACTIVITY_LEVEL_1_KEYS, DEPT_ALLOCATION_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity':
                                dept_wc.id}, pkey1='allocations', resource=dept_alcs, api_message='Success',
                            expectations=(DEPT_ACTIVITY_LEVEL_1_KEYS, DEPT_ALLOCATION_ATTRS))

        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity':
                                client_wc.id}, pkey1='allocations', resource=client_alcs, api_message='Success',
                            expectations=(DEPT_ACTIVITY_LEVEL_1_KEYS, DEPT_ALLOCATION_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many'
        ee_alcs += [Allocation(ee_wc, fake.word(), fake.word()).save()]
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity':
                                ee_wc.id}, pkey1='allocations', resource=ee_alcs, api_message='Success',
                            expectations=(DEPT_ACTIVITY_LEVEL_1_KEYS, DEPT_ALLOCATION_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_allocations_from_all_activities'
        ee_wc2 = WorkCategorizationFactory.create(type='Employee', owner_id=ee_wc.owner.id).save()
        for i in range(randint(1, 10)):
            ee_alcs += [Allocation(choice([ee_wc, ee_wc2]), fake.word()*randint(1,4), fake.word() + '|' + fake.word()).save()]
        _expected_successes(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity':
                                'all'}, pkey1='activities',resource=[ee_wc, ee_wc2],
                            api_message='Success', expectations=(DEPT_LEVEL_1_KEYS, DEPT_ACTIVTIES_ALLOCATIONS_ATTRS))

    def test_create_div_dept_allocations_errors(self, testapp):
        url_to_test = 'activities.post_create_department_activity_allocation'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(None, None),
                         url_param_values={'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id},
                         post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.id},
                         post_data={})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.id},
                         post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={})
        # an employee activity I do not own
        dept_boss = UserFactory.create(client=client, department=dept_wc.owner).save().profile.save()
        employee2 = UserFactory.create(client=client, department=dept_wc.owner).save().profile.save()
        employee2.parent_id = dept_boss.id  # make them an employee
        employee2.user.set_password('secret_pwd')
        employee2.save()
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                         user_password_tuple=(employee2.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_with_bad_post_data'
        resource_name = json.dumps({'allocation': {'name': '<allocation_name>', 'rule': '<string|regex>'}})
        post_data = {'name': fake.sentence(), 'rule': fake.time()}
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division, boss)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), post_data=post_data, resource_name=resource_name,
                         url_param_values={'division': division.id, 'department': department.id, 'activity': ee_wc.id})
        post_data = lambda bad: {'allocation': bad}
        for bad in ({'rule': fake.word()}, {'name': fake.word()},  # just one or the other keys are valid
                    {'rul': fake.word(), 'name': fake.word()}, # mispellings
                    {'rule': fake.word(), 'nam': fake.word()},
                    {'Rule': fake.word(), 'name': fake.word()}): # bad case
            _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test,
                             user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), post_data=post_data(bad),
                             resource_name=resource_name, url_param_values={'division': division.id, 'department':
                    department.id, 'activity': ee_wc.id})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_with_bad_regex'
        regex_rule = '(?44)bob|frank'
        resource_name = 'the rule "{}" is not a valid Regular Expression'.format(regex_rule)
        _expected_errors(testapp, test_name=test_name, method='POST', url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), post_data=post_data({'rule': regex_rule, 'name': fake.word()}),
                         resource_name=resource_name, url_param_values={'division': division.id, 'department':
                department.id, 'activity': ee_wc.id})

    def test_create_div_dept_allocations(self, testapp):
        url_to_test = 'activities.post_create_department_activity_allocation'
        # ============================================================================================================ #
        test_name = 'post_create_allocation'
        method = 'POST'
        post_data = lambda name, rule, extras={}: {
            'allocation': {
                'rule': rule,
                'name': name,
                **extras
        }}

        # tests setup
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        employee = ee_wc.owner
        employee.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, division)

        name = fake.sentence()
        rule = fake.word()
        resource = [Allocation.query.filter(Allocation.name == name)]
        expectations = (DEPT_ACTIVITY_LEVEL_1_KEYS, DEPT_ALLOCATION_ATTRS)
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(employee.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': ee_wc.id},
                            post_data=post_data(name, rule), pkey1='allocations', api_message='Allocation created',
                            resource=resource, expectations=expectations)
        # make a second one - no difference from above
        name2 = fake.sentence()
        resource += [Allocation.query.filter(Allocation.name == name2)]
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test, api_message=
        'Allocation created', user_password_tuple=(boss.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': ee_wc.id},
                            post_data=post_data(name2, rule), pkey1='allocations', resource=resource,
                            expectations=expectations)
        assert Allocation.query.filter(Allocation.name == name).one().workcategorization == ee_wc
        assert Allocation.query.filter(Allocation.name == name2).one().activity == ee_wc
        # finally make a 3rd from the VP
        name3 = fake.sentence()
        resource += [Allocation.query.filter(Allocation.name == name3)]
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': ee_wc.id},
                            post_data=post_data(name3, rule), pkey1='allocations', resource=resource,
                            api_message='Allocation created', expectations=expectations)
        assert Allocation.query.filter(Allocation.name == name3).one().activity == ee_wc

        # boss can create allocations for their own department
        dept_allocation_name = fake.sentence()
        resource = [Allocation.query.filter(Allocation.name == dept_allocation_name)]
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(boss.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': dept_wc.id},
                            post_data=post_data(dept_allocation_name, rule), pkey1='allocations', resource=resource,
                            api_message='Allocation created', expectations=expectations)
        dept_allocation_name2 = fake.sentence()
        resource = [Allocation.query.filter(Allocation.name == dept_allocation_name2)]
        # vp can also create for his subordinate departments
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': dept_wc.id},
                            post_data=post_data(dept_allocation_name2, rule), pkey1='allocations', resource=resource,
                            api_message='Allocation created', expectations=expectations)
        division_allocation_name = fake.sentence()
        resource = [Allocation.query.filter(Allocation.name == division_allocation_name)]
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        # vp is the only one that can create for their own division
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': div_wc.id},
                            post_data=post_data(division_allocation_name, rule), pkey1='allocations', resource=resource,
                            api_message='Allocation created', expectations=expectations)

    def test_patch_div_dept_activity_errors(self, testapp):
        url_to_test = 'activities.patch_change_department_activity'
        method = 'PATCH'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None),
                         url_param_values={'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id},
                         post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.id},
                         post_data={})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.id},
                         post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={})
        # an employee activity I do not own
        dept_boss = UserFactory.create(client=client, department=dept_wc.owner).save().profile.save()
        employee2 = UserFactory.create(client=client, department=dept_wc.owner).save().profile.save()
        employee2.parent_id = dept_boss.id  # make them an employee
        employee2.user.set_password('secret_pwd')
        employee2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee2.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_with_bad_post_data'
        resource_name = json.dumps({'activity': {
                'assigned_time': '<int> <-- OPTIONAL',
                'assigned_percent': '<int> <-- OPTIONAL',
                'my_focus': '<bool> <-- OPTIONAL',
                'assignee': '<employee_ID>|all|None <-- OPTIONAL',
                'all_employees': '<bool> <-- OPTIONAL',
            }})
        post_data = {'my_focus': fake.boolean()}

        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test, user_password_tuple=
        (ee_wc.owner.email, 'secret_pwd'), url_param_values={'division': division.id, 'department': department.id,
                                                             'activity': ee_wc.id},
                         post_data=post_data, resource_name=resource_name)

        post_data = lambda bad: {'activity': {**bad}}

        for usr, bad in [
            (ee_wc.owner.email, {'rulename': fake.time()}),
            (boss.email, {'assignee': 'all', 'type': 'Employee'}),  # can't have 'type'
            (boss.email, {'assignee': 'all', 'owner': 'me'}),  # can't have owner
            ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test, user_password_tuple=
            (usr, 'secret_pwd'), post_data=post_data(bad), resource_name=resource_name, url_param_values=
            {'division': division.id, 'department': department.id, 'activity': ee_wc.id})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_insufficient_access'
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, extra in [(ee_wc.owner.email, {'assignee': 'all'}), (ee_wc.owner.email, {'assignee': 66}),  #  not me
                           (ee_wc.owner.email, {'all_employees': True}),
                           (boss.email, {'assignee': other_dept_ee.uuid}),  #  employee in another dept
                           ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test, user_password_tuple=
            (usr, 'secret_pwd'), post_data=post_data(extra), resource_name=resource_name, url_param_values=
            {'division': division.id, 'department': department.id, 'activity': ee_wc.id})
        # ============================================================================================================ #
        test_name = 'post_resource_for_div_or_dept_bad_post_data'
        for usr, ex, rs, act in [# bad combinations of post keys
                           (boss.email, {'assignee': 'all', 'all_employees': False},
                            "'assignee' = 'all' WITH 'all_employee' = false", dept_wc),
                           (boss.email, {'assignee': ee_wc.owner.uuid, 'all_employees': True},
                            "'assignee' = '{}' WITH 'all_employees' = true".format(ee_wc.owner.uuid), dept_wc),
                            ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), post_data=post_data(ex), resource_name=rs,
                             url_param_values={'division': division.id, 'department': department.id, 'activity': act})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
                           (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id),
                           (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), post_data=post_data({'assignee': 'all'}),
                             url_param_values={'division': division.id, 'department': department.id, 'activity': actvt})

    def test_patch_div_dept_activity(self, testapp):
        # similar to POST
        url_to_test = 'activities.patch_change_department_activity'
        work_week_hours = 40
        post_data = lambda updates: {'activity': {**updates}}
        method = 'PATCH'
        expectations = (DEPT_LEVEL_1_KEYS, EMPLOYEE_ACTIVITY_TARGET_ATTRS)
        # ============================================================================================================ #
        test_name = 'patch_update_activity'

        # tests setup
        ee_wc, dept_wc, _ = _create_employee_department_client_with_activities(make_client_wc=False)
        # assigned_time == 0, assigned_percent == 0.0, my_focus == False and all_employees == False
        employee = ee_wc.owner
        department, division = _create_division_atop_department(employee.client, employee.department)
        boss = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, department, employee)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(employee.client, division)
        employee.parent_id = boss.id
        employee.save()
        employee.user.set_password('secret_pwd')
        boss.user.set_password('secret_pwd')
        vp.user.set_password('secret_pwd')
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()

        resource = lambda wc: Activity.query.filter_by(id=wc.id)

        # EE updates their own, or BOSS / VP updates the EE's wc
        ee_assigned_time = 120
        ee_assigned_percent = 5.0
        ee_my_focus = True
        for email in (employee.email, boss.email, vp.email):
            for updt in ({'assigned_time': ee_assigned_time}, {'assigned_percent': ee_assigned_percent},
                         {'my_focus': ee_my_focus}):
                _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                    user_password_tuple=(email, 'secret_pwd'), url_param_values=
                                    {'division': division.id, 'department': department.id, 'activity': ee_wc.id},
                                    post_data=post_data(updt), pkey1='employees', api_message='Activity updated',
                                    resource=resource(ee_wc), expectations=expectations)
                for k,v in updt.items():
                    if k in ('assigned_time', 'assigned_percent'):
                        assert ee_wc.assigned_time == ee_assigned_time
                        assert ee_wc.assigned_percent == ee_assigned_percent
                        ee_wc.assigned_time = 0
                        ee_wc.assigned_percent = 0.0
                    else:
                        assert ee_wc.my_focus == ee_my_focus
                        ee_wc.my_focus = False
                # reset what we've done...
                ee_wc.save()

        # BOSS updates DEPT's
        employee2 = UserFactory.create(client=employee.client, department=employee.department).save().profile
        employee2.parent_id = boss.id
        employee2.save()

        # set this to true or we end up with no one in the 'employees' part of the payload
        dept_wc.all_employees = True

        for email in (boss.email, vp.email):
            for updt in ({'assigned_time': ee_assigned_time}, {'assigned_percent': ee_assigned_percent},
                         {'my_focus': ee_my_focus}, {'assignee': 'None'}, {'assignee': 'all'},
                         {'assignee': 'None'}, {'assignee': employee.user.uuid}, # put these two in sequence to make it work
                         {'all_employees': False}, {'all_employees': True}
                         ):
                _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                    user_password_tuple=(email, 'secret_pwd'), url_param_values=
                                    {'division': division.id, 'department': department.id, 'activity': dept_wc.id},
                                    post_data=post_data(updt), pkey1='employees', api_message='Activity updated',
                                    resource=resource(dept_wc), expectations=expectations)
                for k,v in updt.items():
                    if k in ('assigned_time', 'assigned_percent'):
                        assert dept_wc.assigned_time == ee_assigned_time
                        assert dept_wc.assigned_percent == ee_assigned_percent
                        dept_wc.assigned_time = 0
                        dept_wc.assigned_percent = 0.0
                    elif k == 'assignee':
                        if v == 'None':
                            all_ees, staff = False, []
                        elif v == 'all':
                            all_ees, staff = True, [employee, employee2]
                        else:
                            from kunin.user.models import User
                            all_ees, staff = False, [User.get_by_uuid(v).profile]
                        assert dept_wc.all_employees == all_ees
                        assert dept_wc.employees() == staff
                    elif k == 'all_employees':
                        assert dept_wc.all_employees == v
                        if v:
                            assert dept_wc.employees() == [employee, employee2]
                        else:
                            assert dept_wc.employees() == [employee]
                    else:
                        assert dept_wc.my_focus == ee_my_focus
                        dept_wc.my_focus = False
                # reset what we've done...
                dept_wc.save()

        # VP updates DIV's
        employee3 = UserFactory.create(client=vp.client, department=vp.department).save().profile
        employee3.parent_id = vp.id
        employee3.save()
        employee4 = UserFactory.create(client=vp.client, department=vp.department).save().profile
        employee4.parent_id = vp.id
        employee4.save()

        for updt in ({'assigned_time': ee_assigned_time}, {'assigned_percent': ee_assigned_percent},
                     {'my_focus': ee_my_focus}, {'assignee': 'None'}, {'assignee': 'all'},
                     {'assignee': 'None'}, {'assignee': employee4.user.uuid},
                     # put these two in sequence to make it work
                     {'all_employees': False}, {'all_employees': True}
                     ):
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                                {'division': division.id, 'department': department.id, 'activity': div_wc.id},
                                post_data=post_data(updt), pkey1='employees', api_message='Activity updated',
                                resource=resource(div_wc), expectations=expectations)
            for k, v in updt.items():
                if k in ('assigned_time', 'assigned_percent'):
                    assert div_wc.assigned_time == ee_assigned_time
                    assert div_wc.assigned_percent == ee_assigned_percent
                    div_wc.assigned_time = 0
                    div_wc.assigned_percent = 0.0
                elif k == 'assignee':
                    if v == 'None':
                        all_ees, staff = False, []
                    elif v == 'all':
                        all_ees, staff = True, [employee3, employee4]
                    else:
                        from kunin.user.models import User
                        all_ees, staff = False, [User.get_by_uuid(v).profile]
                    assert div_wc.all_employees == all_ees
                    assert div_wc.employees() == staff
                elif k == 'all_employees':
                    assert div_wc.all_employees == v
                    if v:
                        assert div_wc.employees() == [employee3, employee4]
                    else:
                        assert div_wc.employees() == [employee4]
                else:
                    assert div_wc.my_focus == ee_my_focus
                    div_wc.my_focus = False
            # reset what we've done...
            div_wc.save()

    def test_get_div_focus_errors(self, testapp):
        url_to_test = 'activities.get_div_dept_activities_myfocus'
        method = 'GET'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
                           (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id),
                           (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))

    def test_get_div_focus(self, testapp):
        # get what we're focusing on (in activities)
        url_to_test = 'activities.get_div_dept_activities_myfocus'
        method = 'GET'
        expectations = (DEPT_LEVEL_1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS)
        # ============================================================================================================ #
        test_name = 'get_single'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities(add_focus=True)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)

        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        div_focus = []
        for i in range(1,3):
            div_focus += [WorkCategorizationFactory.create(type='Department', owner_id=division.id,
                                                           my_focus=True).save()]

        for actv in [(ee_wc, ee_wc.owner), (ee_wc, boss), (ee_wc, vp),
                     (dept_wc, boss), (dept_wc, vp),
                     (client_wc, ee_wc.owner), (client_wc, boss), (client_wc, vp),
                     (choice(div_focus), vp)
                     ]:
            extras = {'achieved_time': 120, 'target_time': 0}
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(actv[1].email, 'secret_pwd'), attrs_extras=extras,
                                url_param_values={'division': division.id, 'department': department.id, 'activity':
                                    actv[0].id}, pkey1='my_focus', resource=actv[0], api_message='Success',
                                expectations=expectations)
        # ============================================================================================================ #
        test_name = 'get_focus_from_all_activities'
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'),
                            url_param_values={'division': division.id, 'department': department.id, 'activity': 'all'},
                            pkey1='my_focus',resource=div_focus, api_message='Success', expectations=expectations)
        # ============================================================================================================ #
        test_name = 'get_focus_from_all_departments'
        expectations = (DIV_LEVEL_1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS)
        for dept in ({'department': 'all'}, {}):
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(vp.email, 'secret_pwd'), api_message='Success',
                                url_param_values={**{'division': division.id}, **dept},
                                pkey1='my_focus',resource=div_focus + [dept_wc], expectations=expectations)

    def test_put_div_focus_errors(self, testapp):
        url_to_test = 'activities.put_div_dept_activities_myfocus'
        method = 'PUT'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
                           (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id),
                           (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))

    def test_put_div_focus(self, testapp):
        # set what we're focusing on (in activities)
        url_to_test = 'activities.put_div_dept_activities_myfocus'
        method = 'PUT'
        expectations = (DEPT_LEVEL_1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS)
        # ============================================================================================================ #
        test_name = 'put_focus'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)

        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        div_wcs = []
        for i in range(1,3):
            div_wcs += [WorkCategorizationFactory.create(type='Department', owner_id=division.id).save()]

        for actv in [(ee_wc, ee_wc.owner), (ee_wc, boss), (ee_wc, vp),
                     (dept_wc, boss), (dept_wc, vp),
                     (client_wc, ee_wc.owner), (client_wc, boss), (client_wc, vp),
                     (choice(div_wcs), vp)
                     ]:
            extras = {'achieved_time': 120, 'target_time': 0}
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(actv[1].email, 'secret_pwd'), attrs_extras=extras,
                                url_param_values={'division': division.id, 'department': department.id, 'activity':
                                    actv[0].id}, pkey1='my_focus', resource=actv[0], api_message='Success',
                                expectations=expectations)
            assert actv[0].my_focus == True
            assert actv[0].all_employees == (True if actv[0].type != 'Employee' else False)
            # reset them
            actv[0].my_focus = False
            actv[0].all_employees = False
        # test setting focus at the division level
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), api_message='Success', url_param_values=
                            {'division': division.id, 'activity': div_wcs[0].uuid}, pkey1='my_focus',
                            resource=div_wcs[0], expectations=(DIV_LEVEL_1_KEYS, MINIMAL_DEPT_ACTIVITY_AGGREGATE_ATTRS))
        # check if many show up when we already have focused wcs
        div_wcs[0].my_focus = True
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'department': department.id, 'activity': div_wcs[1].uuid},
                            pkey1='my_focus', resource=div_wcs[:-1], api_message='Success', expectations=expectations)

    def test_get_div_dept_activities_notes_errors(self, testapp):
        url_to_test = 'activities.get_div_dept_activities_notes'
        method = 'GET'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
                           (boss.email, dept3_wc.id),
                           # employee from another department altogether
                           (other_dept_ee.email, dept_wc.id),
                           (other_dept_ee.email, dept3_wc.id),
                           ]:

            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))

    def test_get_div_dept_activities_notes(self, testapp):
        # see the dialogue that happens (in activities)
        url_to_test = 'activities.get_div_dept_activities_notes'
        method = 'GET'
        expectations = (DEPT_LEVEL_1_KEYS, ACTIVITY_NOTE_ATTRS)
        # ============================================================================================================ #
        test_name = 'get_single'
        ee_wc, d_wc, c_wc, ee_notes, d_notes, c_notes = _create_employee_department_client_with_activities(
            make_dept_wc=True, make_client_wc=True, all_employees=True, notes=3)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)

        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        div_wcs, div_notes = [], []
        for i in range(1,2):
            div_wcs += [WorkCategorizationFactory.create(
                type='Department', owner_id=division.id, all_employees=True).save()]
            for j in range(1,3):
                div_notes += [Note(fake.sentence(), vp, div_wcs[-1]).save()]

        for actv in [(ee_wc, ee_wc.owner),
                     (ee_wc, boss), (ee_wc, vp),
                     (d_wc, boss), (d_wc, vp),
                     (c_wc, ee_wc.owner),
                     (c_wc, boss), (c_wc, vp),
                     (choice(div_wcs), vp)
                     ]:
            _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                user_password_tuple=(actv[1].email, 'secret_pwd'),
                                url_param_values={'division': division.id, 'department': department.id, 'activity':
                                    actv[0].id}, pkey1='notes', resource=actv[0].notes, api_message='Success',
                                expectations=expectations)
        # add one more that we will use for replies later
        note_with_replies = WorkCategorizationFactory.create(type='Department', owner_id=division.id,
                                                             all_employees=True).save()
        div_wcs += [note_with_replies]
        # test a note at the division level
        employee2 = UserFactory.create(department=division, client=vp.client).save().profile
        employee2.parent_id=vp.id
        employee2.save()
        div_ee_note = Note(fake.sentence(), employee2, note_with_replies).save()
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), api_message='Success', url_param_values=
                            {'division': division.id, 'activity': note_with_replies.uuid}, pkey1='notes',
                            resource=note_with_replies.notes, expectations=(DIV_LEVEL_1_KEYS, ACTIVITY_NOTE_ATTRS))
        # now to reply to something...
        div_ee_note.reply_from(vp, fake.sentence())
        extras = {'reply': [activity_notes_schema.dump(div_ee_note.replies)['notes'][0]][0]}
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test, attrs_extras=extras,
                            user_password_tuple=(vp.email, 'secret_pwd'), resource=note_with_replies.notes,
                            url_param_values={'division': division.id, 'department': department.id,
                                              'activity': note_with_replies.id}, pkey1='notes', api_message='Success',
                            expectations=(DIV_LEVEL_1_KEYS, ACTIVITY_NOTE_ATTRS))
        # ============================================================================================================ #
        test_name = 'get_many'
        # give each division wc a bunch of notes
        div_employees = [employee2]
        for i in range(2,5):
            employee = UserFactory.create(department=division, client=vp.client).save().profile
            employee.parent_id=vp.id
            div_employees += [employee.save()]
        [Note(fake.sentence(), employee2, wc).save() for i in range(2,5) for wc in div_wcs]
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(vp.email, 'secret_pwd'), url_param_values=
                            {'division': division.id, 'activity': 'all'}, resource=div_wcs,
                            pkey1='activities', api_message='Success', expectations=(DIV_LEVEL_1_KEYS,
                                                                                ACTIVITIES_ALL_WITH_NOTES_ATTRS))

    def test_get_user_notes_errors(self, testapp):
        url_to_test = 'activities.get_user_notes'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities(
            make_dept_wc=False, make_client_wc=False)
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={'user': ee_wc.owner.username}, post_data={})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'user': ee_wc.owner.username}, post_data={})
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'user': 'foobar'}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_bosses'
        boss_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        client = boss_wc.owner.client
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.save()
        employee.user.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': the_boss.user.id}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_non_reports'
        boss2 = UserFactory.create(client=client).save().profile
        employee2 = UserFactory.create(client=client).save().profile
        employee2.parent_id = boss2.id
        employee2.save()
        _expected_errors(testapp, test_name=test_name, method='GET', url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': employee2.user.id}, post_data={})

    def test_get_user_notes(self, testapp):
        url_to_test = 'activities.get_user_notes'
        method = 'GET'
        expectations = (USER_LEVEL_1_KEYS, ACTIVITIES_ALL_WITH_NOTES_ATTRS)
        # ============================================================================================================ #
        test_name = 'get_many'
        # just in a department
        ee_wc, d_wc, c_wc, ee_notes, d_notes, c_notes = _create_employee_department_client_with_activities(
            make_dept_wc=True, make_client_wc=True, all_employees=True, notes=3)
        ee_wc.owner.user.set_password('secret_pwd')
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, ee_wc.owner.department,
                                                                      ee_wc.owner)

        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), expectations=expectations,
                            url_param_values={'user': ee_wc.owner.username}, post_data={}, pkey1='activities',
                            resource=[ee_wc, d_wc, c_wc], api_message='Success')
        # ============================================================================================================ #
        # in a proper org
        expectations = (DEPT_LEVEL_1_KEYS, ACTIVITIES_ALL_WITH_NOTES_ATTRS)
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                            user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), expectations=expectations,
                            url_param_values={'user': ee_wc.owner.username}, post_data={}, pkey1='activities',
                            resource=[ee_wc, d_wc, c_wc], api_message='Success')

    def test_post_notes_errors(self, testapp):
        url_to_test = 'activities.post_activities_notes'
        method = 'POST'
        # ============================================================================================================ #
        test_name = 'not_logged_in'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        dept2 = DepartmentFactory.create(client=client_wc.owner)
        dept2.parent_id = dept_wc.owner.id
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(None, None), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'logged_in_different_client'
        resource_name = 'Division and Department'
        client2 = ClientFactory()
        diff_client_ee = UserFactory.create(client=client2).save()
        diff_client_ee.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'non_existing_resource'
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': 64, 'department': 14, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        dept2.parent_id = None
        dept2.client = client2
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(diff_client_ee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid},
                         resource_name=resource_name)
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_mine'
        client = client_wc.owner
        dept2.parent_id = dept_wc.owner.id
        dept2.client = client
        dept2.save()
        boss_wc, dept3_wc, client_wc2 = _create_employee_department_client_with_activities(client=client)
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.department = dept2
        employee.save()
        employee.user.set_password('secret_pwd')
        the_boss.user.set_password('secret_pwd')
        # a dept which is not in my tree
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept3_wc.owner.id, 'activity': ee_wc.uuid})
        # a dept which is upstream from me
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept_wc.owner.id, 'activity': ee_wc.uuid})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_not_managed_by_me'
        employee.department = dept_wc.owner
        employee.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'division': dept_wc.owner.id, 'department': dept2.id, 'activity': ee_wc.uuid})
        # # ============================================================================================================ #
        test_name = 'get_allocations_for_div_or_dept_insufficient_access'
        ee_wc, dept_wc, client_wc = _create_employee_department_client_with_activities()
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        div_wc = WorkCategorizationFactory.create(owner_id=division.id, type='Department').save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        other_dept_ee = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, dept2)
        for usr, actvt in [
            (boss.email, dept3_wc.id),
            # employee from another department altogether
            (other_dept_ee.email, dept_wc.id),
            (other_dept_ee.email, dept3_wc.id),
        ]:
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(usr, 'secret_pwd'), url_param_values={
                    'division': division.id, 'department': department.id, 'activity': actvt})
        # ============================================================================================================ #
        test_name = 'get_allocations_for_dept_not_owned_by_div'
        error_message = 'Division {} is not the parent of Department {}'
        dept2.client = division.client  # ensure dept2 has same client as division
        dept2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(boss.email, 'secret_pwd'), url_param_values={
                'division': division.id, 'department': dept2.id, 'activity': dept_wc.uuid},
                         resource_name=error_message.format(division.uuid, dept2.uuid))
        # ============================================================================================================ #
        test_name = 'get_resource_for_bosses'
        boss_wc, _, _ = _create_employee_department_client_with_activities(make_dept_wc=False, make_client_wc=False)
        client = boss_wc.owner.client
        the_boss = boss_wc.owner
        employee = UserFactory.create(client=client).save().profile
        employee.parent_id = the_boss.id
        employee.save()
        employee.user.set_password('secret_pwd')
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': the_boss.user.id, 'activity': boss_wc.uuid}, post_data={})
        # ============================================================================================================ #
        test_name = 'get_resource_for_non_reports'
        boss2 = UserFactory.create(client=client).save().profile
        employee2 = UserFactory.create(client=client).save().profile
        employee2.parent_id = boss2.id
        employee2.save()
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(employee.email, 'secret_pwd'), url_param_values={
                'user': employee2.user.id, 'activity': boss_wc.id}, post_data={})
        # ============================================================================================================ #
        # reply to a thread which already has a reply
        test_name = 'too_many_replies'
        post_data = lambda note={}: {'note': {**note}}
        error_message = 'this Note already has a reply and notes only support a single reply'
        ee_wc, d_wc, c_wc, ee_notes, d_notes, c_notes = _create_employee_department_client_with_activities(
            make_dept_wc=True, make_client_wc=True, all_employees=True, notes=3)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)

        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)

        replied_note = Note(fake.sentence(), ee_wc.owner, ee_wc).save()
        replied_note.reply_from(boss, fake.sentence())
        _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                         user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), url_param_values={
                'user': ee_wc.owner.user.id, 'activity': ee_wc.id}, resource_name=error_message,
                         post_data=post_data({'reply': fake.sentence(), 'note': replied_note.note}))
        # ============================================================================================================ #
        # reply to a thread which already has a reply
        test_name = 'post_notes_bad_post_data'
        error_message = json.dumps({'note': {'note': '<string>, AND WITH','reply': '<string>, (if it is a reply)'}})
        for p in ({}, {'data': None}, {'NOTE': {}}, post_data({'reply': fake.word()})):
            _expected_errors(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                             user_password_tuple=(ee_wc.owner.email, 'secret_pwd'), url_param_values={
                    'user': ee_wc.owner.user.id, 'activity': ee_wc.id}, resource_name=error_message, post_data=p)

    def test_post_notes(self, testapp):
        # add to the dialogue of notes
        url_to_test = 'activities.post_activities_notes'
        post_data = lambda note={}: {'note': {**note}}
        method = 'POST'
        expectations = (DEPT_LEVEL_1_KEYS, ACTIVITY_NOTE_ATTRS)
        param_values = lambda main, activity: {**main, 'activity': activity.id}
        # ============================================================================================================ #
        test_name = 'post_note'
        ee_wc, d_wc, c_wc = _create_employee_department_client_with_activities(make_dept_wc=True, make_client_wc=True,
                                                                               all_employees=True)
        ee_wc.owner.user.set_password('secret_pwd')
        department, division = _create_division_atop_department(ee_wc.owner.client, ee_wc.owner.department)
        division2 = DepartmentFactory.create(client=ee_wc.owner.client).save()
        boss = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, department, ee_wc.owner)
        vp = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division)
        vp2 = _create_ee_in_client_dept_with_password_possibly_staff(ee_wc.owner.client, division2)

        div_wcs, div_notes = [], []
        for i in range(1, 2):
            div_wcs += [WorkCategorizationFactory.create(
                type='Department', owner_id=division.id, all_employees=True).save()]
            for j in range(1, 3):
                div_notes += [Note(fake.sentence(), vp, div_wcs[-1]).save()]

        # can only be from the employee's boss or higher
        note_text = fake.sentence()
        for actv in [(ee_wc, ee_wc.owner, boss), # normal course of operations, employee note with boss reply
                     (ee_wc, boss, boss), # weird to do this, but just the boss leaving themself a note
                     (ee_wc, boss, vp), # boss note with VP reply
                     (ee_wc, vp, vp), # weird to do this, but just the VP leaving themself a note
                     (d_wc, boss, boss),
                     (d_wc, boss, vp),
                     (c_wc, ee_wc.owner, boss),
                     (c_wc, boss, vp),
                     (c_wc, vp, vp2),
                     (choice(div_wcs), vp, vp)
                     ]:
            for url_pvs in (param_values({'division': division.id, 'department': department.id}, actv[0]),
                            param_values({'user': actv[1].uuid}, actv[0]),
                            ):
                for rep in ({'note': note_text}, {'reply': fake.sentence(), 'note': note_text}):
                    initiator = actv[1].email if 'reply' not in rep else actv[2].email
                    _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                        user_password_tuple=(initiator, 'secret_pwd'),
                                        api_message='Note created' if 'reply' not in rep else 'Reply to note created',
                                        url_param_values=url_pvs, pkey1='notes', resource=actv[0].notes,
                                        expectations=expectations, post_data=post_data(rep))
                note_text = fake.sentence()

        expectations = (DIV_LEVEL_1_KEYS, ACTIVITY_NOTE_ATTRS)
        employee2 = UserFactory.create(client=ee_wc.owner.client, department=division).save().profile
        employee2.parent_id = vp.id
        employee2.save()

        for actv in [(d_wc, ee_wc.owner, vp),
                     (d_wc, boss, vp),
                     (d_wc, vp, vp),
                     ]:
            for url_pvs in (param_values({'division': division.id}, actv[0]),
                            param_values({'division': division.id, 'department': 'all'}, actv[0]),
                            ):
                for rep in ({'note': note_text}, {'reply': fake.sentence(), 'note': note_text}):
                    initiator = actv[1].email if 'reply' not in rep else actv[2].email
                    _expected_successes(testapp, test_name=test_name, method=method, url_to_test=url_to_test,
                                        user_password_tuple=(initiator, 'secret_pwd'),
                                        url_param_values=url_pvs, pkey1='notes', resource=actv[0].notes,
                                        api_message='Note created' if 'reply' not in rep else 'Reply to note created',
                                        expectations=expectations, post_data=post_data(rep))
                note_text = fake.sentence()
