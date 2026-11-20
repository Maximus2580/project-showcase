"""Real Chromium deck regressions (no TTS/network calls).

Run: .venv/bin/python -m unittest discover -s tests -p test_browser.py -v
Requires setup's Node dependencies and Chrome (or CHROME_PATH).
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/project-showcase/scripts'
sys.path.insert(0, str(SCRIPTS))
import showcase as s
from render import build_outputs
import design as d
from bootstrap import environment_fixture


class DeckBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('node') or not (s.SKILL / 'node_modules/playwright').exists():
            raise unittest.SkipTest('Run skill setup first: Node and Playwright required')
        cls.temp = tempfile.TemporaryDirectory(prefix='project-showcase-browser-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.fixture = cls.root / 'fixture'
        cls.fixture.mkdir()
        # Copy every referenced image; renderer creates local media/fonts assets.
        environment_fixture(cls.fixture)
        model = s.load(cls.fixture)
        build_outputs(model, None, cls.fixture, s.SKILL)

    def check_copy(self, name, css='', source=None):
        deck = self.root / name
        shutil.copytree((source or self.fixture) / 'deck', deck)
        index = deck / 'index.html'
        if css:
            original = index.read_text(encoding='utf-8')
            index.write_text(original.replace('</style>', css + '</style>', 1), encoding='utf-8')
        output = self.root / (name + '-qa')
        result = subprocess.run(['node', str(SCRIPTS / 'check-deck.mjs'), str(index), str(output)],
                                capture_output=True, text=True, timeout=180, env=os.environ.copy())
        self.assertTrue((output / 'report.json').is_file(), result.stderr + result.stdout)
        report = json.loads((output / 'report.json').read_text())
        return result, report

    def design_fixture(self,name):
        fixture=self.root/name;shutil.copytree(self.fixture,fixture)
        d.scaffold(Namespace(out=fixture))
        return fixture

    def test_four_full_design_decks_pass_at_both_sizes(self):
        fixture=self.design_fixture('designed-all')
        for ident in ('direction-a','direction-b','direction-c','direction-d'):
            source=fixture/'design/variants'/ident
            m=s.load(fixture);m['_design']={'config':s.read(source/'variant.json'),'source':str(source)}
            build_outputs(m,None,fixture,s.SKILL)
            result,report=self.check_copy('full-'+ident,source=fixture)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(report['ok']);self.assertEqual(report['slide_count'],8)
            self.assertEqual(report['viewports'],[1920,1280])

    def test_invisible_ancestor_and_bad_contrast_are_rejected(self):
        fixture=self.design_fixture('designed-hidden')
        source=fixture/'design/variants/direction-a'
        m=s.load(fixture);m['_design']={'config':s.read(source/'variant.json'),'source':str(source)}
        build_outputs(m,None,fixture,s.SKILL)
        for name,css,reason in [('hidden-header','.designed header{opacity:0}','hidden required content ancestor'),('hidden-stage','#stage{opacity:0}','hidden required content ancestor'),('bad-contrast','.designed h1{color:#f5f7fb}','text contrast')]:
            result,report=self.check_copy(name,css,fixture)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertTrue(any(reason in issue for shot in report['shots'] for issue in shot['issues']))

    def test_normal_deck_passes_real_browser_and_navigation(self):
        result, report = self.check_copy('normal')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['errors'], [])
        self.assertGreaterEqual(report['samples'], 8)
        self.assertTrue(all(not shot['issues'] for shot in report['shots']))

    def test_panel_ancestor_clipping_is_rejected(self):
        result, report = self.check_copy('clipped', '.panel{height:20px!important;overflow:hidden!important}')
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertFalse(report['ok'])
        issues = [issue for shot in report['shots'] for issue in shot['issues']]
        self.assertTrue(any('ancestor clipping' in issue for issue in issues), issues)
        # Failure must be clipping, not broken fixture paths or JS startup.
        self.assertEqual(report['errors'], [])
        self.assertNotIn('missing image', issues)

    def test_unavailable_demo_fallback_has_no_clipping_or_missing_assets(self):
        fixture = self.root / 'unavailable-fixture'
        shutil.copytree(self.fixture, fixture)
        model = s.read(fixture / 'project.json')
        for scene in model['scenes']:
            if scene['kind'] == 'demo':
                scene.pop('media', None)
                scene['states'] = {}; scene['beats'] = []
                scene['verification'] = 'code-reviewed'
                scene['unavailable_reason'] = 'API 인증 정보가 없어 실행하지 못했습니다.'
        s.write(fixture / 'project.json', model)
        build_outputs(s.load(fixture), None, fixture, s.SKILL)
        result, report = self.check_copy('unavailable', source=fixture)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(report['ok'], report)


if __name__ == '__main__':
    unittest.main()
