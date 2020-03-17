import discord

async def quote_handler(bot:discord.Client, message:discord.Message, command:list, devRole:discord.Role) -> None:
    try:
        if command[1] == "inspirobot":
            response = await bot.inspirobot.get_quote()
            e = discord.Embed(colour=0xff00e7, title="Quote from Inspirobot")
            e.set_image(url=response)
            
            await message.channel.send(embed=e)
    # NO NO NO NO, WHY U DO DIS???
    except Exception as e:
        await message.channel.send(f"**{bot.izzymojis['izzyangry']} IZZY**\nHey {devRole.mention} There was an error.\n```\n{e}\n```")