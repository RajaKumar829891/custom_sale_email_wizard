{
    'name': 'Custom Sale Email Wizard with Contact Selection',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Customize sales quotation email wizard to select contacts',
    'description': '''
        This module customizes the "Send by Email" wizard for sales quotations
        to show contact selection interface instead of simple email form.
        Users can select multiple contacts and emails are populated automatically.
    ''',
    'author': 'Raja Kumar',
    'depends': ['sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_contact_email_wizard_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}