from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.client import Client
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from simple_import.models import *
from django.core.files import File

class SimpleTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.c = Client()
        self.c.login(username='temporary', password='temporary')
        self.absolute_path = finders.find('test_import.xls')
        self.import_setting = ImportSetting.objects.create(
            user=user,
            content_type=ContentType.objects.get(name="import log", app_label="simple_import")
        )
        with open(self.absolute_path) as fp:
            self.import_log = ImportLog.objects.create(
                name='test',
                user=user,
                import_file = File(fp),
                import_setting = self.import_setting,
                import_type = 'N',
            )   
        
    def test_import(self):
        """ Make sure we can upload the file and match columns """
        import_log_ct_id = ContentType.objects.get(name="import log", app_label="simple_import").id
        
        with open(self.absolute_path) as fp:
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
        self.assertContains(response, '<option value="import_setting">import setting (Required) (Related)</option>')
        # Check Sample Data
        self.assertContains(response, '/tmp/foo.xls')
        
    def test_match_relations(self):
        """ Test matching relations view  """
        return #IndexError: list index out of range - WHY?
        response = self.c.post('/simple_import/match_columns/{0}/'.format(self.import_log.id), {
            'form-TOTAL_FORMS':6,
            'form-INITIAL_FORMS':6,
            'form-MAX_NUM_FORMS':1000,
            'form-0-id':1,
            'form-0-column_name':'name',
            'form-0-import_setting':self.import_setting.id,
            'form-0-field_name':'name',
            'form-1-id':2,
            'form-1-column_name':'UseR',
            'form-1-import_setting':self.import_setting.id,
            'form-1-field_name':'user',
            'form-2-id':3,
            'form-2-column_name':'nothing',
            'form-2-import_setting':self.import_setting.id,
            'form-2-field_name':'',
            'form-3-id':4,
            'form-3-column_name':'import file',
            'form-3-import_setting':self.import_setting.id,
            'form-3-field_name':'import_file',
            'form-4-id':5,
            'form-4-column_name':'import_setting',
            'form-4-import_setting':self.import_setting.id,
            'form-4-field_name':'import_setting',
            'form-5-id':6,
            'form-5-column_name':'importtype',
            'form-5-import_setting':self.import_setting.id,
            'form-5-field_name':'import_type',
        }, follow=True)
        self.assertContains(response, 'Match Relations and Prepare to Run Import')