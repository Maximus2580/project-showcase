"""Filesystem installer checks; package installation is mocked here."""
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('install_global',ROOT/'scripts/install_global.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class InstallTests(unittest.TestCase):
    def test_global_install_preserves_existing_and_backs_up_explicit_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder)
            with patch.object(installer.Path,'home',return_value=home), patch.object(installer.venv.EnvBuilder,'create'), patch.object(installer.subprocess,'run') as run, patch.object(installer.shutil,'which',return_value='/usr/bin/npm'), redirect_stdout(io.StringIO()):
                with patch('sys.argv',['install_global.py']):installer.main()
                dest=home/'.agents/skills/project-showcase'
                skill=dest/'SKILL.md'
                self.assertIn('name: project-showcase',skill.read_text())
                self.assertIn('Prepared global runtime',skill.read_text())
                self.assertEqual((home/'.claude/skills/project-showcase').resolve(),dest.resolve())
                self.assertTrue((home/'.local/share/project-showcase/install-manifest.json').is_file())
                self.assertEqual(run.call_count,2)
                skill.write_text('user change')
                with patch('sys.argv',['install_global.py']):
                    with self.assertRaisesRegex(SystemExit,'Existing install preserved'):installer.main()
                self.assertEqual(skill.read_text(),'user change')
                with patch('sys.argv',['install_global.py','--replace']):installer.main()
                backups=list((home/'.local/share/project-showcase/backups').glob('*/0-project-showcase/SKILL.md'))
                self.assertEqual(len(backups),1)
                self.assertEqual(backups[0].read_text(),'user change')
                self.assertIn('name: project-showcase',skill.read_text())

if __name__=='__main__':unittest.main()
