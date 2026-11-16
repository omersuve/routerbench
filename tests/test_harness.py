import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from routerbench.adapters import Observation, Replay, Rules, Local, NoRedirect
from routerbench.io import load_inputs, verified_run, write_new, file_hash
from routerbench.protocol import digest, decode_jev, RUBRIC
from routerbench.runner import predict
from routerbench.scoring import score, wilson
from routerbench.routing import route, recover
from routerbench.execution import execute, CASES
from routerbench.__main__ import main

ROOT = Path(__file__).resolve().parents[1]

def task(**changes):
    facts = {'environment':'sandbox','action':'read','data_class':'synthetic','external_effect':False,'context_tokens':1000}
    facts.update(changes)
    return {'text':'Fix a spelling error in supplied text.','facts':facts}

def assessment(**changes):
    value={'difficulty':'simple','risk':'low','capabilities':['text'],'skills':[]};value.update(changes);return value

class HarnessTests(unittest.TestCase):
    def setup_files(self, directory):
        directory=Path(directory);inputs=directory/'inputs.json';labels=directory/'labels.json'
        write_new(inputs,[{'id':'one','task':task()}])
        write_new(labels,{'inputs_sha256':file_hash(inputs),'labels':[{'id':'one','task_sha256':digest(task()),'expected':{**assessment(),'model':'local','effort':'low'}}]})
        return inputs,labels
    def test_observe_scoring_and_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);out=Path(d)/'run'
            predict(inputs,out,Rules());manifest,rows=verified_run(out)
            self.assertFalse(rows[0]['execute']);self.assertFalse(rows[0]['route']['execute'])
            result=score(out,labels);self.assertEqual(result['metrics']['route_exact']['correct'],1)
            self.assertEqual(result['coverage'],1);self.assertEqual(manifest['paid_calls'],0)
    def test_prediction_refuses_combined_labels(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'in.json';write_new(path,[{'id':'x','task':task(),'expected':assessment()}])
            with self.assertRaises(ValueError):load_inputs(path)
    def test_duplicate_inputs_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'in.json';write_new(path,[{'id':'x','task':task()}]*2)
            with self.assertRaises(ValueError):load_inputs(path)
    def test_no_prediction_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,_=self.setup_files(d);out=Path(d)/'run';predict(inputs,out,Rules())
            with self.assertRaises(FileExistsError):predict(inputs,out,Rules())
    def test_receipt_detects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);out=Path(d)/'run';predict(inputs,out,Rules())
            with (out/'predictions.jsonl').open('a') as f:f.write('{}\n')
            with self.assertRaises(ValueError):score(out,labels)
    def test_wrong_labels_dataset_refused(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);out=Path(d)/'run';predict(inputs,out,Rules())
            data=json.loads(labels.read_text());data['inputs_sha256']='wrong';labels.write_text(json.dumps(data))
            with self.assertRaises(ValueError):score(out,labels)
    def test_task_label_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);out=Path(d)/'run';predict(inputs,out,Rules())
            data=json.loads(labels.read_text());data['labels'][0]['task_sha256']='wrong';labels.write_text(json.dumps(data))
            with self.assertRaises(ValueError):score(out,labels)
    def test_missing_replay_is_unobserved_not_correct(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);record=Path(d)/'replay.jsonl';record.write_text('')
            out=Path(d)/'run';predict(inputs,out,Replay(record,'jev'));result=score(out,labels)
            self.assertEqual(result['coverage'],0);self.assertEqual(result['statuses'],{'missing':1})
            self.assertIsNone(result['metrics']['risk']['observed_accuracy'])
            self.assertIsNone(result['metrics']['risk']['accuracy'])
            self.assertEqual(result['metrics']['risk']['yield'],0)
    def test_threshold_abstains_without_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);record=Path(d)/'replay.jsonl'
            record.write_text(json.dumps({'task_sha256':digest(task()),'assessment':assessment(),'certainty':.6})+'\n')
            out=Path(d)/'run';predict(inputs,out,Replay(record),.7)
            _,rows=verified_run(out);self.assertIsNone(rows[0]['route']);self.assertEqual(rows[0]['status'],'abstain')
            self.assertEqual(score(out,labels)['events']['uncertain'],['one'])
    def test_no_confidence_is_not_one(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);out=Path(d)/'run';predict(inputs,out,Rules(),.7)
            self.assertEqual(score(out,labels)['statuses'],{'abstain':1})
    def test_invalid_replay_has_no_guessed_difficulty(self):
        with tempfile.TemporaryDirectory() as d:
            inputs,labels=self.setup_files(d);record=Path(d)/'replay.jsonl';record.write_text(json.dumps({'task_sha256':digest(task()),'assessment':{}})+'\n')
            out=Path(d)/'run';predict(inputs,out,Replay(record));result=score(out,labels)
            self.assertEqual(result['statuses'],{'invalid':1});self.assertEqual(result['metrics']['difficulty']['correct'],0)
    def test_wilson_zero_and_perfect(self):
        self.assertIsNone(wilson(0,0));self.assertLess(wilson(24,24)[0],1);self.assertGreater(wilson(0,24)[1],0)
    def test_cli_does_not_accept_labels_for_predict(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):main(['predict','--inputs','x','--output','y','--labels','z'])
    def test_paid_adapter_without_replay_refused(self):
        with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main(['predict','--inputs','x','--output','y','--adapter','jev']),2)
    def test_reference_originals_preserved(self):
        self.assertEqual(len(json.loads((ROOT/'datasets/phase1/original.json').read_text())),28)
        self.assertEqual(len(json.loads((ROOT/'datasets/phase2/original.json').read_text())),24)
        for phase in ('phase1','phase2'):
            manifest=json.loads((ROOT/f'datasets/{phase}/manifest.json').read_text())
            self.assertEqual(file_hash(ROOT/f'datasets/{phase}/original.json'),manifest['original_sha256'])

