import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('candidate_check',Path(__file__).with_name('check.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Checks(unittest.TestCase):
    def setUp(self):
        self.address='0x'+'a'*40
        self.local={'chainId':20261001,'genesis':'0xabc','syncing':False,'peers':3,'height':100,'heightAfter':102,'commonHash':'0xdef','validators':[]}
        self.reference={'chainId':20261001,'genesis':'0xabc','height':102,'commonHash':'0xdef'}
    def assess(self):return module.assess(self.local,self.reference,self.address,'0xabc')
    def test_healthy_candidate_requires_admission(self):
        r=self.assess();self.assertTrue(r['technicalPreflightPassed']);self.assertEqual(r['admission'],'pending-governance')
    def test_membership_is_separate_from_health(self):
        self.local['validators']=[self.address.upper()];self.local['syncing']={};r=self.assess();self.assertFalse(r['technicalPreflightPassed']);self.assertEqual(r['admission'],'active-on-chain')
    def test_wrong_chain_genesis_and_fork_fail(self):
        self.local.update(chainId=1,genesis='0xwrong',commonHash='0xfork');self.assertEqual(len(self.assess()['issues']),3)
    def test_stalled_lagging_isolated_node_fails(self):
        self.local.update(heightAfter=100,peers=0);self.reference['height']=110;self.assertEqual(len(self.assess()['issues']),3)
    def test_reference_wrong_chain_fails(self):
        self.reference['chainId']=1;self.assertFalse(self.assess()['technicalPreflightPassed'])

if __name__=='__main__':unittest.main()
