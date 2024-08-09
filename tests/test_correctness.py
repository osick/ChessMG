import json
import os
import sys

from pycmg import perft

def test_correctness():
    verbose = (len(sys.argv)>=2 and sys.argv[1]=="verbose")

    success= True
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata.json"),"r") as fh: testdata=json.load(fh)
    for pos in testdata:
        nodes = perft(pos["fen"], pos["depth"])
        success = success and (nodes == pos['nodes'])
        if verbose: print(f"{'  ERROR: ' if nodes != pos['nodes'] else 'SUCCESS: '}depth={pos['depth']:<2} Expected={pos['nodes']:<8} Result={nodes:<8} remark:{pos['remark'][:17]+('...' if len(pos['remark'])>15 else''):<21} pos['fen']={pos['fen']:<15}")
    return success
if __name__ =="__main__":
    print("\nTest Case ",__file__,sep="")
    success = test_correctness()

    {print ("TEST PASSED") and exit(0)} if success else {print ("TEST FAILED") and exit(1)}