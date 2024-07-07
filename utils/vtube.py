import asyncio, pyvts,base64
VOICE_LEVEL = 5
VOICE_PARAMETER = "MouthOpen"

plugin_info = {
    "plugin_name": "Waifu",
    "developer": "TumblerWarren",
    "authentication_token_path": "./pyvts_token.txt"

}


async def main():
    myvts = pyvts.vts(plugin_info=plugin_info)


    await myvts.connect()
    await myvts.request_authenticate_token()  # get token
    await myvts.request_authenticate()  # use token

    level = [0.2, 0.4, 0.5, 0.6, 0.3, 0.2, 0.67, 0.5, 0.2, 0.4, 0.6, 0.8, 0.3, 0.9, 0.3, 0.2, 0.1, 0.34, 0.6, 0.8, 0.5, 0.3, 0.86, 0.34, 0.35, 0.63, 0.72, 0.31, 0.12]
    level.append(0)

    for mem in level:
        await myvts.request(myvts.vts_request.requestSetParameterValue(parameter=VOICE_PARAMETER, value=mem))
        await asyncio.sleep(1 / 30)

if __name__ == "__main__":
    asyncio.run(main())