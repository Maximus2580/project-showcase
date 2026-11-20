"""Selection gates and immutable previews. Mock QA here is not visual approval."""
import copy
from argparse import Namespace
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/project-showcase/scripts'))
import showcase as s
import design as d
import render
from bootstrap import environment_fixture

class DesignTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name).resolve()
        self.args=Namespace(out=self.out,project=self.out,timed=False,regenerate=False,variant=None)
        s.init(self.args);environment_fixture(self.out);d.scaffold(self.args)
        self.brief=self.out/'design/brief.json'
        b=s.read(self.brief);b.update(ready=True,context='Synthetic test fixture',decision_notes='Explicit fixture directions',representatives=['scene-01','scene-04','scene-06'])
        s.write(self.brief,b)
        for ident in b['variants']:
            p=self.out/'design/variants'/ident/'variant.json';c=s.read(p);c['rationale']='Synthetic test direction';s.write(p,c)

    def fake_qa(self,argv,**kwargs):
        dest=Path(argv[3]);dest.mkdir(exist_ok=True)
        s.write(dest/'report.json',{'ok':True,'fixture_only':True})
        return '{}'

    def previews(self):
        with patch.object(s,'run',side_effect=self.fake_qa):d.preview(self.args)

    def select(self):
        current=s.read(self.out/'design/previews/direction-a/current.json')
        d.select(Namespace(out=self.out,variant='direction-a',revision=current['revision'],by='automated test fixture',reason='Not a human preference or review'))

    def ready(self):self.previews();self.select()

    def test_new_init_requires_selection_and_uses_stable_ids(self):
        m=s.load(self.out);self.assertTrue(d.enabled(m))
        self.assertTrue(m['scenes'][1]['utterances'][0]['emphasis_id'])
        for fn in (s.build,s.tts,s.timeline,s.resume,s.check,s.snapshots,s.render,s.finish,s.export_bundle):
            with self.subTest(fn=fn.__name__), self.assertRaisesRegex(ValueError,'E_DESIGN_SELECTION_REQUIRED'):
                fn(self.args)
        self.assertFalse((self.out/'audio').exists());self.assertFalse((self.out/'deck').exists())

    def test_selected_preview_and_production_share_markup_and_assets(self):
        self.ready();s.build(self.args)
        preview=(self.out/'design/previews/direction-a/r001/deck/index.html').read_text()
        full=(self.out/'deck/index.html').read_text()
        a=preview[preview.index('<section'):preview.index('</section>')+10]
        self.assertIn(a,full)
        self.assertEqual(d.status(self.out,s.load(self.out))['phase'],'production')

    def test_wrong_revision_and_missing_other_directions_are_rejected(self):
        self.args.variant='direction-a';self.previews()
        with self.assertRaisesRegex(ValueError,'E_DESIGN_PREVIEW_REQUIRED'):self.select()
        self.args.variant=None;self.previews()
        with self.assertRaisesRegex(ValueError,'E_DESIGN_REVISION'):
            d.select(Namespace(out=self.out,variant='direction-a',revision='r999',by='fixture',reason='fixture'))

    def test_partial_revision_preserves_old_preview_and_other_directions(self):
        self.ready();old=self.out/'design/previews/direction-a/r001/deck/index.html';before=old.read_bytes()
        css=self.out/'design/variants/direction-a/style.css';css.write_text('.designed .eyebrow{font-weight:600}')
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)
        self.args.variant='direction-a';self.previews()
        self.assertEqual(old.read_bytes(),before)
        self.assertEqual(s.read(self.out/'design/previews/direction-b/current.json')['revision'],'r001')
        self.assertEqual(s.read(self.out/'design/previews/direction-a/current.json')['revision'],'r002')
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)
        self.select();self.assertEqual(d.require_selected(self.out)['selection']['revision'],'r002')

    def test_manual_preview_edit_is_preserved_and_blocks_selection(self):
        self.previews();p=self.out/'design/previews/direction-a/r001/deck/index.html';p.write_text(p.read_text()+'manual')
        with self.assertRaisesRegex(ValueError,'E_DESIGN_PREVIEW_EDIT'):self.select()
        with self.assertRaisesRegex(ValueError,'E_DESIGN_PREVIEW_EDIT'):self.previews()
        self.assertTrue(p.read_text().endswith('manual'))

    def test_selection_is_stale_after_request_font_or_asset_change(self):
        self.ready();p=self.out/'project.json';original=p.read_bytes();m=s.read(p);m['design']['request']='A different direction';s.write(p,m)
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)
        p.write_bytes(original)
        image=self.out/s.load(self.out)['scenes'][3]['states']['input']['media']
        image.write_bytes(image.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)

    def test_speech_and_nonrepresentative_content_preserve_style_choice(self):
        self.ready();p=self.out/'project.json';m=s.read(p)
        m['scenes'][0]['utterances'][0]['text']='발화만 변경합니다.'
        m['scenes'][7]['items'][0]['text']='마지막 장의 내용 수정';s.write(p,m)
        self.assertIsNotNone(d.require_selected(self.out))

    def test_reordering_content_keeps_emphasis_semantics(self):
        m=s.load(self.out);sc=m['scenes'][1];uid=sc['utterances'][0]['emphasis_id'];before=next(x['text'] for x in sc['items'] if x['id']==uid)
        sc['items'].reverse();d.normalize(m)
        self.assertEqual(next(x['text'] for x in sc['items'] if x['id']==uid),before)
        js=render.motion(sc,{'duration':3,'clips':[{'utterance':sc['utterances'][0]['id'],'local_start':0}]},{})
        self.assertIn('data-content-id="'+uid+'"',js)
        self.assertNotIn('items[0]',js)

    def test_color_only_directions_are_rejected(self):
        a=self.out/'design/variants/direction-a/variant.json';b=self.out/'design/variants/direction-b/variant.json'
        config=s.read(a);config['id']='direction-b';config['tokens']['accent']='#303030';s.write(b,config)
        with self.assertRaisesRegex(ValueError,'E_DESIGN_DIVERSITY'):self.previews()

    def test_failed_qa_never_reuses_prior_success(self):
        self.ready();p=self.out/'design/variants/direction-a/style.css';p.write_text('h1{height:1px}')
        def fail(argv,**kwargs):
            self.fake_qa(argv,**kwargs);raise RuntimeError('browser failure')
        with patch.object(s,'run',side_effect=fail),self.assertRaises(RuntimeError):d.preview(self.args)
        self.assertFalse(s.read(self.out/'design/previews/direction-a/current.json')['ok'])
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)

    def test_custom_shell_requires_evidence_slots_and_local_assets(self):
        p=self.out/'design/variants/direction-a/shell.html'
        for markup in ('{{header}}{{content}}','{{header}}{{content}}{{footer}}<script>alert(1)</script>','{{header}}{{content}}{{footer}}<img src="https://example.com/x.png" alt="x">'):
            p.write_text(markup)
            with self.assertRaisesRegex(ValueError,'E_DESIGN_'):self.previews()

    def test_font_and_license_are_required_and_hash_bound(self):
        root=self.out/'design/variants/direction-a';config=s.read(root/'variant.json')
        config['fonts']=[{'family':'FixtureFont','source':'font.woff2','license':'font-license.txt'}]
        config['tokens']['heading-font']='FixtureFont';s.write(root/'variant.json',config)
        with self.assertRaisesRegex(ValueError,'E_DESIGN_ASSET_MISSING'):self.previews()
        shutil.copy2(s.SKILL/'assets/fonts/PretendardVariable.woff2',root/'font.woff2');(root/'font-license.txt').write_text('Test fixture')
        self.ready();(root/'font.woff2').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'E_DESIGN_STALE'):d.require_selected(self.out)

    def test_replacing_all_archives_sources_and_selection(self):
        self.ready();self.args.replace=True;d.scaffold(self.args)
        backups=list((self.out/'backups').glob('design-*'));self.assertEqual(len(backups),1)
        self.assertTrue((backups[0]/'selection.json').exists())
        self.assertFalse((self.out/'design/selection.json').exists())
        with self.assertRaisesRegex(ValueError,'E_DESIGN_SELECTION_REQUIRED'):s.build(self.args)

    def test_global_css_cannot_bypass_selected_revision(self):
        self.ready();m=s.read(self.out/'project.json');m['extra_css']='.designed{background:red}'
        s.write(self.out/'project.json',m)
        with self.assertRaisesRegex(ValueError,'E_DESIGN_CSS'):s.build(self.args)

    def test_evidence_without_table_keeps_item_ids(self):
        self.ready();m=s.load(self.out);sc=m['scenes'][5];sc.pop('table');sc.pop('rows')
        sc['utterances'][0]['emphasis_id']=sc['items'][0]['id'];m['_design']=d.require_selected(self.out)
        output=render.body(sc,m,{})
        self.assertIn('data-content-id="'+sc['items'][0]['id']+'"',output)

    def test_exported_design_sources_can_be_resolved_without_other_variants(self):
        self.ready();dest=self.out/'extracted';dest.mkdir()
        paths=d.selected_files(self.out,s.load(self.out));paths['project.json']=self.out/'project.json'
        paths.update(s.referenced_inputs(s.load(self.out),self.out))
        for name,path in paths.items():
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        self.assertIsNotNone(d.require_selected(dest))

    def test_revision_wait_time_restarts_after_a_completed_selection(self):
        with patch.object(d.time,'time',return_value=100):self.previews()
        with patch.object(d.time,'time',return_value=150):self.select()
        self.assertEqual(s.read(self.out/'design/selection.json')['waiting_seconds'],50)
        (self.out/'design/variants/direction-a/style.css').write_text('.designed{padding-top:74px}')
        with patch.object(d.time,'time',return_value=500):self.previews()
        with patch.object(d.time,'time',return_value=520):self.select()
        self.assertEqual(s.read(self.out/'design/selection.json')['waiting_seconds'],20)

    def test_legacy_deck_order_and_representative_order_are_independent(self):
        m=s.load(self.out);m['scenes'][0],m['scenes'][1]=m['scenes'][1],m['scenes'][0]
        render.build_deck(m,self.out,self.out/'legacy-order',s.SKILL)
        doc=(self.out/'legacy-order/index.html').read_text()
        self.assertLess(doc.index('id="scene-01-scene"'),doc.index('id="scene-02-scene"'))
        m['_preview']=True;m['scenes']=[m['scenes'][1],m['scenes'][3],m['scenes'][0]]
        render.build_deck(m,self.out,self.out/'rep-order',s.SKILL)
        doc=(self.out/'rep-order/index.html').read_text()
        self.assertLess(doc.index('id="scene-04-scene"'),doc.index('id="scene-02-scene"'))

    def test_manual_generated_css_cannot_bypass_the_selected_sources(self):
        self.ready();s.build(self.args)
        st=s.state(self.out);st['steps']['build']['timed']=True;s.write(self.out/'state.json',st)
        p=self.out/'deck/index.html';p.write_text(p.read_text().replace('</style>','h1{color:red}</style>',1))
        with patch.object(s,'run') as run,self.assertRaisesRegex(ValueError,'E_DESIGN_OUTPUT_CHANGED'):
            s.check(self.args)
        run.assert_not_called();self.assertIn('h1{color:red}',p.read_text())

    def test_legacy_project_remains_opt_in_and_signature_compatible(self):
        legacy=self.out/'legacy';args=Namespace(out=legacy,project=self.out,legacy=True,timed=False,regenerate=False)
        s.init(args);self.assertFalse(d.enabled(s.load(legacy)));s.build(args)
        self.assertNotIn('designed problem',(legacy/'deck/index.html').read_text())
        self.assertIsNone(d.require_selected(legacy))

if __name__=='__main__':unittest.main()
