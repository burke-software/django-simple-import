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
        
    def test_start_import(self):
        """ Make sure match guessing works """
        c = Client()
        c.login(username='temporary', password='temporary')
        import_log_ct_id = ContentType.objects.get(name="import log", app_label="simple_import").id
        
        absolute_path = finders.find('test_import.xls')

        with open(absolute_path) as fp:
            response = c.post('/simple_import/start_import/', {
                'name': 'This is a test',
                'import_file': fp,
                'import_type': "N",
                'model': import_log_ct_id}, follow=True)
        self.assertContains(response, '<h1>Match columns</h1>')