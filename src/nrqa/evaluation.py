"""Trusted scoring boundary, using the unchanged local official FinQA scorer."""
import importlib.util
import hashlib
from pathlib import Path


def load_official(path):
    spec = importlib.util.spec_from_file_location('official_finqa', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_coverage(predictions, expected):
    ids = [p['id'] for p in predictions]
    if len(ids) != len(set(ids)) or set(ids) != set(expected) or len(ids) != len(expected):
        raise ValueError('Missing, extra or duplicate prediction IDs')


def score(predictions, expected, prediction_path, reference_path, scorer_path):
    check_coverage(predictions, expected)
    official = load_official(scorer_path)
    execution, program = official.evaluate_result(str(prediction_path), str(reference_path))
    return {'label': 'handwritten test fixtures; NOT model results', 'denominator': len(expected),
            'official_execution_fraction': execution, 'official_program_fraction': program,
            'scorer_sha256': hashlib.sha256(Path(scorer_path).read_bytes()).hexdigest()}
