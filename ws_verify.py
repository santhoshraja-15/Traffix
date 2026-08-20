import asyncio
import json
import sys

async def listen():
    try:
        import websockets
        uri = 'ws://127.0.0.1:8000/api/simulation/demo-phase2/ws'
        async with websockets.connect(uri, open_timeout=5) as ws:
            for i in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                edges = data.get('traffic', [])
                tick = data['tick']
                source = data.get('source', 'unknown')
                model = data.get('model', 'unknown')
                print(f'Tick={tick} source={source} model={model} edges={len(edges)}')
                if edges:
                    e = edges[0]
                    print(f'  edge_id={e["edge_id"]} risk={e["risk_score"]} cost={e["edge_cost"]} cong={e["congestion"]}')
                sys.stdout.flush()
    except Exception as ex:
        print(f'WS error: {ex}')

if __name__ == '__main__':
    asyncio.run(listen())
