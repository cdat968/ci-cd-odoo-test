{
    'name': 'QA Helpdesk Bridge',
    'version': '18.0.1.0.0',
    'category': 'Quality',
    'summary': 'Manual bridge between OCA Helpdesk tickets and QA bug tickets',
    'depends': [
        'qa_bug_management',
        'helpdesk_mgmt',
        'helpdesk_mgmt_project',
        'project',
    ],
    'data': [
        'views/helpdesk_ticket_views.xml',
        'views/qa_bug_ticket_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
