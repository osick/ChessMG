from timeit import timeit
from pycmg import moves

def test_average(data):
    rounds=1_000_000
    for fen in data:
        testmoves=moves(fen, fen.split(" ")[1]=="w")
        movenumber=len(testmoves)//3
        result = timeit(stmt=f"p.moves()", setup=f'from pycmg import Pos; p=Pos("{fen}")', number=rounds)
        print(f"SUCCESS: NPS={rounds*movenumber//result:_} ({rounds*movenumber:_} moves) {fen=}")

if __name__=='__main__':
    data =[
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1",
        "1Bn5/1n6/2q5/8/8/8/8/1K5k w - - 0 1",
        "r3kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "8/k1P5/8/1K6/8/8/8/8 w - - 0 1",]
    
    test_average(data=data)
