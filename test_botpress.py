import httpx
import json
import asyncio

async def test():
    url = 'http://botpress:3000/api/v1/bots/ric/converse/test999'
    payload = {'type': 'text', 'text': 'Hello'}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        data = response.json()
        
        responses = data.get('responses', [])
        print(f'Total responses: {len(responses)}')
        
        for idx, r in enumerate(responses):
            print(f'\n=== Response {idx} ===')
            print(f'Type: {r.get("type")}')
            print(f'Keys: {list(r.keys())}')
            
            if 'text' in r:
                text = r['text']
                print(f'Text: {text[:100] if len(text) > 100 else text}')
            
            if 'choices' in r:
                print(f'Choices ({len(r["choices"])}):')
                for c in r['choices']:
                    print(f'  - title: {c.get("title")}, value: {c.get("value")}')

asyncio.run(test())
