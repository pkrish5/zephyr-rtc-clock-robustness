#!/usr/bin/env python3
"""Synthetic file-packaging checks only: no compiler, Renode, SSH or Slurm calls."""
import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('setup.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
class Packaging(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='s2-synthetic-packaging-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.old=self.root/'old';self.new=self.root/'new'
        self.repo.mkdir();self.new.mkdir();(self.repo/'paper').mkdir();(self.repo/'paper/DESIGN.md').write_text('synthetic design fixture')
        self.image=self.root/'image';self.image.write_bytes(b'NOT A REAL CONTAINER')
        self.unit=dict(id='synthetic-case',board_id='synthetic-board',wall_timeout_seconds=1)
        self.board=dict(nominal=32000,minimum=17000,maximum=47000)
        old=dict(output_relative='results/old',units=[self.unit],boards={'synthetic-board':self.board})
        save(self.old/'plan.json',old)
        b=self.old/'results/old/builds/synthetic-case';(b/'build/zephyr').mkdir(parents=True)
        (b/'build.log').write_text('synthetic build log, no compiler ran')
        self.elf=b/'build/zephyr/zephyr.elf';self.elf.write_bytes(b'NOT EXECUTABLE: SYNTHETIC ELF FIXTURE')
        (b/'build/zephyr/.config').write_text('synthetic config')
        self.record=dict(status='built',log_sha256=sha(b/'build.log'),
            build_products_sha256={'zephyr/.config':sha(b/'build/zephyr/.config')},
            elf_path=str(self.elf.relative_to(self.old)),elf_sha256=sha(self.elf),slurm_job_id='synthetic-no-job')
        save(b/'build_record.json',self.record)
        self.plan=dict(production_authorized=True,conditional_approval_evidence={'report':{'all_15_accepted':True},'qualification_plan_sha256':sha(self.old/'plan.json')},
            image_sha256=sha(self.image),design_sha256=sha(self.repo/'paper/DESIGN.md'),input_sha256={},code_sha256={},
            output_relative='results/new',units=[self.unit],boards={'synthetic-board':dict(self.board)},tasks=[{'index':0},{'index':1}])
        self.seal()
    def seal(self):
        save(self.new/'plan.json',self.plan);(self.new/'plan.sha256').write_text(sha(self.new/'plan.json')+'  plan.json\n')
    def invoke(self):
        return subprocess.run([sys.executable,str(SCRIPT),'--bundle',str(self.new),'--previous',str(self.old),'--repo',str(self.repo),'--image',str(self.image)],
            env=dict(os.environ,SLURM_JOB_PARTITION='normal',SLURM_JOB_ID='synthetic-no-job'),capture_output=True,text=True)
    def test_copies_immutable_record_and_retains_its_elf_pointer(self):
        original_hash=sha(self.elf);r=self.invoke();self.assertEqual(r.returncode,0,r.stderr)
        copied=json.loads((self.new/'results/new/builds/synthetic-case/build_record.json').read_text())
        self.assertEqual(copied,self.record);self.assertEqual(sha(self.new/copied['elf_path']),original_hash)
        self.assertEqual(sha(self.elf),original_hash)
        lines=(self.new/'results/new/launcher/primary/jobfile').read_text().splitlines()
        self.assertEqual(len(lines),2);self.assertTrue(lines[0].endswith(' 0'));self.assertTrue(lines[1].endswith(' 1'))
    def test_rejects_image_drift_before_copying(self):
        self.image.write_bytes(b'CHANGED SYNTHETIC IMAGE');self.assertNotEqual(self.invoke().returncode,0)
        self.assertFalse((self.new/'results/new/builds').exists())
    def test_rejects_changed_board_clock_before_copying(self):
        self.plan['boards']['synthetic-board']['nominal']=40000;self.seal()
        self.assertNotEqual(self.invoke().returncode,0);self.assertFalse((self.new/'results/new/launcher').exists())
if __name__=='__main__':unittest.main()
