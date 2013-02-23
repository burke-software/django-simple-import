from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.client import Client
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User

class SimpleTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.c = Client()
        self.c.login(username='temporary', password='temporary')
        
    def test_import(self):
        """ Make sure we can upload the file and match columns """
        import_log_ct_id = ContentType.objects.get(name="import log", app_label="simple_import").id
        
        absolute_path = finders.find('test_import.xls')

        with open(absolute_path) as fp:
            response = self.c.post('/simple_import/start_import/', {
                'name': 'This is a test',
                'import_file': fp,
                'import_type': "N",
                'model': import_log_ct_id}, follow=True)
        self.assertContains(response, '<h1>Match columns</h1>')
        # Check matching
        self.assertContains(response, '<option value="name" selected="selected">')
        self.assertContains(response, '<option value="user" selected="selected">')
        self.assertContains(response, '<option value="import_file" selected="selected">')
        self.assertContains(response, '<option value="import_settings" selected="selected">')
        # Check Sample Data
        self.assertContains(response, '/tmp/foo.xls')