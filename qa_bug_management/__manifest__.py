{
    'name': 'QA Bug Management',
    'version': '18.0.1.0.0',
    'category': 'Quality',
    'summary': 'Automated QA bug ticket management with CI/CD integration',
    'depends': ['base', 'mail'],
    'data': [
        'security/qa_bug_security.xml',
        'security/ir.model.access.csv',
        'data/qa_bug_sequence.xml',
        'views/qa_bug_ticket_views.xml',
        'views/qa_bug_ticket_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
