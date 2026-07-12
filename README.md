# WolfTg

Official Python SDK for the **WolfTg API**.

WolfTg provides a simple and modern interface for interacting with the WolfTg API from Python applications. The library includes both synchronous and asynchronous clients with fully typed request models powered by Pydantic.

## Features

* Official WolfTg API client
* Synchronous and asynchronous interfaces
* Type-safe request models
* Built-in request validation using Pydantic
* Configurable HTTP sessions
* Connection pooling
* Easy integration into existing Python projects

## Requirements

* Python 3.12 or newer

## Installation

```bash
pip install WolfTg
```

## Quick Start

### Synchronous Client

```python
from WolfTg import Client
from WolfTg.methods import GetBalance

with Client(api_key="YOUR_API_KEY") as client:
    result = client(GetBalance())
    print(result)

```

### Asynchronous Client

```python
import asyncio

from WolfTg import AsyncClient
from WolfTg.methods import GetBalance


async def main():
    client = AsyncClient(api_key="YOUR_API_KEY")

    await client.start()

    try:
        result = await client(GetBalance())
        print(result)
    finally:
        await client.stop()


asyncio.run(main())
```

## Configuration

The client can be configured with custom options such as:

* API key
* Request timeout
* HTTP session implementation
* Custom HTTP settings

Refer to the API documentation for all available options.

## Documentation

* API Documentation: https://wolf-tg.com/api/docs

## Support

If you encounter a bug or would like to request a feature, please open an issue on GitHub.

Repository:

https://github.com/eeeob/WolfTg

## License

This project is licensed under the MIT License (or the license included with this repository).
