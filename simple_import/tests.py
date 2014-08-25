import os

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from simple_import.compat import User
from simple_import.models import *
from django.core.files import File

class SimpleTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.client.login(username='temporary', password='temporary')
        self.absolute_path = os.path.join(os.path.dirname(__file__), 'static', 'test_import.xls')
        self.import_setting = ImportSetting.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(ImportLog)
        )
        with open(self.absolute_path) as fp:
            self.import_log = ImportLog.objects.create(
                name=u'test',
                user=user,
                import_file = File(fp),
                import_setting = self.import_setting,
                import_type = u'N',
            )

    def test_import(self):
        """ Make sure we can upload the file and match columns """
        import_log_ct_id = ContentType.objects.get_for_model(ImportLog).id

        self.assertEqual(ImportLog.objects.count(), 1)

        with open(self.absolute_path) as fp:
            response = self.client.post(reverse('simple_import-start_import'), {
                'name': 'This is a test',
                'import_file': fp,
                'import_type': "N",
                'model': import_log_ct_id}, follow=True)

        self.assertEqual(ImportLog.objects.count(), 2)

        self.assertRedirects(response, reverse('simple_import-match_columns', kwargs={'import_log_id': ImportLog.objects.all()[1].id}))
        self.assertContains(response, '<h1>Match Columns</h1>')
        # Check matching
        self.assertContains(response, '<option value="name" selected="selected">')
        self.assertContains(response, '<option value="user" selected="selected">')
        self.assertContains(response, '<option value="import_file" selected="selected">')
        self.assertContains(response, '<option value="import_setting">import setting (Required) (Related)</option>')
        # Check Sample Data
        self.assertContains(response, '/tmp/foo.xls')

    def test_match_columns(self):
        """ Test matching columns view  """
        self.assertEqual(ColumnMatch.objects.count(), 0)

        response = self.client.post(
            reverse('simple_import-match_columns', kwargs={'import_log_id': self.import_log.id}), {
            'columnmatch_set-TOTAL_FORMS':6,
            'columnmatch_set-INITIAL_FORMS':6,
            'columnmatch_set-MAX_NUM_FORMS':1000,
            'columnmatch_set-0-id':1,
            'columnmatch_set-0-column_name':'name',
            'columnmatch_set-0-import_setting':self.import_setting.id,
            'columnmatch_set-0-field_name':'name',
            'columnmatch_set-1-id':2,
            'columnmatch_set-1-column_name':'UseR',
            'columnmatch_set-1-import_setting':self.import_setting.id,
            'columnmatch_set-1-field_name':'user',
            'columnmatch_set-2-id':3,
            'columnmatch_set-2-column_name':'nothing',
            'columnmatch_set-2-import_setting':self.import_setting.id,
            'columnmatch_set-2-field_name':'',
            'columnmatch_set-3-id':4,
            'columnmatch_set-3-column_name':'import file',
            'columnmatch_set-3-import_setting':self.import_setting.id,
            'columnmatch_set-3-field_name':'import_file',
            'columnmatch_set-4-id':5,
            'columnmatch_set-4-column_name':'import_setting',
            'columnmatch_set-4-import_setting':self.import_setting.id,
            'columnmatch_set-4-field_name':'import_setting',
            'columnmatch_set-5-id':6,
            'columnmatch_set-5-column_name':'importtype',
            'columnmatch_set-5-import_setting':self.import_setting.id,
            'columnmatch_set-5-field_name':'import_type',
        }, follow=True)

        self.assertRedirects(response, reverse('simple_import-match_relations', kwargs={'import_log_id': self.import_log.id}))
        self.assertContains(response, '<h1>Match Relations and Prepare to Run Import</h1>')
        self.assertEqual(ColumnMatch.objects.count(), 6)

    def test_match_relations(self):
        """ Test matching relations view  """
        self.assertEqual(RelationalMatch.objects.count(), 0)

        response = self.client.post(
            reverse('simple_import-match_relations', kwargs={'import_log_id': self.import_log.id}), {
            'relationalmatch_set-TOTAL_FORMS':2,
            'relationalmatch_set-INITIAL_FORMS':2,
            'relationalmatch_set-MAX_NUM_FORMS':1000,
            'relationalmatch_set-0-id':1,
            'relationalmatch_set-0-import_log':self.import_log.id,
            'relationalmatch_set-0-field_name':'user',
            'relationalmatch_set-0-related_field_name':'id',
            'relationalmatch_set-1-id':2,
            'relationalmatch_set-1-import_log':self.import_log.id,
            'relationalmatch_set-1-field_name':'import_setting',
            'relationalmatch_set-1-related_field_name':'id',
        }, follow=True)

        self.assertRedirects(response, reverse('simple_import-do_import', kwargs={'import_log_id': self.import_log.id}))
        self.assertContains(response, '<h1>Import Results</h1>')

        self.assertEqual(RelationalMatch.objects.count(), 2)