class RoutingTests(unittest.TestCase):
    def test_policy_ignores_injected_low_risk(self):
        out=route(task(environment='production',action='delete'),assessment())
        self.assertEqual(out['policy']['status'],'blocked');self.assertFalse(out['execute'])
    def test_risk_does_not_determine_effort(self):
        out=route(task(environment='production',action='edit'),assessment(risk='high',capabilities=['text','tool_use']))
        self.assertEqual(out['effort'],'low')
    def test_private_cloud_refused(self):
        out=route(task(data_class='private'),assessment(difficulty='hard'))
        self.assertEqual(out['model'],'none')
    def test_unsupported_capability_not_dropped(self):
        self.assertEqual(route(task(),assessment(capabilities=['text','hardware_debug']))['model'],'none')
    def test_context_headroom(self):
        self.assertEqual(route(task(context_tokens=8000),assessment())['model'],'general')
    def test_permission_failure_not_bypassed(self):
        self.assertEqual(recover(task(),route(task()),'permission')['action'],'stop')
    def test_missing_facts_fail_closed(self):
        t=task();del t['facts']['action']
        with self.assertRaises(ValueError):route(t)

class LocalBoundaryTests(unittest.TestCase):
    def test_explicit_opt_in_before_network(self):
        with patch('urllib.request.OpenerDirector.open') as network:
            with self.assertRaises(ValueError):Local('fixture')
            network.assert_not_called()
    def test_redirect_refused(self):
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_remote_model_name_refused(self):
        with self.assertRaises(ValueError):Local('fixture-cloud',True)
    def test_installed_model_required_no_pull(self):
        with patch.object(Local,'_api',return_value={'models':[]}) as api:
            with self.assertRaises(ValueError):Local('missing',True)
            api.assert_called_once_with('/api/tags')
    def test_local_generation_has_bounds_and_no_tools(self):
        with patch.object(Local,'_api',side_effect=[{'models':[{'name':'fixture'}]},{'thinking':{'values':[False]}}]):client=Local('fixture',True)
        with patch.object(client,'_api',return_value={'done':True,'done_reason':'stop','response':'{"ok":true}'}) as api:
            result,_,_=client.complete('fixture')
            self.assertEqual(result,{'ok':True});body=api.call_args.args[1]
            self.assertEqual(body['options']['num_predict'],512);self.assertEqual(body['options']['num_ctx'],4096)
            self.assertNotIn('tools',body);self.assertNotIn('format',body)

class DecoderTests(unittest.TestCase):
    def response(self):
        answers={}
        for key,levels in [('difficulty',RUBRIC['DIFF']),('risk',RUBRIC['RISK'])]:
            chosen=next(iter(levels));answers[key]={'type':'choice','choice':chosen,'probabilities':{k:float(k==chosen) for k in levels}}
        for key in RUBRIC['CAPS']:answers['cap_'+key]={'type':'noul','noul':0}
        for i in range(len(RUBRIC['SKILLS'])):answers['skill_'+str(i)]={'type':'noul','noul':0}
        return {'model':'recorded-model','answers':answers}
    def test_valid_atomic_response(self):
        a,p=decode_jev(self.response());self.assertEqual(a,assessment());self.assertEqual(p,1)
    def test_uncertainty_distinct_from_class(self):
        r=self.response();r['answers']['cap_vision']['noul']=.5
        a,p=decode_jev(r);self.assertIn('vision',a['capabilities']);self.assertEqual(p,.5)
    def test_malformed_probabilities_rejected(self):
        for value in (float('nan'),-.1,1.2):
            r=self.response();r['answers']['cap_vision']['noul']=value
            with self.assertRaises(ValueError):decode_jev(r)
    def test_missing_question_rejected(self):
        r=self.response();del r['answers']['cap_web']
        with self.assertRaises(ValueError):decode_jev(r)

