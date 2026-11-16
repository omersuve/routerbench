from dataclasses import dataclass
import re

DIFFICULTIES = ('simple', 'moderate', 'hard', 'unknown')
RISKS = ('low', 'medium', 'high')
CAPABILITIES = frozenset(('text', 'code', 'tool_use', 'vision', 'web', 'hardware_debug'))
SKILL_PATTERNS = {
    'figma:figma-design-to-code': r'figma',
    'vercel:verification': r'browser',
    'pdf:pdf': r'\bpdf\b',
    'spreadsheets:Spreadsheets': r'spreadsheet',
    'reverse-engineer-anything': r'firmware',
    'vercel:deployments-cicd': r'deploy',
}

@dataclass(frozen=True)
class Model:
    id: str
    tier: int
    capabilities: frozenset
    context: int
    efforts: tuple
    local: bool = False
    available: bool = True

# These are replaceable model+runtime profiles, NOT claims of measured quality.
CATALOG = (
    Model('local', 0, frozenset(('text','code')), 4096, ('low',), True),
    Model('general', 1, frozenset(('text','code','tool_use','web')), 64000, ('low','medium','high')),
    Model('visual', 1, frozenset(('text','code','tool_use','web','vision')), 64000, ('low','medium','high')),
    Model('deep', 2, frozenset(('text','code','tool_use','web','vision')), 128000, ('medium','high')),
)

def validate_task(task):
    if not isinstance(task, dict) or set(task) != {'text','facts'}:
        raise ValueError('task requires only text and trusted facts')
    if not isinstance(task['text'], str) or not 1 <= len(task['text']) <= 16000:
        raise ValueError('task text length')
    f = task['facts']
    fields = {'environment','action','data_class','external_effect','context_tokens'}
    if not isinstance(f, dict) or set(f) != fields:
        raise ValueError('all trusted operator facts required')
    enums = {'environment': ('sandbox','local','production'),
             'action': ('read','edit','delete','deploy','send','push'),
             'data_class': ('synthetic','public','private','secret')}
    if any(f[k] not in v for k,v in enums.items()):
        raise ValueError('unknown fact value')
    if type(f['external_effect']) is not bool or type(f['context_tokens']) is not int or f['context_tokens'] < 1:
        raise ValueError('invalid fact types')

def policy(task):
    """Facts must come from a trusted host, never from the classifier/task prose.

    This is an advisory eligibility gate, NOT a sandbox or authorization token.
    There is no approval field: every actual effect is outside this experiment.
    """
    validate_task(task)
    f = task['facts']
    reasons = []
    if f['environment'] == 'production' and f['action'] != 'read':
        reasons.append('production_mutation_outside_pilot')
    if f['external_effect'] or f['action'] in ('deploy','send','push'):
        reasons.append('external_effect_outside_pilot')
    if f['data_class'] == 'secret':
        reasons.append('secret_input_prohibited')
    return {'status': 'blocked' if reasons else 'observe_only',
            'reasons': reasons, 'execute': False}

def validate_assessment(a):
    if not isinstance(a, dict) or set(a) != {'difficulty','risk','capabilities','skills'}:
        raise ValueError('invalid assessment schema')
    if a['difficulty'] not in DIFFICULTIES or a['risk'] not in RISKS:
        raise ValueError('invalid assessment enum')
    for key, allowed in [('capabilities', CAPABILITIES), ('skills', SKILL_PATTERNS)]:
        if not isinstance(a[key], list) or any(not isinstance(x,str) for x in a[key]):
            raise ValueError('invalid assessment list')
        if len(a[key]) != len(set(a[key])) or not set(a[key]) <= set(allowed):
            raise ValueError('unknown or duplicate assessment item')
    if 'text' not in a['capabilities']:
        raise ValueError('text capability required')
    return a

