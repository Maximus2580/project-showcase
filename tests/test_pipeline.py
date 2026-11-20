"""Offline state-machine regressions; mock media is not playback/visual QA evidence."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/project-showcase/scripts'))
import showcase as s
from render import body
from bootstrap import environment_fixture


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
        self.m = environment_fixture(self.out)
        self.m['schema_version'] = 2
        self.m['profile'] = 'sample'
        # Keep an actual image fixture; never let a missing image mask a gate failure.
        media = next((self.out / 'input').rglob('*.png')).relative_to(self.out).as_posix()
        for sc in self.m['scenes']:
            sc['utterances'] = [{'id': 'u01', 'text': sc['id'] + ' 첫 설명입니다.'},
                                {'id': 'u02', 'text': sc['id'] + ' 두 번째 설명입니다.'}]
            sc.pop('narration', None)
            sc['states'] = {'screen': {'media': media, 'label': '테스트 화면', 'source': 'fixture'}}
            sc['beats'] = [{'utterance': 'u01', 'action': 'replace', 'state': 'screen'},
                           {'utterance': 'u02', 'action': 'highlight', 'state': 'screen',
                            'region': [0.1, 0.2, 0.3, 0.4]}]
            sc['media'] = media
            sc.pop('needs_visual_review', None)
        self.save()
        self.m = s.load(self.out)
        self.args = Namespace(out=self.out, timed=True, regenerate=False, draft=True)

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        s.write(self.out / 'project.json', self.m)

    def seed(self, length=2):
        for unit in s.voice_units(self.m):
            p = self.out / 'audio' / (s.voice_key(self.m, unit) + '.mp3')
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(b'test-only-not-real-audio')
            s.write(p.with_suffix('.json'), {'duration': length, 'audio_sha256': s.filehash(p),
                    'cues': [{'start': .1, 'end': length - .1, 'text': unit['narration']}]})

    def generated(self):
        """Synthetic tracked output for state tests, deliberately no browser/render claim."""
        self.seed()
        timeline = s.make_timeline(self.m, self.out)
        for folder in ('deck', 'video'):
            (self.out / folder).mkdir(exist_ok=True)
            (self.out / folder / 'index.html').write_text('<html>fixture</html>')
        for name in s.SIDECARS:
            (self.out / name).write_text('fixture')
        s.write(self.out / 'timeline.json', timeline)
        (self.out / 'captions.srt').write_text(s.srt(timeline['captions']))
        s.record(self.out, 'build', {'timed': True, 'project_digest': s.digest(s.load(self.out)),
                 'inputs_digest': s.inputs_digest(self.m, self.out),
                 'signature': s.build_signature(self.out), 'generated': s.generated_files(self.out)})

    def approved(self):
        self.generated()
        sig = s.build_signature(self.out)
        p = self.out / 'renders/fixture.mp4'
        p.parent.mkdir(); p.write_bytes(b'test-only-not-real-video')
        st = s.state(self.out)
        st['steps'].update({'check': {'ok': True, 'id': 'check-1', 'signature': sig},
                            'snapshots': {'signature': sig},
                            'render': {'signature': sig, 'file': 'renders/fixture.mp4', 'sha256': s.filehash(p)}})
        st['reviews'] = {'frames': {'signature': sig, 'check_id': 'check-1'},
                         'listening': {'signature': sig, 'render_sha256': s.filehash(p)}}
        s.write(self.out / 'state.json', st)
        s.require_frames(self.out)

    def test_v2_fixture_validates_with_real_images(self):
        self.assertEqual(s.load(self.out)['schema_version'], 2)
        self.m['profile'] = 'production'; self.save()
        s.load(self.out)

    def test_timing_offsets_and_beats_follow_each_utterance(self):
        self.seed(2.001)
        t = s.make_timeline(self.m, self.out)
        for row in t['scenes']:
            self.assertEqual(row['beats'][0]['time'], 0)
            self.assertEqual(row['beats'][1]['time'], row['clips'][1]['local_start'])
            self.assertGreaterEqual(row['clips'][1]['start'], row['clips'][0]['start'] + 2.001)
            self.assertGreaterEqual(row['duration'], row['audio_duration'] + .3)
        for a, b in zip(t['scenes'], t['scenes'][1:]):
            self.assertEqual(a['start_frame'] + a['frames'], b['start_frame'])
        self.assertAlmostEqual(t['captions'][2]['start'], t['scenes'][1]['start'] + .1)

    def test_production_duration_guard_and_valid_window(self):
        self.m['profile'] = 'production'; self.seed(2)
        with self.assertRaisesRegex(ValueError, 'E_DURATION'):
            s.make_timeline(self.m, self.out)
        self.seed(11)
        self.assertTrue(170 <= s.make_timeline(self.m, self.out)['duration'] <= 190)

    def test_voice_cache_changes_only_with_voice_inputs(self):
        unit = next(s.voice_units(self.m)); before = s.voice_key(self.m, unit)
        self.m['scenes'][0]['title'] = '다른 제목'
        self.assertEqual(before, s.voice_key(self.m, next(s.voice_units(self.m))))
        self.m['scenes'][0]['utterances'][0]['text'] += ' 새 문장.'
        self.assertNotEqual(before, s.voice_key(self.m, next(s.voice_units(self.m))))

    def test_reordering_reuses_audio_but_retimes_cues(self):
        self.seed()
        original = s.make_timeline(self.m, self.out)
        second = list(s.voice_units(self.m))[2]
        key = s.voice_key(self.m, second)
        self.m['scenes'][0], self.m['scenes'][1] = self.m['scenes'][1], self.m['scenes'][0]
        reordered = s.make_timeline(self.m, self.out)
        self.assertEqual(key, s.voice_key(self.m, next(s.voice_units(self.m))))
        self.assertEqual(reordered['scenes'][0]['start_frame'], 0)
        self.assertEqual(reordered['captions'][0]['scene'], original['captions'][2]['scene'])
        self.assertAlmostEqual(reordered['captions'][0]['start'], .1)

    def test_corrupt_audio_is_not_reused(self):
        self.seed(); unit = next(s.voice_units(self.m))
        (self.out / 'audio' / (s.voice_key(self.m, unit) + '.mp3')).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'E_AUDIO_CHANGED'):
            s.make_timeline(self.m, self.out)

    def test_failed_recheck_invalidates_prior_success_and_reviews(self):
        self.approved()
        with patch.object(s, 'run', side_effect=RuntimeError('browser crashed')) as run:
            with self.assertRaisesRegex(RuntimeError, 'browser crashed'):
                s.check(self.args)
        run.assert_called_once()
        st = s.state(self.out)
        for key in ('check', 'snapshots', 'render'):
            self.assertNotIn(key, st['steps'])
        self.assertEqual(st['reviews'], {})
        with self.assertRaisesRegex(ValueError, 'E_CHECK_REQUIRED'):
            s.require_frames(self.out)

    def test_sidecar_tampering_invalidates_frames(self):
        self.approved()
        for name in s.SIDECARS:
            with self.subTest(name=name):
                p = self.out / name; original = p.read_bytes(); p.write_bytes(original + b'changed')
                with self.assertRaisesRegex(ValueError, 'E_CHECK_REQUIRED'):
                    s.require_frames(self.out)
                p.write_bytes(original)
        s.require_frames(self.out)

    def test_input_image_tampering_invalidates_frames(self):
        self.approved()
        (self.out / self.m['scenes'][0]['media']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'E_CHECK_REQUIRED'):
            s.require_frames(self.out)

    def test_changed_source_image_requires_rebuild_before_check(self):
        self.approved()
        image = self.out / self.m['scenes'][0]['media']
        image.write_bytes(image.read_bytes() + b'changed-source')
        with patch.object(s, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'E_INPUTS_CHANGED'): s.check(self.args)
        run.assert_not_called()
        self.assertEqual(s.state(self.out)['reviews'], {})

    def test_changed_source_image_makes_resume_rebuild(self):
        self.generated()
        image = self.out / self.m['scenes'][0]['media']
        image.write_bytes(image.read_bytes() + b'changed-source')
        with patch.object(s, 'tts') as tts, patch.object(s, 'build') as build, \
                patch.object(s, 'check'), patch.object(s, 'snapshots'):
            s.resume(self.args)
        tts.assert_called_once_with(self.args)
        build.assert_called_once_with(self.args)

    def test_manual_html_blocks_resume_before_tts_and_preserves_file(self):
        self.generated(); p = self.out / 'deck/index.html'; p.write_text('manual design')
        with patch.object(s, 'tts') as tts:
            with self.assertRaisesRegex(ValueError, 'E_MANUAL_EDITS'):
                s.resume(self.args)
        tts.assert_not_called(); self.assertEqual(p.read_text(), 'manual design')

    def test_regenerate_backs_up_manual_html(self):
        self.generated(); (self.out / 'deck/index.html').write_text('manual design')
        self.args.regenerate = True
        s.protect_edits(self.args)
        backups = list((self.out / 'backups').glob('*/deck/index.html'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'manual design')
        self.assertEqual((self.out / 'deck/index.html').read_text(), 'manual design')

    def test_new_manual_file_is_protected_and_backed_up(self):
        self.generated()
        added = self.out / 'deck/custom.css'; added.write_text('.hero{color:red}')
        with self.assertRaisesRegex(ValueError, 'E_MANUAL_EDITS.*custom.css'):
            s.protect_edits(self.args)
        self.args.regenerate = True; s.protect_edits(self.args)
        backup = list((self.out / 'backups').glob('*/deck/custom.css'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_text(), added.read_text())

    def test_timeline_regeneration_is_not_misclassified_as_manual_edit(self):
        self.approved(); self.seed(3)
        s.timeline(self.args)
        s.protect_edits(self.args)
        st = s.state(self.out)
        self.assertNotIn('check', st['steps']); self.assertEqual(st['reviews'], {})
        self.assertGreater(s.read(self.out / 'timeline.json')['duration'], 45)

    def test_status_is_read_only_while_locked(self):
        s.write(self.out / 'state.json', {'status': '진행 중', 'steps': {}, 'reviews': {}, 'active': {'command': 'render'}})
        lock = self.out / '.pipeline.lock'; lock.write_text('held-lock')
        before = (self.out / 'state.json').read_bytes()
        result = subprocess.run([sys.executable, str(s.SKILL / 'scripts/showcase.py'), '--out', str(self.out), 'status'],
                                capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['active']['command'], 'render')
        self.assertEqual(lock.read_text(), 'held-lock')
        self.assertEqual(before, (self.out / 'state.json').read_bytes())

    def test_export_excludes_unreferenced_private_input(self):
        self.approved(); (self.out / 'input/private.txt').write_text('private')
        with zipfile.ZipFile(s.export_bundle(self.args)) as z:
            self.assertNotIn('input/private.txt', z.namelist())
            self.assertIn(self.m['scenes'][0]['media'], z.namelist())
            self.assertEqual(json.loads(z.read('MANIFEST.json'))['status'], '검수 대기')

    def test_export_manifest_hashes_match_actual_archive_bytes(self):
        self.approved()
        with zipfile.ZipFile(s.export_bundle(self.args)) as z:
            manifest = json.loads(z.read('MANIFEST.json'))
            self.assertEqual(set(z.namelist()) - {'MANIFEST.json', 'START-HERE.txt'}, set(manifest['files']))
            for name, digest in manifest['files'].items():
                with self.subTest(name=name):
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
            self.assertEqual(manifest['signature'], s.build_signature(self.out))

    def test_export_rejects_stale_render_even_with_current_frame_approval(self):
        self.approved(); st = s.state(self.out); st['steps']['render']['signature'] = 'old'
        s.write(self.out / 'state.json', st)
        with self.assertRaisesRegex(ValueError, 'E_EXPORT_STALE'):
            s.export_bundle(self.args)

    def test_export_rejects_modified_render_bytes(self):
        self.approved(); (self.out / 'renders/fixture.mp4').write_bytes(b'other')
        with self.assertRaisesRegex(ValueError, 'E_EXPORT_VIDEO'):
            s.export_bundle(self.args)

    def test_reviewed_export_requires_current_listening(self):
        self.approved(); st = s.state(self.out); st['reviews'].pop('listening'); s.write(self.out / 'state.json', st)
        self.args.draft = False
        with self.assertRaisesRegex(ValueError, 'E_LISTENING_REQUIRED'):
            s.export_bundle(self.args)

    def test_frame_review_is_bound_to_check_run(self):
        self.approved(); st = s.state(self.out); st['steps']['check']['id'] = 'new-check'
        s.write(self.out / 'state.json', st)
        with self.assertRaisesRegex(ValueError, 'E_FRAMES_REQUIRED'):
            s.require_frames(self.out)

    def test_v2_invalid_beats_and_states_fail_with_specific_errors(self):
        cases = [
            ('E_BEAT_UTTERANCE', lambda sc: sc['beats'][1].update(utterance='missing')),
            ('E_BEAT_STATE', lambda sc: sc['beats'][1].update(state='missing')),
            ('E_BEAT_ACTION', lambda sc: sc['beats'][1].update(action='spin')),
            ('E_BEAT_REGION', lambda sc: sc['beats'][1].update(region=[.9, 0, .2, .2])),
            ('E_BEAT_REGION', lambda sc: sc['beats'][1].update(region=[float('nan'), 0, .2, .2])),
            ('E_BEAT_ORDER', lambda sc: sc['beats'].reverse()),
            ('E_STATE_MEDIA', lambda sc: sc['states']['screen'].update(media='input/missing.png')),
            ('E_STATE_EVIDENCE', lambda sc: sc['states']['screen'].pop('source')),
            ('E_UTTERANCES', lambda sc: sc['utterances'][1].update(id='u01')),
            ('E_DEMO_BEATS', lambda sc: sc.update(beats=[])),
        ]
        for code, mutate in cases:
            with self.subTest(code=code):
                m = copy.deepcopy(self.m); sc = next(sc for sc in m['scenes'] if sc['kind'] == 'demo')
                mutate(sc); s.write(self.out / 'project.json', m)
                with self.assertRaisesRegex(ValueError, code): s.load(self.out)

    def test_production_demo_requires_actual_media(self):
        self.m['profile'] = 'production'
        sc = next(sc for sc in self.m['scenes'] if sc['kind'] == 'demo')
        sc.pop('media'); sc['states'] = {}; sc['beats'] = []
        self.save()
        with self.assertRaisesRegex(ValueError, 'production 데모는 실제 캡처 이미지'): s.load(self.out)

    def test_production_state_media_needs_no_duplicate_scene_media(self):
        self.m['profile'] = 'production'
        next(sc for sc in self.m['scenes'] if sc['kind'] == 'demo').pop('media')
        self.save(); s.load(self.out)

    def unavailable_demo(self):
        self.m['profile'] = 'production'
        sc = next(sc for sc in self.m['scenes'] if sc['kind'] == 'demo')
        sc.pop('media', None)
        sc['states'] = {}; sc['beats'] = []
        sc['verification'] = 'code-reviewed'
        sc['unavailable_reason'] = 'API 인증 정보가 없어 실행하지 못했습니다.'
        return sc

    def test_unavailable_demo_accepts_reason_and_renders_honest_fallback(self):
        sc = self.unavailable_demo(); self.save()
        s.load(self.out)
        for video in (False, True):
            rendered = body(sc, self.m, {}, video)
            self.assertIn('실행 화면 미확보', rendered)
            self.assertIn(sc['unavailable_reason'], rendered)
            self.assertIn('코드 검토 · 실행 미확인', rendered)
            self.assertNotIn('<svg', rendered)

    def test_unavailable_demo_rejects_conflicting_execution_or_visuals(self):
        self.unavailable_demo()
        for field, value in [('verification', 'executed'),
                             ('media', self.m['scenes'][0]['media']),
                             ('states', copy.deepcopy(self.m['scenes'][0]['states'])),
                             ('beats', copy.deepcopy(self.m['scenes'][0]['beats']))]:
            with self.subTest(field=field):
                m = copy.deepcopy(self.m)
                next(sc for sc in m['scenes'] if sc['kind'] == 'demo')[field] = value
                s.write(self.out / 'project.json', m)
                with self.assertRaisesRegex(ValueError, 'E_UNAVAILABLE_DEMO'): s.load(self.out)

    def test_unavailable_demo_without_nonempty_reason_is_rejected(self):
        sc = self.unavailable_demo()
        for reason in ('', '   ', None):
            with self.subTest(reason=reason):
                sc['unavailable_reason'] = reason; self.save()
                with self.assertRaises(ValueError): s.load(self.out)

    def test_missing_slides_and_duplicate_ids_rejected(self):
        self.m['scenes'][1]['id'] = self.m['scenes'][0]['id']
        self.m['scenes'][1]['slide'] = 1
        self.save()
        with self.assertRaisesRegex(ValueError, 'id 중복'): s.load(self.out)
        self.m['scenes'][1]['id'] = 'unique-scene'
        self.save()
        with self.assertRaisesRegex(ValueError, '8장 슬라이드'): s.load(self.out)

    def test_production_migration_requires_visual_review(self):
        self.m['profile'] = 'production'
        self.m['scenes'][0]['needs_visual_review'] = True
        self.save()
        with self.assertRaisesRegex(ValueError, 'E_MIGRATION_REVIEW'): s.load(self.out)

    def test_gate_fails_closed(self):
        for report in ({'ok': True, 'browserSkipped': True, 'layout': {'samples': 20}},
                       {'ok': True, 'browserSkipped': False, 'layout': {'samples': 0}},
                       {'ok': True, 'browserSkipped': False},
                       {'ok': True, 'browserSkipped': False, 'layout': {'samples': []}}):
            self.assertFalse(s.gate_hf(report))
        for samples in (8, [0.5, 2.0]):
            self.assertTrue(s.gate_hf({'ok': True, 'browserSkipped': False, 'layout': {'samples': samples}}))

    def test_inventory_excludes_secrets_and_links(self):
        root = self.out / 'project'; root.mkdir()
        (root / '.env.local').write_text('secret'); (root / 'app.py').write_text('pass')
        (root / 'node_modules').mkdir(); (root / 'node_modules/x').write_text('x')
        (root / 'link').symlink_to('/etc/hosts')
        out = self.out / 'out'; s.inventory(root, out)
        self.assertEqual([f['path'] for f in s.read(out / 'inventory.json')['files']], ['app.py'])

    def test_safe_media_paths(self):
        for name in ('../private.png', 'input/../private.png', str(self.out / 'input/image.png'),
                     'input\\image.png', 'C:\\private.png'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError): s.safe(self.out, name)
        self.assertEqual(s.safe(self.out, 'input/image.png'), (self.out / 'input/image.png').resolve())

    def test_doctor_online_failure_clears_previous_pass(self):
        s.write(self.out / 'doctor.json', {'ok': True})
        self.args.online = True
        with patch.object(s, 'run', return_value='v22.0.0'), \
                patch.object(s, 'hf', return_value='0.9.72'), \
                patch('importlib.metadata.version', return_value='7.3.1'), \
                patch('edge_tts.list_voices', new=AsyncMock(side_effect=RuntimeError('offline'))):
            with self.assertRaisesRegex(RuntimeError, 'offline'): s.doctor(self.args)
        report = s.read(self.out / 'doctor.json')
        self.assertIs(report['ok'], False)
        self.assertEqual(report['status'], 'checking')

    def test_preflight_doctor_failure_clears_previous_pass(self):
        s.write(self.out / 'preflight.json', {'ok': True})
        def fail_doctor(args):
            self.assertIs(s.read(self.out / 'preflight.json')['ok'], False)
            raise RuntimeError('offline doctor')
        with patch.object(s, 'doctor', side_effect=fail_doctor):
            with self.assertRaisesRegex(RuntimeError, 'offline doctor'): s.preflight(self.args)
        report = s.read(self.out / 'preflight.json')
        self.assertIs(report['ok'], False)
        self.assertEqual(report['status'], 'checking')

    def test_emphasis_target_accepts_point_and_table_boundaries(self):
        for kind in ('problem', 'evidence'):
            sc = next(sc for sc in self.m['scenes'] if sc['kind'] == kind)
            if kind == 'evidence':
                sc['table'] = [['항목', '관찰', '한계']] * 4
            count = len(sc.get('table') or sc['points'])
            for target in (1, count):
                with self.subTest(kind=kind, target=target):
                    sc['utterances'][0]['emphasis_target'] = target
                    self.save(); s.load(self.out)

    def test_emphasis_target_rejects_invalid_types_bounds_and_demo(self):
        for kind, targets in [('problem', [0, 99, -1, True, 1.0, '1', None]), ('demo', [1])]:
            for target in targets:
                with self.subTest(kind=kind, target=target):
                    model = copy.deepcopy(self.m)
                    sc = next(sc for sc in model['scenes'] if sc['kind'] == kind)
                    sc['utterances'][0]['emphasis_target'] = target
                    s.write(self.out / 'project.json', model)
                    with self.assertRaisesRegex(ValueError, 'E_EMPHASIS_TARGET'): s.load(self.out)

    def test_init_creates_neutral_outline_and_preserves_original(self):
        args = Namespace(out=self.out / '한글 폴더', project=self.out)
        s.init(args); model=s.load(args.out); self.assertTrue(all(x['verification']=='unverified' for x in model['scenes'])); self.assertEqual(list((args.out/'input').iterdir()),[]); original = (args.out / 'project.json').read_bytes()
        with self.assertRaises(ValueError): s.init(args)
        self.assertEqual(original, (args.out / 'project.json').read_bytes())

    def test_srt_carries_milliseconds(self):
        self.assertEqual(s.stamp(59.9996), '00:01:00,000')

    def test_sample_cannot_finish_without_review(self):
        s.load(self.out)
        with self.assertRaisesRegex(ValueError, 'E_CHECK_REQUIRED'): s.finish(self.args)


if __name__ == '__main__':
    unittest.main()
