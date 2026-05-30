{
    'name': 'QA Bug Management',
    'version': '18.0.3.0.0',
    'category': 'Quality',
    'summary': 'Automated QA bug ticket management with CI/CD integration',
    'depends': ['base', 'mail'],
    'data': [
        'security/qa_bug_security.xml',
        'security/ir.model.access.csv',
        'data/qa_bug_sequence.xml',
        'data/qa_field_options.xml',
        'views/qa_bug_ticket_views.xml',
        'views/qa_field_option_views.xml',
        'views/qa_report_views.xml',
        'views/qa_evidence_upload_wizard_views.xml',
        'views/res_users_views.xml',
        'views/qa_bug_ticket_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'qa_bug_management/static/src/css/evidence_gallery.css',
            'qa_bug_management/static/src/js/evidence_lightbox.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
