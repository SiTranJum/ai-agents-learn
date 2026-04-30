"""
Demo: Python decorator execution timing

Shows that decorators execute at FILE LOAD TIME,
not when server.run() is called.
"""

print("=" * 60)
print("STEP 1: File starts loading")
print("=" * 60)


class Server:
    def __init__(self, name):
        self._handlers = {}
        print(f"  Server created: {name}")

    def list_tools(self):
        print(f"  >> list_tools() factory called, returning decorator")
        def decorator(func):
            print(f"  >> decorator executing, registering: {func.__name__}")
            self._handlers["tools/list"] = func
            return func
        return decorator

    def call_tool(self):
        print(f"  >> call_tool() factory called, returning decorator")
        def decorator(func):
            print(f"  >> decorator executing, registering: {func.__name__}")
            self._handlers["tools/call"] = func
            return func
        return decorator


server = Server("demo")

print("\n" + "=" * 60)
print("STEP 2: Decorators execute NOW (file loading)")
print("=" * 60)

@server.list_tools()
async def list_tools():
    return ["tool1", "tool2"]

@server.call_tool()
async def call_tool(name, arguments):
    return f"result of {name}"

print(f"\n  Registered handlers: {list(server._handlers.keys())}")

print("\n" + "=" * 60)
print("STEP 3: server.run() has NOT been called yet!")
print("  But handlers are ALREADY registered.")
print("  server.run() only starts LISTENING for requests.")
print("=" * 60)

print("\n" + "=" * 60)
print("STEP 4: Simulate client request (function executes NOW)")
print("=" * 60)

import asyncio

async def simulate():
    handler = server._handlers["tools/list"]
    result = await handler()
    print(f"  tools/list result: {result}")

    handler = server._handlers["tools/call"]
    result = await handler("query_nutrition", {"food": "apple"})
    print(f"  tools/call result: {result}")

asyncio.run(simulate())

print("\n" + "=" * 60)
print("TIMELINE:")
print("  1. File loads     -> Server() created")
print("  2. File loads     -> @decorators register handlers")
print("  3. server.run()   -> starts listening (handlers already ready)")
print("  4. Client request -> handler function actually executes")
print("=" * 60)
