import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import site_release as site
import public_projection as projection

class PublicProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.output=Path(self.temp.name)/'site'
        site.package(ROOT,self.output,public=True)

    def test_public_snapshot_passes_while_canonical_review_is_preserved(self):
        result=site.check_artifact(ROOT,self.output,public=True)
        self.assertGreater(result['pages'],20)
        self.assertEqual(site.publication_blockers(ROOT,self.output),[])
        internal=site.read_json(ROOT/'atlas/entities/index.json')['entities']
        self.assertTrue(any(e['lifecycleStatus']=='REVIEW' for e in internal))
        public=site.read_json(self.output/'atlas/entities/index.json')['entities']
        self.assertTrue(all(e['lifecycleStatus']=='PUBLISHED' for e in public))
        self.assertLess(len(public),len(internal))

    def test_private_static_alias_payload_and_edges_are_absent(self):
        hidden,paths=projection.private_paths(ROOT)
        for rel in paths:self.assertFalse((self.output/rel).exists(),rel)
        for p in self.output.rglob('*'):
            if p.is_file() and p.suffix in ('.html','.json','.xml'):
                text=p.read_text(encoding='utf-8')
                for eid in hidden:self.assertNotIn(eid,text,str(p))
        self.assertTrue((self.output/'atlas/organization.html').exists())
        self.assertTrue((self.output/'atlas/concept/private-capital/index.html').exists())

    def test_hidden_entity_in_an_extra_json_file_rejects_publication(self):
        p=self.output/'atlas/sources/injected.json'
        p.write_text(json.dumps({'sources':[{'id':'source:injected','object':'project:dadman'}]}))
        self.assertTrue(any('non-public reference project:dadman' in e for e in site.publication_blockers(ROOT,self.output)))
        with self.assertRaisesRegex(ValueError,'extra='):
            site.check_artifact(ROOT,self.output,public=True)

    def test_dangling_evidence_and_hidden_relation_are_rejected(self):
        p=self.output/'atlas/claims/stage-5-reviewed.json';d=site.read_json(p)
        d['claims'][0]['object']='project:dadman'
        d['claims'][0]['evidenceRefs']=['evidence:absent']
        p.write_text(json.dumps(d))
        errors=site.publication_blockers(ROOT,self.output)
        self.assertTrue(any('dangling public Entity' in e for e in errors))
        self.assertTrue(any('broken Evidence' in e for e in errors))

    def test_unattributed_reported_claim_is_rejected(self):
        p=self.output/'atlas/claims/stage-5-reviewed.json';d=site.read_json(p)
        d['claims'][0]['status']='REPORTED';d['claims'][0]['context']={}
        p.write_text(json.dumps(d))
        self.assertTrue(any('lacks attribution' in e for e in site.publication_blockers(ROOT,self.output)))

    def test_current_revision_is_public_and_history_remains_internal(self):
        public,_=projection.records(self.output,'claims')
        internal,_=projection.records(ROOT,'claims')
        current='claim:ali-sanginian-ceo-amin-investment-bank-observed-1395'
        predecessor=internal[current]['supersedes']
        self.assertIn(current,public);self.assertIn(predecessor,internal)
        self.assertNotIn(predecessor,public)
        self.assertIsNone(public[current]['temporal']['start'])
        self.assertIn('1395-04-09',public[current]['context']['observation_date'])

    def test_profile_provenance_is_fail_closed(self):
        original=projection.records
        def missing_source(root,family):
            data,owners=original(root,family)
            if family=='sources':data.pop('source:achareh-official-profile')
            return data,owners
        with patch.object(projection,'records',side_effect=missing_source):
            with self.assertRaisesRegex(ValueError,'missing profile source'):
                projection.snapshot(ROOT)

    def test_article_chart_attribution_is_correct_and_primary_not_claimed(self):
        article=site.read_json(ROOT/'research/content/private-markets/private-capital-research/research.json')
        figure=next(b for s in article['sections'] for b in s['content'] if b['id']=='block-0015')
        self.assertIn('Deloitte',figure['credit']);self.assertNotIn('CFA',figure['credit'])
        self.assertTrue(any(c['sourceRef']=='source:deloitte-asian-investment' and c['contentBlockId']=='block-0009' for c in article['citations']))
        self.assertNotIn('source:globalswf-reports',site.read_json(self.output/'atlas/sources/index.json')['sources'])

    def test_source_frameworks_and_research_connections_remain_visible(self):
        page=(self.output/'atlas/concept/private-capital/index.html').read_text(encoding='utf-8')
        self.assertIn('CFA',page);self.assertIn('Preqin',page)
        self.assertIn('/articles/private-capital.html',page)
        self.assertIn('/articles/private-capital-research.html',page)

if __name__=='__main__':unittest.main()
