import json

from pycmg import perft

def test_correctness():
    success= True
    with open("testdata.json","r") as fh: testdata=json.load(fh)
    for pos in testdata:
        nodes = perft(pos["fen"], pos["depth"])
        success = success and (nodes == pos['nodes'])
        print(f"{'  ERROR: ' if nodes != pos['nodes'] else 'SUCCESS: '}depth={pos['depth']:<2} Expected={pos['nodes']:<8} Result={nodes:<8} remark:{pos['remark'][:17]+('...' if len(pos['remark'])>15 else''):<21} pos['fen']={pos['fen']:<15}")
    return success
if __name__ =="__main__":
    success = test_correctness()
    if success:
        print ("TEST PASSED")
        exit(0)
    else:
        print ("TEST FAILED")
        exit(1)