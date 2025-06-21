# serverを起動要
# blocking関数を並列処理しnon-blocking関数は非同期処理
# loop.run_in_executor(executor, non-bfunc, 10) は
# （※ executor = concurrent.futures.ProcessPoolExecutor())
#非同期コードから同期処理を非同期っぽく使うための橋渡し

import asyncio
import time

# __await__によりawait obj 可能
class AwaitableClass(object):
    def __init__(self, name):
        self.name = name

    def __await__(self):
        return self.request_server().__await__()  # <- 非同期関数を呼び出してその__await__を返す

    async def request_server(self):
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
        print(f"[client] : {self.name} sending request")
        writer.write(self.name.encode())
        await writer.drain()
        data = await reader.read()
        print(f"[client] : {self.name} received raw: {data!r}")
        return int(data.decode())

# async for に対応したクラス(__aiter__, __anext__)
class AsyncIterator(object):
    def __init__(self, name):
        self.name = name

    #iteratorを初期化し自分自身を返す
    def __aiter__(self):
        return self

# 非同期イテレータでawait使えるようにするためにasync defにする
    # 各ループでAwaitable Classによって非同期アクセスし結果を返す。
    async def __anext__(self):
        data = await AwaitableClass(self.name)
        if data < 0:
            print('[__anext__]StopIter')
            raise StopAsyncIteration
        return data

# async withのクロージャのようなもの
class AsyncContextManager(object):
    def __init__(self, name):
        self.enter = 'enter'
        self.ac = AsyncIterator(name)
        self.exit = 'exit'

    # with句に入った時
    async def __aenter__(self):
        print(self.enter)
        await asyncio.sleep(3)
        return self.ac

    # with句を抜けた時
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(self.exit)
        await asyncio.sleep(3)

# 【Future】
# - 低レベルの非同期処理
# - executorから返る（＝非同期関数ではなく、blocking関数の結果）
# - .add_done_callback() などでコールバックも可能

# 【Task】
# - async関数を「スケジューラに登録して」実行する高レベルAPI
# - asyncio.create_task() で生成
# - Futureを継承しているので、awaitやcallbackも使える

# 　今どきの asyncio では Task を中心に書くのが主流。
#   ただし、run_in_executor() などで外部処理を非同期化したいときは Future を使う。

#blocking関数
import concurrent.futures

def blocking_task(name):
    print(f'block {name}')
    time.sleep(1)
    return f'done {name}'

async def combo_main():
    results = []

    # 非同期でデータ取得
    async with AsyncContextManager('job') as aiter:
        async for result in aiter:
            results.append(result)
        print(f'results = {results}')

    # 非同期取得データに対して、同期の重い処理を並列実行
    def done_callback(future):
        print(f'[done] {future.result()}')

    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as executor:

        futures = []
        for r in results:
            f = loop.run_in_executor(executor, blocking_task, f'block {r}')
            f.add_done_callback(done_callback)
            futures.append(f)

        await asyncio.gather(*futures)

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('spawn')
    asyncio.run(combo_main())
