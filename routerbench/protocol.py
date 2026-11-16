"""Versioned assessment schema and frozen phase 2 semantic rubric."""
import hashlib
import json
import math
from pathlib import Path
from .routing import validate_assessment

RUBRIC = json.loads(Path(__file__).with_name('rubric.json').read_text())

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def prompt(task):
    definitions = {'instructions': RUBRIC['PREFIX'], 'difficulty': RUBRIC['DIFF'],
                   'risk': RUBRIC['RISK'], 'capabilities': RUBRIC['CAPS'], 'skills': RUBRIC['SKILLS']}
    enums = {'difficulty': list(RUBRIC['DIFF']), 'risk': list(RUBRIC['RISK']),
             'capabilities': ['text', *RUBRIC['CAPS']], 'skills': list(RUBRIC['SKILLS'])}
    return ('Return one JSON object with exactly difficulty, risk, capabilities, skills. Allowed values: '
            + json.dumps(enums) + '. Choose one difficulty and one risk string; capabilities and skills are arrays of unique allowed strings. '
            'Include the literal string "text" in capabilities. Include every other required capability and all relevant skills; use [] for no skills. '
            'Do not return explanations or descriptions as values. Shape example (not the answer): '
            '{"difficulty":"moderate","risk":"low","capabilities":["text","code","tool_use"],"skills":[]}. '
            'Semantic definitions: ' + json.dumps(definitions, ensure_ascii=False)
            + '\nTask: ' + json.dumps(task, ensure_ascii=False))

def decode_jev(response):
    """Decode a recorded System One response; certainty is NOT correctness."""
    answers = response.get('answers')
    expected = {'difficulty', 'risk', *('cap_' + x for x in RUBRIC['CAPS']),
                *('skill_' + str(i) for i in range(len(RUBRIC['SKILLS'])))}
    if not isinstance(response.get('model'), str) or not isinstance(answers, dict) or set(answers) != expected:
        raise ValueError('incomplete Jev response')
    result = {'capabilities': ['text'], 'skills': []}
    certainties = []
    for key, answer in answers.items():
        if not isinstance(answer, dict):
            raise ValueError('answer object required')
        if key in ('difficulty', 'risk'):
            allowed = RUBRIC['DIFF' if key == 'difficulty' else 'RISK']
            probabilities = answer.get('probabilities')
            if answer.get('type') != 'choice' or not isinstance(probabilities, dict) or set(probabilities) != set(allowed):
                raise ValueError('invalid choice schema')
            values = list(probabilities.values())
            if any(type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1 for p in values) or abs(sum(values) - 1) > .001:
                raise ValueError('invalid distribution')
            choice = answer.get('choice')
            if choice not in probabilities or probabilities[choice] != max(values):
                raise ValueError('invalid choice')
            result[key] = choice
            certainties.append(probabilities[choice])
        else:
            p = answer.get('noul')
            if answer.get('type') != 'noul' or type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError('invalid Noul')
            certainties.append(max(p, 1 - p))
            if p >= .5:
                if key.startswith('cap_'):
                    result['capabilities'].append(key[4:])
                else:
                    result['skills'].append(list(RUBRIC['SKILLS'])[int(key[6:])])
    result['capabilities'].sort()
    result['skills'].sort()
    return validate_assessment(result), min(certainties)
