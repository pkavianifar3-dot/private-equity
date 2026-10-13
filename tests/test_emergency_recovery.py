"""Standalone emergency recovery; successful fixtures never authorize deployment."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from urllib.request import build_opener, ProxyHandler
from urllib.error import HTTPError
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import recovery as rec
import emergency_release as emergency
import site_release as site
import tests.test_recovery as public_tests


class EmergencyRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.bundle=self.base/'bundle';self.output=self.base/'restored'
        self.sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        env=dict(GITHUB_REPOSITORY=rec.REPOSITORY,GITHUB_SHA=self.sha,GITHUB_RUN_ID='101',GITHUB_RUN_ATTEMPT='1',
                 GITHUB_REF='refs/heads/main',GITHUB_EVENT_NAME='push')
        # This is an explicit clean-source test fixture, not an actual authorized CI run.
        original=subprocess.check_output
        def git_fixture(args,**kwargs):
            if args==['git','status','--porcelain']:return ''
            return original(args,**kwargs)
        with patch.dict(os.environ,env),patch.object(subprocess,'check_output',side_effect=git_fixture):
            self.m=rec.create(ROOT,self.base/'site',self.bundle,kind='emergency')

    def test_independent_roundtrip_without_canonical_data(self):
        isolated=self.base/'source';shutil.copytree(ROOT/emergency.TEMPLATES,isolated/emergency.TEMPLATES)
        self.assertFalse((isolated/'atlas').exists());self.assertFalse((isolated/'research').exists())
        self.assertEqual(rec.publication(isolated,self.base/'site',kind='emergency')['files'],4)
        result=rec.restore(ROOT,self.bundle,self.output,ROOT)
        self.assertEqual(result['files'],4)
        self.assertEqual({p.name for p in self.output.iterdir()},emergency.FILES)
        rec.pages_tar(self.output,self.base/'pages.tar')
        self.assertFalse((self.output/'manifest.json').exists())

    def test_emergency_files_never_enter_normal_site(self):
        normal=site.package_paths(ROOT,public=True)
        self.assertFalse(any('emergency' in name or name.startswith('tools/') for name in normal))
        self.assertNotIn('data-emergency-site="true"',(ROOT/'index.html').read_text(encoding='utf-8'))
        self.assertEqual(self.m['kind'],'emergency')
        self.assertTrue(self.m['artifact_name'].startswith('emergency-recovery-'))

    def test_dirty_source_rejected(self):
        with patch.object(subprocess,'check_output',side_effect=[self.sha,' M index.html']):
            with self.assertRaisesRegex(ValueError,'clean source'):
                rec.create(ROOT,self.base/'dirty-site',self.base/'dirty-bundle',kind='emergency')

    def rezip(self,mutate):
        with zipfile.ZipFile(self.bundle/'site.zip') as z:values={i.filename:z.read(i) for i in z.infolist()}
        mutate(values)
        with zipfile.ZipFile(self.bundle/'site.zip','w') as z:
            for name,data in values.items():z.writestr(name,data)
        self.m['files']={name:sha256(data).hexdigest() for name,data in values.items()}
        self.m['file_count']=len(values);self.m['archive_sha256']=sha256((self.bundle/'site.zip').read_bytes()).hexdigest()
        (self.bundle/'manifest.json').write_text(json.dumps(self.m),encoding='utf-8')

    def test_hashes_cannot_approve_canonical_or_modified_content(self):
        self.rezip(lambda values:values.update({'atlas/entities/index.json':b'{"REVIEW":true}'}))
        with self.assertRaisesRegex(ValueError,'exactly four'):rec.restore(ROOT,self.bundle,self.output)

    def test_changed_page_even_with_matching_manifest_is_rejected(self):
        self.rezip(lambda values:values.update({'index.html':values['index.html']+b'<script>fetch("/atlas/")</script>'}))
        with self.assertRaisesRegex(ValueError,'bytes differ'):rec.restore(ROOT,self.bundle,self.output)

    def test_raw_tampering_missing_manifest_and_kind_swap(self):
        (self.bundle/'site.zip').write_bytes(b'bad archive')
        with self.assertRaisesRegex(ValueError,'SHA-256'):rec.restore(ROOT,self.bundle,self.output)
        (self.bundle/'manifest.json').unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):rec.manifest(self.bundle)

    def api_fixture(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            for name in ('site.zip','manifest.json'):z.writestr(name,(self.bundle/name).read_bytes())
        raw=stream.getvalue();run,artifact,workflow,jobs=public_tests.RecoveryTests.origin(self)
        artifact['digest']='sha256:'+sha256(raw).hexdigest()
        return run,artifact,raw,workflow,jobs

    def test_verified_emergency_api_download(self):
        destination=self.base/'downloaded'
        with patch.object(rec,'api',side_effect=self.api_fixture()), \
             patch.object(rec,'historical_workflow_hash',return_value=self.m['workflow_sha256']):
            result=rec.fetch(ROOT,101,77,self.sha,destination,kind='emergency')
        self.assertEqual(result['kind'],'emergency')
        rec.restore(ROOT,destination,self.output,ROOT)

    def test_emergency_source_branch_and_kind_restrictions(self):
        fixture=list(self.api_fixture());fixture[0]['head_branch']='feature'
        with patch.object(rec,'api',side_effect=fixture):
            with self.assertRaisesRegex(ValueError,'source branch'):rec.fetch(ROOT,101,77,self.sha,self.base/'wrong-branch',kind='emergency')
        with patch.object(rec,'api',side_effect=self.api_fixture()), \
             patch.object(rec,'historical_workflow_hash',return_value=self.m['workflow_sha256']):
            with self.assertRaisesRegex(ValueError,'kind mismatch'):rec.fetch(ROOT,101,77,self.sha,self.base/'wrong-kind',kind='public')
        self.m['kind']='public'
        (self.bundle/'manifest.json').write_text(json.dumps(self.m),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'name/kind'):rec.manifest(self.bundle)

    def test_emergency_gate_cannot_bypass_authorization(self):
        with patch.dict(os.environ,{'PAGES_RELEASE_ENABLED':'false'}),patch.object(rec,'api') as api:
            with self.assertRaisesRegex(ValueError,'OFF'):rec.gate()
            api.assert_not_called()

    def test_missing_canonical_data_does_not_weaken_structure_checks(self):
        isolated=self.base/'source';shutil.copytree(ROOT/emergency.TEMPLATES,isolated/emergency.TEMPLATES)
        copied=self.base/'unsafe-site';shutil.copytree(self.base/'site',copied)
        for parent in (isolated/emergency.TEMPLATES,copied):
            p=parent/'index.html';p.write_text(p.read_text(encoding='utf-8')+'<script>bad()</script>',encoding='utf-8',newline='\n')
        with self.assertRaisesRegex(ValueError,'dependencies'):emergency.check(isolated,copied)

    def test_home_and_missing_routes_http(self):
        spec=importlib.util.spec_from_file_location('emergency_preview',ROOT/'tools/preview-release.py')
        preview=importlib.util.module_from_spec(spec);spec.loader.exec_module(preview)
        class Quiet(preview.CandidateHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(self.base/'site')))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        opener=build_opener(ProxyHandler({}))
        try:
            for route,status in [('/',200),('/missing',404),('/articles/private-capital.html',404),('/atlas/',404)]:
                try:response=opener.open(f'http://127.0.0.1:{server.server_port}{route}',timeout=5)
                except HTTPError as error:response=error
                with response:
                    self.assertEqual(response.status,status)
                    self.assertIn('data-emergency-site="true"',response.read().decode('utf-8'))
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
