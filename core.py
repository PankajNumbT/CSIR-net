"""Question-bank validation and CSIR Mathematical Sciences scoring.

No Streamlit dependency: this module is also used by import tools and tests.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TRACK_TOPICS = {
    'Mathematics': [
        'Real Analysis', 'Complex Analysis', 'Linear Algebra', 'Abstract Algebra',
        'Topology', 'Number Theory', 'Multivariable Calculus',
        'Ordinary Differential Equations', 'Partial Differential Equations',
        'Numerical Analysis', 'Calculus of Variations', 'Integral Equations',
        'Functional Analysis', 'Discrete Mathematics', 'Geometry',
        'Classical Mechanics', 'Operations Research', 'Aptitude', 'Unclassified',
    ],
    'Statistics': [
        'Probability', 'Probability Distributions', 'Statistical Inference',
        'Stochastic Processes', 'Regression and Multivariate Analysis',
        'Sampling and Design of Experiments', 'Aptitude', 'Unclassified',
    ],
}
MARKS = {'A': 2.0, 'B': 3.0, 'C': 4.75}
PENALTIES = {'A': 0.5, 'B': 0.75, 'C': 0.0}
LABELS = ('A', 'B', 'C', 'D')


class BankError(ValueError):
    pass


@dataclass(frozen=True)
class Question:
    id: str
    source_type: str
    paper_id: str | None
    question_number: int | None
    part: str
    track: str
    topic: str
    difficulty: str
    prompt: str
    options: dict[str, str]
    correct_options: list[str]
    hints: list[str]
    solution: str
    theory: str
    similar_questions: list[dict[str, str]]
    review_status: str
    source_note: str
    answer_source: str
    page: int | None = None
    image: str | None = None
    classification_status: str = 'reviewed'

    @property
    def marks(self) -> float:
        return MARKS[self.part]

    @property
    def answer_type(self) -> str:
        return 'Multiple correct' if self.part == 'C' else 'Single correct'


def validate_question(item: dict[str, Any], paper_ids: set[str]) -> Question:
    if not isinstance(item, dict):
        raise BankError('Every question must be an object.')
    required = [f for f in Question.__dataclass_fields__ if f not in ('page', 'image', 'classification_status')]
    missing = [f for f in required if f not in item]
    if missing:
        raise BankError('Missing fields: ' + ', '.join(missing))
    unknown = set(item) - set(Question.__dataclass_fields__)
    if unknown:
        raise BankError('Unknown fields: ' + ', '.join(sorted(unknown)))
    strings = ['id', 'source_type', 'part', 'track', 'topic', 'difficulty', 'prompt',
               'solution', 'theory', 'review_status', 'source_note', 'answer_source']
    for field in strings:
        if not isinstance(item[field], str) or not item[field].strip():
            raise BankError(f'{field} must be a nonempty string.')
    if item['source_type'] not in ('original_practice', 'official_exam'):
        raise BankError('source_type must be original_practice or official_exam.')
    if item['part'] not in MARKS:
        raise BankError('part must be A, B, or C.')
    if item['track'] not in ('Mathematics', 'Statistics', 'Shared'):
        raise BankError('Unknown track.')
    if item['track'] == 'Shared':
        if item['topic'] != 'Aptitude' or item['part'] != 'A':
            raise BankError('Shared questions must be Part A Aptitude.')
    elif item['topic'] not in TRACK_TOPICS[item['track']]:
        raise BankError('Topic does not belong to the selected track.')
    if item['topic'] == 'Aptitude' and item['track'] != 'Shared':
        raise BankError('Use the Shared track for Aptitude.')
    if item['difficulty'] not in ('Easy', 'Moderate', 'Hard'):
        raise BankError('difficulty must be Easy, Moderate, or Hard.')
    if item['review_status'] not in ('draft', 'reviewed', 'source_issue'):
        raise BankError('review_status must be draft, reviewed, or source_issue.')
    opts = item['options']
    if not isinstance(opts, dict) or set(opts) != set(LABELS):
        raise BankError('Four options labelled A, B, C, D are required.')
    if any(not isinstance(v, str) or not v.strip() for v in opts.values()):
        raise BankError('Every option must have text.')
    answers = item['correct_options']
    if not isinstance(answers, list) or (not answers and item['review_status'] != 'source_issue') or any(a not in LABELS for a in answers):
        raise BankError('correct_options must be a nonempty list of A-D labels.')
    if len(answers) != len(set(answers)):
        raise BankError('Repeated correct options are not allowed.')
    if item['part'] != 'C' and len(answers) != 1 and item['review_status'] != 'source_issue':
        raise BankError('Parts A and B require exactly one correct option.')
    if not isinstance(item['hints'], list) or len(item['hints']) < 2 or any(
        not isinstance(h, str) or not h.strip() for h in item['hints']
    ):
        raise BankError('At least two nonempty progressive hints are required.')
    if not isinstance(item['similar_questions'], list) or not item['similar_questions']:
        raise BankError('At least one worked similar question is required.')
    for example in item['similar_questions']:
        if not isinstance(example, dict) or set(example) != {'prompt', 'solution'} or any(
            not isinstance(v, str) or not v.strip() for v in example.values()
        ):
            raise BankError('Each similar question requires prompt and solution text.')
    qn = item['question_number']
    if item['source_type'] == 'official_exam':
        if item['paper_id'] not in paper_ids:
            raise BankError('An official question must reference a known paper_id.')
        if type(qn) is not int or not 1 <= qn <= 120:
            raise BankError('Official question_number must be an integer from 1 to 120.')
        expected_part = 'A' if qn <= 20 else ('B' if qn <= 60 else 'C')
        if item['part'] != expected_part:
            raise BankError(f'Question {qn} belongs to Part {expected_part}.')
        if item['review_status'] == 'reviewed' and len(item['answer_source'].strip()) < 10:
            raise BankError('Reviewed exam questions need a specific answer-key/reference citation.')
    elif item['paper_id'] is not None or qn is not None:
        raise BankError('Original practice questions must not carry exam provenance.')
    if item.get('page') is not None and (type(item['page']) is not int or item['page'] < 1):
        raise BankError('page must be a positive integer or null.')
    return Question(**item)


def parse_bank(data: Any, paper_ids: set[str]) -> list[Question]:
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('questions'), list):
        raise BankError('Expected {"schema_version": 1, "questions": [...]}')
    parsed: list[Question] = []
    ids: set[str] = set()
    sources: set[tuple[str, int]] = set()
    for i, item in enumerate(data['questions']):
        try:
            q = validate_question(item, paper_ids)
            if q.id in ids:
                raise BankError(f'Duplicate id: {q.id}')
            if q.source_type == 'official_exam':
                source = (q.paper_id, q.question_number)
                if source in sources:
                    raise BankError('Repeated paper/question-number pair.')
                sources.add(source)
            ids.add(q.id)
            parsed.append(q)
        except (BankError, TypeError) as exc:
            raise BankError(f'Question {i + 1}: {exc}') from exc
    return parsed


def read_bank(path: Path, paper_ids: set[str]) -> list[Question]:
    try:
        return parse_bank(json.loads(path.read_text(encoding='utf-8')), paper_ids)
    except (OSError, json.JSONDecodeError) as exc:
        raise BankError(f'Could not read {path.name}: {exc}') from exc


def load_project_bank(root: Path, include_drafts: bool = True) -> list[Question]:
    """Load the original inventory and independently authored paper packs."""
    papers = json.loads((root / 'data/papers.json').read_text(encoding='utf-8'))
    paper_ids = {p['id'] for p in papers}
    raw = json.loads((root / 'data/raw_questions.json').read_text(encoding='utf-8'))
    source_ids = {r['id'] for r in raw}
    questions = source_questions(raw)
    files = [root / 'data/exam_questions.json']
    files += sorted((root / 'data/completed_papers').glob('*.json'))
    if include_drafts:
        files += sorted((root / 'data/ai_drafts').glob('*.json'))
    for path in files:
        packs = read_bank(path, paper_ids)
        if any(q.id not in source_ids for q in packs):
            raise BankError(f'{path.name} references a question absent from the source inventory.')
        questions = overlay_solutions(questions, packs)
    return questions


def merge_banks(existing: list[Question], incoming: list[Question], paper_ids: set[str]) -> list[Question]:
    """Reject collisions rather than silently replacing existing study material."""
    return parse_bank({'schema_version': 1, 'questions': [asdict(q) for q in existing + incoming]}, paper_ids)


def export_bank(questions: list[Question]) -> str:
    return json.dumps({'schema_version': 1, 'questions': [asdict(q) for q in questions]}, indent=2, ensure_ascii=False)


def grade(q: Question, selected: list[str]) -> dict[str, Any]:
    if q.review_status != 'reviewed' or not q.correct_options:
        raise BankError('This question has no reviewed answer yet; your selection can be saved without a score.')
    chosen = set(selected)
    if not chosen or not chosen <= set(LABELS):
        raise BankError('Choose an answer before submitting.')
    if q.part != 'C' and len(chosen) != 1:
        raise BankError('Choose exactly one option for this question.')
    correct = chosen == set(q.correct_options)
    return {'correct': correct, 'points': q.marks if correct else (-PENALTIES[q.part] if PENALTIES[q.part] else 0.0),
            'maximum': q.marks, 'selected': sorted(chosen)}


def filter_questions(questions: list[Question], track: str, topic: str = 'All topics',
                     paper_id: str = 'all', source_type: str = 'all',
                     difficulty: list[str] | None = None, part: str = 'All parts',
                     bookmarked: set[str] | None = None) -> list[Question]:
    allowed = set(difficulty or [])
    return [q for q in questions if q.track in (track, 'Shared', 'Unclassified')
            and (topic == 'All topics' or q.topic == topic)
            and (paper_id == 'all' or q.paper_id == paper_id)
            and (source_type == 'all' or q.source_type == source_type)
            and (not allowed or q.difficulty in allowed)
            and (part == 'All parts' or q.part == part)
            and (bookmarked is None or q.id in bookmarked)]


def shuffled_ids(questions: list[Question], seed: int) -> list[str]:
    ids = [q.id for q in questions]
    random.Random(seed).shuffle(ids)
    return ids


def bank_digest(questions: list[Question]) -> str:
    return hashlib.sha256(export_bank(questions).encode()).hexdigest()[:16]


def coverage(questions: list[Question], papers: list[dict]) -> list[dict]:
    ready = Counter(q.paper_id for q in questions if q.source_type == 'official_exam' and q.review_status == 'reviewed')
    drafts = Counter(q.paper_id for q in questions if q.source_type == 'official_exam' and q.review_status == 'draft')
    issues = Counter(q.paper_id for q in questions if q.source_type == 'official_exam' and q.review_status == 'source_issue')
    available = Counter(q.paper_id for q in questions if q.source_type == 'official_exam')
    return [{'paper_id': p['id'], 'paper': p['label'], 'ready': ready[p['id']],
             'draft': drafts[p['id']], 'explained_issues': issues[p['id']], 'available': available[p['id']],
             'pending': available[p['id']] - ready[p['id']] - drafts[p['id']] - issues[p['id']], 'expected': 120,
             'missing': 120 - available[p['id']]} for p in papers]


def source_questions(raw: list[dict]) -> list[Question]:
    """Internal source inventory, deliberately separate from solved bank imports."""
    result = []
    for item in raw:
        result.append(Question(
            id=item['id'], source_type='official_exam', paper_id=item['paper_id'],
            question_number=item['question_number'], part=item['part'],
            track=item['track'], topic=item['topic'], difficulty='Unrated',
            prompt='Read the original question and numbered options below.',
            options={k: f'Option {i} in the question image' for i,k in enumerate(LABELS,1)},
            correct_options=[], hints=[], solution='', theory='', similar_questions=[],
            review_status='pending', source_note='Original attached paper; candidate responses are not an answer key.',
            answer_source='', page=item['page'], image=item['image'],
            classification_status=item.get('classification_status','pending')))
    return result


def overlay_solutions(sources: list[Question], solved: list[Question]) -> list[Question]:
    """Only replace the exact source ID and paper/number; preserve the original image."""
    from dataclasses import replace
    by_id = {q.id:q for q in sources}
    for q in solved:
        old = by_id.get(q.id)
        if old:
            if (old.paper_id, old.question_number, old.part) != (q.paper_id,q.question_number,q.part):
                raise BankError('Solution provenance does not match its source question.')
            if old.review_status == 'reviewed' and q.review_status != 'reviewed':
                continue
            by_id[q.id] = replace(q, image=old.image)
        else:
            by_id[q.id] = q
    return list(by_id.values())


def validate_progress(data: Any, question_ids: set[str]) -> dict:
    """Imported scores are recomputed in the app, never trusted from a file."""
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise BankError('This is not a NET Studio progress file.')
    saved = data.get('bookmarks', [])
    responses = data.get('responses', {})
    if not isinstance(saved, list) or not isinstance(responses, dict):
        raise BankError('Invalid progress structure.')
    if any(not isinstance(x, str) for x in saved):
        raise BankError('Invalid bookmark id.')
    clean = {}
    for qid, response in responses.items():
        if qid not in question_ids:
            continue
        if not isinstance(response, dict) or not isinstance(response.get('selected'), list):
            raise BankError('Invalid saved response.')
        choices = response['selected']
        if any(not isinstance(x, str) or x not in LABELS for x in choices):
            raise BankError('Invalid saved answer.')
        clean[qid] = {'selected': sorted(set(choices)), 'submitted': bool(response.get('submitted')),
                      'assisted': bool(response.get('assisted'))}
    return {'bookmarks': [x for x in saved if x in question_ids], 'responses': clean}