class ExecutionTests(unittest.TestCase):
    def test_real_file_validation_with_bounded_data(self):
        class Fixture:
            def __init__(self):self.i=0
            def complete(self,prompt):
                name,original,instruction,kind,expected=CASES[self.i];self.i+=1
                if kind=='csv':content='name,amount\nAda,12\nİpek,9\n'
                elif kind=='ini':content='[service]\nenabled=yes\nmode=preview\n'
                elif kind=='jsonl':content='\n'.join(json.dumps(x) for x in expected)+'\n'
                elif kind=='text':content=expected
                else:content=json.dumps(expected)
                return {'content':content},0,{}
        self.assertEqual(execute(Fixture())['passed'],6)
    def test_code_or_wrong_shape_never_executes(self):
        class Fixture:
            def complete(self,prompt):return {'code':'raise RuntimeError'},0,{}
        self.assertEqual(execute(Fixture())['passed'],0)

class ScientificChecks(unittest.TestCase):
    def test_high_risk_error_is_separate_from_policy(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);t=task(environment='production',action='edit',external_effect=True)
            write_new(d/'inputs.json',[{'id':'risky','task':t}])
            expected={**assessment(risk='high',capabilities=['text','tool_use']),'model':'general','effort':'low'}
            write_new(d/'labels.json',{'inputs_sha256':file_hash(d/'inputs.json'),'labels':[{'id':'risky','task_sha256':digest(t),'expected':expected}]})
            (d/'response.jsonl').write_text(json.dumps({'task_sha256':digest(t),'assessment':assessment()})+'\n')
            predict(d/'inputs.json',d/'run',Replay(d/'response.jsonl'))
            result=score(d/'run',d/'labels.json')
            self.assertEqual(result['events']['high_risk_as_low'],['risky'])
            self.assertEqual(result['events']['capability_miss'],['risky'])
            self.assertEqual(verified_run(d/'run')[1][0]['policy']['status'],'blocked')
    def test_new_set_is_disjoint_and_label_hashes_frozen(self):
        import hashlib
        new=ROOT/'datasets/phase3'
        manifest=json.loads((new/'manifest.json').read_text())
        self.assertEqual(file_hash(new/'inputs.json'),manifest['inputs_sha256'])
        self.assertEqual(file_hash(new/'labels.json'),manifest['labels_sha256'])
        rows=load_inputs(new/'inputs.json');self.assertEqual(len(rows),32)
        old={digest(r['task']) for phase in ('phase1','phase2') for r in load_inputs(ROOT/f'datasets/{phase}/inputs.json')}
        self.assertTrue(all(digest(r['task']) not in old for r in rows))
    def test_score_requires_sealed_complete_run(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);(path/'predictions.jsonl').write_text('')
            with self.assertRaises(FileNotFoundError):verified_run(path)
    def test_jev_cannot_be_named_over_generic_assessment(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'response.jsonl';file.write_text(json.dumps({'task_sha256':digest(task()),'assessment':assessment()})+'\n')
            self.assertEqual(Replay(file,'jev').predict(task()).status,'invalid')
    def test_existing_execution_output_refused_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result.json';p.write_text('{}')
            with patch('routerbench.__main__.Local') as client,contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['execute','--model','fixture','--allow-local','--output',str(p)]),2)
                client.assert_not_called()

class ReleaseTests(unittest.TestCase):
    def make_root(self,d):
        from routerbench.release import FILES,DIRECTORIES
        root=Path(d)
        for name in FILES:
            (root/name).parent.mkdir(parents=True, exist_ok=True)
            (root/name).write_text('[project]\nname="fixture"\ndependencies=[]\n' if name=='pyproject.toml' else 'safe fixture\n')
        for name in DIRECTORIES:(root/name).mkdir()
        return root
    def test_export_excludes_ignored_material_and_is_deterministic(self):
        from routerbench.release import export_release
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'root';p.mkdir();root=self.make_root(p)
            (root/'archive').mkdir();(root/'archive/private.txt').write_text('excluded fixture')
            a=export_release(root,Path(d)/'one.zip');b=export_release(root,Path(d)/'two.zip')
            self.assertEqual(a['archive_sha256'],b['archive_sha256'])
            with zipfile.ZipFile(Path(d)/'one.zip') as z:
                self.assertFalse(any('archive/' in n for n in z.namelist()))
                self.assertIn('routerbench-0.1.0/.github/workflows/ci.yml', z.namelist())
    def test_personal_path_and_credential_patterns_fail_audit(self):
        from routerbench.release import audit_release
        with tempfile.TemporaryDirectory() as d:
            root=self.make_root(d)
            (root/'README.md').write_text('/'+'Users'+'/private-example/data')
            self.assertFalse(audit_release(root)['passed'])
            (root/'README.md').write_text('sk-'+'a'*24)
            self.assertFalse(audit_release(root)['passed'])
    def test_unshipped_markdown_link_refused(self):
        from routerbench.release import audit_release
        with tempfile.TemporaryDirectory() as d:
            root=self.make_root(d);(root/'README.md').write_text('[old](archive/old.md)')
            self.assertFalse(audit_release(root)['passed'])
    def test_symlink_refused(self):
        from routerbench.release import audit_release
        with tempfile.TemporaryDirectory() as d:
            root=self.make_root(d);(root/'routerbench/link.py').symlink_to(root/'LICENSE')
            with self.assertRaises(ValueError):audit_release(root)
