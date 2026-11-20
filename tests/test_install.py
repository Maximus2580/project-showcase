"""Filesystem installer checks; package installation is mocked here."""
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import tempfile
import subprocess
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

    def test_dependency_failure_keeps_the_existing_install_active(self):
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder)
            with patch.object(installer.Path,'home',return_value=home),patch.object(installer.venv.EnvBuilder,'create'),patch.object(installer.shutil,'which',return_value='/usr/bin/npm'),redirect_stdout(io.StringIO()):
                with patch.object(installer.subprocess,'run'),patch('sys.argv',['install_global.py']):installer.main()
                skill=home/'.agents/skills/project-showcase/SKILL.md';before=skill.read_bytes()
                launcher=home/'.local/bin/project-showcase';command=launcher.read_bytes()
                with patch.object(installer.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'npm')),patch('sys.argv',['install_global.py','--replace']),self.assertRaises(subprocess.CalledProcessError):installer.main()
                self.assertEqual(skill.read_bytes(),before);self.assertEqual(launcher.read_bytes(),command)
                self.assertTrue((home/'.claude/skills/project-showcase/SKILL.md').exists())
                self.assertFalse((home/'.local/share/project-showcase/backups').exists())

    def test_activation_failure_restores_old_skill_alias_and_launcher(self):
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder)
            with patch.object(installer.Path,'home',return_value=home),patch.object(installer.venv.EnvBuilder,'create'),patch.object(installer.shutil,'which',return_value='/usr/bin/npm'),patch.object(installer.subprocess,'run'),redirect_stdout(io.StringIO()):
                with patch('sys.argv',['install_global.py']):installer.main()
                skill=home/'.agents/skills/project-showcase/SKILL.md';before=skill.read_bytes()
                launcher=home/'.local/bin/project-showcase';command=launcher.read_bytes()
                with patch.object(installer.Path,'symlink_to',side_effect=OSError('fixture activation failure')),patch('sys.argv',['install_global.py','--replace']),self.assertRaises(OSError):installer.main()
                self.assertEqual(skill.read_bytes(),before);self.assertEqual(launcher.read_bytes(),command)
                self.assertTrue((home/'.claude/skills/project-showcase/SKILL.md').exists())

if __name__=='__main__':unittest.main()
