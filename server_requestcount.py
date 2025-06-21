import asyncio
import collections

class CountServer(object):
    def __init__(self):
        self.counter = collections.Counter()
        self.lock = asyncio.Lock()

    async def handle_echo(self, reader, writer):
        data = await reader.read(100)
        #来たバイト列をstr変換
        name = data.decode()

        async with self.lock:
            if self.counter[name] > 10:
                writer.write(b'-1')
                self.counter[name] = 0
            else:
                writer.write(str(self.counter[name]).encode())
                self.counter[name] += 1
        await writer.drain()
        writer.close()
        await writer.wait_closed()

async def main():
    count_server = CountServer()

    server = await asyncio.start_server(
        count_server.handle_echo, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'[server] : Serving on {addrs}')

    async with server:
        await server.serve_forever()

asyncio.run(main())
