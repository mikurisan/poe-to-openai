<div align="center">
  <img src="https://i.imgur.com/VU5TOfr.png" alt="Poe" height="300">
</div>

# Poe-to-Openai

This repository provides a utility to convert AI output received from **Poe** into a format compatible with the **OpenAI** API, supporting both [chat completion](https://platform.openai.com/docs/api-reference/chat/create) and [response](https://platform.openai.com/docs/api-reference/responses/create) types.


## How to start

**To download python libraries**:

```
pip install -r requirements.txt
``` 

**To start a redis**, for example using docker:

```shell
$ docker run -d --name my-redis -p 6379:6379 redis

```

You can pass your own *redis url* in `ImageManager`.

> Using redis is solely for caching locally uploaded iamges.


**To start this project**, execute in the root direcotry:

```shell
$ uvicorn app.main:app --host 0.0.0.0 --port 2026 --workers 1 --loop uvloop --http httptools
```

## How to use

**For chat completion request**, for example:

```shell
curl http://localhost:2026/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <Your_Poe_Key>" \
  -d '{
    "model": "gpt-4.1",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

**For response request**, for example:

```shell
curl http://localhost:2026/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <Your_Poe_Key>" \
  -d '{
    "model": "gpt-4.1",
    "input": "Tell me a three sentence bedtime story about a unicorn."
  }'
```

## Reference

[Create chat completion](https://platform.openai.com/docs/api-reference/chat/create)

[Create a model response](https://platform.openai.com/docs/api-reference/responses/create)