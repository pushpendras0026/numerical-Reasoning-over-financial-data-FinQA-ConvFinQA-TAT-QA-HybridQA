"""Portable dataset paths with explicit, nonsecret environment overrides."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT_ENV = {'hybridqa':'NRQA_HYBRIDQA_QUESTIONS','multihiertt':'NRQA_MULTIHIERTT_ROOT'}


def source_path(config):
    key=SOURCE_ROOT_ENV.get(config['dataset'])
    override=os.environ.get(key,'') if key else ''
    return ((Path(override)/Path(config['source']).name) if override else (ROOT/config['source'])).resolve()


def corpus_candidates(config):
    override=os.environ.get('NRQA_HYBRIDQA_CORPUS')
    if override:return [Path(override).resolve()]
    corpus=config.get('corpus')
    if corpus and corpus!='auto':return [(ROOT/corpus).resolve()]
    paths=config.get('corpus_candidates',['data/WikiTables-WithLinks','../HybridQA/WikiTables-WithLinks','../WikiTables-WithLinks'])
    return [(ROOT/path).resolve() for path in paths]


def corpus_path(config):
    candidates=corpus_candidates(config)
    for path in candidates:
        if (path/'tables_tok').is_dir() and (path/'request_tok').is_dir():return path
    # Return the explicit expected path so missing resources can be reported precisely.
    return candidates[0] if candidates else None
