"""Real bounded data-file repairs. Only trusted validators run, never model code."""
import configparser
import csv
import io
import json
from pathlib import Path
import tempfile
import time

CASES = (
    ('config.json', '{"service":"demo","retry_count":0,"timeout_seconds":30,"enabled":true}\n',
     'Set retry_count to 3. Preserve every other field.', 'json', {'service':'demo','retry_count':3,'timeout_seconds':30,'enabled':True}),
    ('rows.csv', 'name,amout\nAda,12\nİpek,9\n',
     'Correct the header typo amout to amount. Preserve names, values and row order.', 'csv', [{'name':'Ada','amount':'12'},{'name':'İpek','amount':'9'}]),
    ('README.md', '# Demo\nRead the [guide](guide.md).\n',
     'The guide exists at docs/guide.md. Fix only the relative link target.', 'text', '# Demo\nRead the [guide](docs/guide.md).\n'),
    ('app.ini', '[service]\nenabled = no\nmode = preview\n',
     'Enable the service. Preserve its mode and section name.', 'ini', {'enabled':True,'mode':'preview'}),
    ('events.jsonl', '{"id":1,"text":"α"}\n{"id":2,"text":"β"}\n{"id":1,"text":"later"}\n',
     'Deduplicate by id, retaining the first record in original order. Preserve its fields.', 'jsonl', [{'id':1,'text':'α'},{'id':2,'text':'β'}]),
    ('versions.json', '{"versions":["2.10","2.2","1.9"],"channel":"stable"}\n',
     'Sort versions numerically by major then minor, ascending. Preserve channel.', 'json', {'versions':['1.9','2.2','2.10'],'channel':'stable'}),
)

def check(kind, content, expected):
    if kind == 'json':
        return json.loads(content) == expected
    if kind == 'csv':
        reader = csv.DictReader(io.StringIO(content))
        return reader.fieldnames == ['name','amount'] and list(reader) == expected
    if kind == 'jsonl':
        return [json.loads(line) for line in content.splitlines() if line.strip()] == expected
    if kind == 'ini':
        parser = configparser.ConfigParser()
        parser.read_string(content)
        return parser.sections() == ['service'] and set(parser['service']) == {'enabled','mode'} and parser.getboolean('service','enabled') == expected['enabled'] and parser['service']['mode'] == expected['mode']
    return content == expected

def execute(client):
    records = []
    for filename, original, instruction, kind, expected in CASES:
        start = time.perf_counter()
        error = None
        usage = {}
        with tempfile.TemporaryDirectory(prefix='routerbench-work-') as directory:
            target = Path(directory) / filename
            target.write_text(original, encoding='utf-8')
            (Path(directory) / 'docs').mkdir()
            (Path(directory) / 'docs/guide.md').write_text('Synthetic guide\n')
            try:
                # The client receives only this string, never filesystem paths or a tool.
                response, _, usage = client.complete('Repair the following synthetic data file. Return JSON with exactly one key "content" whose string is the complete corrected file. No code, markdown fences, shell, tools or filenames.\n'
                    + instruction + '\nInput file content:\n' + target.read_text())
                if not isinstance(response, dict) or set(response) != {'content'} or not isinstance(response['content'], str) or len(response['content'].encode()) > 16384:
                    raise ValueError('bounded content object required')
                target.write_text(response['content'], encoding='utf-8')
                passed = check(kind, target.read_text(), expected)
                if kind == 'text':
                    passed = passed and (Path(directory) / 'docs/guide.md').is_file()
            except Exception as exc:
                passed = False
                error = type(exc).__name__
            records.append({'case':filename,'passed':passed,'error_type':error,
                            'latency_ms':(time.perf_counter()-start)*1000,'usage':usage})
    return {'n':len(records),'passed':sum(r['passed'] for r in records),'records':records,
            'metadata':getattr(client,'metadata',{}),'paid_calls':0,
            'scope':'Data-file repairs in fresh temporary directories; no generated source execution, tools, agent integration, network except opted-in loopback inference.'}