def assess(task):
    """Small transparent heuristic baseline, no fitted confidence score."""
    validate_task(task)
    text = task['text'].casefold()
    f = task['facts']
    if re.search(r'belirtilmedi|unclear|make it better|hangi dosya', text):
        difficulty = 'unknown'
    elif re.search(r'distributed|race|invariant|zero-downtime|100k|firmware|cross-module', text):
        difficulty = 'hard'
    elif re.search(r'spelling|one.line|off.by.one|sum\b|three durations|formula|tek|yazım|one production|single supplied', text):
        difficulty = 'simple'
    else:
        difficulty = 'moderate'
    # Risk is independent of difficulty and cannot unlock policy.
    risk = 'high' if f['environment'] == 'production' or f['external_effect'] or f['data_class'] == 'secret' else 'medium' if f['data_class'] == 'private' or f['action'] == 'delete' else 'low'
    caps = {'text'}
    if re.search(r'python|function|expression|\bsql\b|database|controller|schema|component|react|refactor|parser|test|code|queue|firmware|helper', text):
        caps.add('code')
    if f['action'] in ('edit','delete','deploy','send','push') or re.search(r'browser|repository|hardware debug', text):
        caps.add('tool_use')
    if re.search(r'screenshot|figma|render.*pages|layout', text):
        caps.add('vision')
    if re.search(r'current.*documentation|look up', text):
        caps.add('web')
    if 'firmware' in text:
        caps.add('hardware_debug')
    skills = [s for s,p in SKILL_PATTERNS.items() if re.search(p, text)]
    return {'difficulty': difficulty, 'risk':risk, 'capabilities':sorted(caps), 'skills':sorted(skills)}

def route(task, assessment=None, catalog=CATALOG, excluded=(), min_tier=0):
    p = policy(task)
    notes = []
    try:
        a = validate_assessment(assessment if assessment is not None else assess(task))
    except (ValueError, TypeError):
        # Malformed model outputs never become "simple" defaults.
        a = assess(task)
        a['difficulty'] = 'unknown'
        notes.append('invalid_assessment_escalated')
    difficulty = a['difficulty']
    tier = max(min_tier, {'simple':0, 'moderate':1, 'hard':2, 'unknown':2}[difficulty])
    effort = {'simple':'low','moderate':'medium','hard':'high','unknown':'high'}[difficulty]
    f = task['facts']
    eligible = [m for m in catalog if m.available and m.id not in excluded
                and m.tier >= tier and set(a['capabilities']) <= m.capabilities
                and f['context_tokens'] + 1024 <= m.context
                and (f['data_class'] not in ('private','secret') or m.local)]
    selected = min(eligible, key=lambda m:(m.tier, len(m.capabilities), m.id)) if eligible else None
    # A secret must never even be proposed as a model input.
    if f['data_class'] == 'secret':
        selected = None
    if selected and effort not in selected.efforts:
        selected = None
        notes.append('unsupported_effort')
    if not selected:
        notes.append('no_eligible_model_manual_escalation')
    if difficulty == 'unknown':
        notes.append('clarify_scope_before_work')
    return {'mode':'observe', 'execute':False, 'assessment':a, 'policy':p,
            'model':selected.id if selected else 'none',
            'effort':effort if selected else 'none', 'skills':a['skills'],
            'notes':notes}

def recover(task, previous, failure, attempts=1, catalog=CATALOG):
    """Pure recommendation only; never retries or runs a provider."""
    terminal = {'auth','billing','permission','policy','safety','uncertain_write'}
    if failure in terminal:
        return {'action':'stop', 'execute':False, 'reason':failure}
    if attempts >= 2:
        return {'action':'manual', 'execute':False, 'reason':'attempt_limit'}
    if failure == 'context':
        return {'action':'reduce_context', 'execute':False, 'reason':'do_not_truncate_silently'}
    if failure not in {'timeout','overload','rate_limit','unavailable','validation'}:
        return {'action':'manual', 'execute':False, 'reason':'unknown_failure'}
    current = next((m for m in catalog if m.id == previous['model']), None)
    if current is None:
        return {'action':'manual', 'execute':False, 'reason':'no_previous_route'}
    # A validation failure raises capability tier; capacity failures preserve it.
    next_route = route(task, previous['assessment'], catalog,
                       excluded=(current.id,), min_tier=current.tier + (failure=='validation'))
    return {'action':'recommend_fallback' if next_route['model']!='none' else 'manual',
            'execute':False, 'reason':failure, 'retry_delay':'respect_retry_after' if failure in ('rate_limit','overload') else None,
            'route':next_route}
