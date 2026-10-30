"""Deterministic local retrieval/extractive grounding baseline, not an LLM RAG."""
import argparse
import json
import re
import time
import uuid
from pathlib import Path


def tokens(text):
    return set(re.findall(r"[a-z0-9가-힣]+",text.lower()))


def latest_documents(documents):
    latest={}
    versions={}
    for doc in documents:
        required={'id','version','tags','text'}
        if (not isinstance(doc,dict) or not required.issubset(doc)
                or not isinstance(doc['id'],str) or not doc['id'].strip()
                or type(doc['version']) is not int or doc['version'] < 1
                or not isinstance(doc['text'],str) or not doc['text'].strip()
                or not isinstance(doc['tags'],list)
                or not all(isinstance(tag,str) and tag.strip() for tag in doc['tags'])):
            raise ValueError('invalid document')
        identity=(doc['id'],doc['version'])
        if identity in versions and versions[identity]!=doc:
            raise ValueError('conflicting document versions')
        versions[identity]=doc
        old=latest.get(doc['id'])
        if old is None or doc['version']>old['version']:latest[doc['id']]=doc
    return list(latest.values())


def answer(question, documents, events=None):
    trace=uuid.uuid4().hex; started=time.perf_counter();query=tokens(question)
    docs=latest_documents(documents)
    scored=sorted([(len(query & tokens(' '.join(d['tags']))),d) for d in docs],key=lambda x:x[0],reverse=True)
    enough=bool(scored and scored[0][0]>=2 and (len(scored)==1 or scored[0][0]>scored[1][0]))
    result={'status':'abstain','answer':'근거가 충분하지 않습니다.','citations':[]}
    if enough:
        d=scored[0][1]
        result={'status':'supported','answer':d['text'],'citations':[{'id':d['id'],'version':d['version'],'quote':d['text']}]}
    result['trace_id']=trace
    if events is not None:
        events.append({'trace_id':trace,'span_id':trace,'parent_id':None,'stage':'retrieve-and-ground',
                       'duration_ms':(time.perf_counter()-started)*1000,'candidate_count':len(docs),
                       'top_overlap':scored[0][0] if scored else 0,'status':result['status']})
    return result


def is_grounded(result, documents):
    current={(d['id'],d['version']):d['text'] for d in latest_documents(documents)}
    if not isinstance(result,dict):return False
    if result.get('status')=='abstain':
        return result.get('citations')==[] and result.get('answer')=='근거가 충분하지 않습니다.'
    citations=result.get('citations')
    if (result.get('status')!='supported' or not isinstance(result.get('answer'),str)
            or not result['answer'].strip() or not isinstance(citations,list) or len(citations)!=1):
        return False
    citation=citations[0]
    if (not isinstance(citation,dict) or not isinstance(citation.get('id'),str)
            or type(citation.get('version')) is not int or not isinstance(citation.get('quote'),str)):
        return False
    identity=(citation['id'],citation['version'])
    return identity in current and current[identity]==citation['quote']==result['answer']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('question');p.add_argument('--output',default='.runs/grounding.json');args=p.parse_args()
    docs=json.loads(Path(__file__).with_name('fixtures').joinpath('documents.json').read_text());events=[]
    result=answer(args.question,docs,events)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'result':result,'trace':events,'grounded':is_grounded(result,docs)},ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False))
