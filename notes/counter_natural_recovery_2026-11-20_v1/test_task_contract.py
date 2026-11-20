#!/usr/bin/env python3
"""Offline regression for the actual frozen worker record constructors; no simulation."""
import ast,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];note=Path(__file__).resolve().parent
module=ast.parse((root/'harness/tacc_s2/worker.py').read_text());fn=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='run')
calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='dict' and any(k.arg is None and isinstance(k.value,ast.Name) and k.value.id=='task' for k in x.keywords)]
assert len(calls)==2
old=json.loads((root/'notes/counter_natural_sweep_2026-11-19_v1/plan.json').read_text());new=json.loads((note/'plan.json').read_text());old_errors=0
for call in calls:
 keys=[k.arg for k in call.keywords if k.arg is not None]
 # Execute Python's same keyword-expansion semantics, with irrelevant values stubbed.
 def invoke(task):
  args=[ast.keyword(arg=k,value=ast.Constant(None)) for k in keys]+[ast.keyword(arg=None,value=ast.Name(id='task',ctx=ast.Load()))]
  expression=ast.fix_missing_locations(ast.Expression(ast.Call(func=ast.Name(id='dict',ctx=ast.Load()),args=[],keywords=args)))
  return eval(compile(expression,'frozen_record_constructor','eval'),{'task':task})
 for task in old['tasks']:
  try:invoke(task)
  except TypeError:old_errors+=1
 for task in new['tasks']:assert invoke(task)['unit_id']==task['unit_id']
assert old_errors==len(old['tasks']) # only final record constructor has family; build-failure constructor does not
assert len(new['tasks'])==140
for a,b in zip(old['tasks'],new['tasks']):assert {k:v for k,v in a.items() if k!='family'}==b
print('PASS: reproduced old duplicate-key failure; all140 recovered tasks satisfy both frozen constructors; scientific task fields unchanged')
