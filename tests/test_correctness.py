import json

from pycmg import perft, ChessMoveGenerator

def test_correctness():
    with open("testdata.json","r") as fh: testdata=json.load(fh)
    for pos in testdata:
        nodes = perft(pos["fen"], pos["depth"])
        print(f"{'  ERROR: ' if nodes != pos['nodes'] else 'SUCCESS: '}depth={pos['depth']:<2} Expected={pos['nodes']:<8} Result={nodes:<8} remark:{pos['remark'][:17]+('...' if len(pos['remark'])>15 else''):<21} pos['fen']={pos['fen']:<15}")

if __name__ =="__main__":
    test_correctness()
