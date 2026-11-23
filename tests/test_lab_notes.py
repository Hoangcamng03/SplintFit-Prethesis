import tempfile,unittest,subprocess,sys,shutil
from pathlib import Path
from tools.check_lab_notes import validate_changes
from tools.new_lab_note import create_note


class LabNoteTests(unittest.TestCase):
    def test_source_only_change_is_rejected(self):
        self.assertTrue(validate_changes(['app.py'],lambda _:''))
    def test_readme_is_not_a_dated_lab_note(self):
        self.assertTrue(validate_changes(['app.py','LAB_NOTES/README.md'],lambda _:''))
    def test_draft_note_is_rejected(self):
        self.assertTrue(validate_changes(['LAB_NOTES/LN-20261123-003_test.md'],lambda _:'status: draft'))
    def test_complete_record_with_sections_is_accepted(self):
        text='status: complete\n'+''.join('## '+s+'\nObserved record.\n' for s in ['Objective','Changes','Validation','Limitations','Next'])
        self.assertFalse(validate_changes(['app.py','LAB_NOTES/LN-20261123-003_test.md'],lambda _:text))
    def test_two_notes_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)/'LAB_NOTES';folder.mkdir()
            (folder/'TEMPLATE.md').write_text('{{ID}} {{TITLE}} {{DATE}}\nstatus: draft',encoding='utf-8')
            a=create_note(t,'same change');b=create_note(t,'same change')
            self.assertNotEqual(a,b);self.assertTrue(a.exists());self.assertTrue(b.exists())

    def test_staged_check_from_outside_repository_checks_its_own_project(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'repo';tools=root/'tools';tools.mkdir(parents=True)
            script=tools/'check_lab_notes.py'
            shutil.copyfile(Path(__file__).resolve().parents[1]/'tools/check_lab_notes.py',script)
            subprocess.run(['git','init','-b','main'],cwd=root,check=True,capture_output=True)
            (root/'app.py').write_text('print(1)',encoding='utf-8')
            subprocess.run(['git','add','.'],cwd=root,check=True)
            bad=subprocess.run([sys.executable,str(script),'--staged'],cwd=t,capture_output=True)
            self.assertEqual(bad.returncode,1)
            folder=root/'LAB_NOTES';folder.mkdir()
            note='status: complete\n'+''.join('## '+s+'\nRecorded.\n' for s in ['Objective','Changes','Validation','Limitations','Next'])
            (folder/'LN-20261123-003_fixture.md').write_text(note,encoding='utf-8')
            subprocess.run(['git','add','.'],cwd=root,check=True)
            good=subprocess.run([sys.executable,str(script),'--staged'],cwd=t,capture_output=True)
            self.assertEqual(good.returncode,0,good.stderr.decode())


if __name__=='__main__':unittest.main()
