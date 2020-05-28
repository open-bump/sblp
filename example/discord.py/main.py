# This is a python example for integrating SBLP status updates in a bump command.
# I'm not actually a python dev and this was my first thing I've ever done in python because Stefan wouldn't know how to do it
# So if there are bad design choices, I'm sorry :3

import asyncio
import json

import discord
import jishaku
from discord.ext import commands

import config

bot = commands.AutoShardedBot(max_messages=5000, command_prefix=config.prefix)
bot.load_extension("jishaku")


class MessageType():
    REQUEST = 'REQUEST'
    START = 'START'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'


@bot.event
async def on_ready():
    print("Logged in as %s!" % (bot.user.name))
    for guild in bot.guilds:
        print("- %s (%s)" % (guild.name, guild.id))
    await bot.change_presence(activity=discord.Game(name="discord.py"))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.bot:
        return

    await bot.process_commands(message)


def get_sblp_post_channel():
    return bot.get_channel(config.sblpPostChannel)


async def sblp_post_bump_request(guild, channel, user):
    sblp = get_sblp_post_channel()
    return await sblp.send(json.dumps({'type': 'REQUEST', 'guild': guild, 'channel': channel, 'user': user}, indent=2))


def sblp_parse_payload(content):
    try:
        payload = json.loads(content)
        return payload
    except:
        pass


@bot.command()
async def bump(ctx):
    # The timeout after when pending SBLP entities are marked as timed out
    timeout = 60

    # Start bumping...
    bumpMessage = await ctx.message.channel.send('Bumping...')

    sblpEntities = {}
    timeouted = False
    updateCallback: callable = None

    async def nested():
        # Post request
        requestMessage = await sblp_post_bump_request(ctx.guild.id.__str__(), ctx.channel.id.__str__(), ctx.author.id.__str__())

        # Define on message function
        def on_message(message):
            author = message.author
            sblp = get_sblp_post_channel()
            if(message.channel.id == sblp.id and author != bot.user):
                payload = sblp_parse_payload(message.content)
                if(payload and 'type' in payload and 'response' in payload and payload['response'] == requestMessage.id.__str__()):
                    # Save payload
                    if(payload['type'] == MessageType.START):
                        if(author.id in sblpEntities):
                            asyncio.create_task(message.channel.send(
                                '[DEBUG] Ignoring a started payload from an already-in-progress bot'))
                            return
                        sblpEntities[author.id] = payload
                    elif(payload['type'] == MessageType.FINISHED):
                        if(not author.id in sblpEntities):
                            asyncio.create_task(message.channel.send(
                                '[DEBUG] Ignoring a finished payload from a not-in-progress bot'))
                            return
                        sblpEntities[author.id] = payload
                    elif(payload['type'] == MessageType.ERROR):
                        sblpEntities[author.id] = payload
                    else:
                        return

                    # Execute update callback
                    if(updateCallback):
                        asyncio.create_task(updateCallback())

        # Await messages
        try:
            await bot.wait_for('message', check=on_message, timeout=timeout)
        except:
            pass
        timeouted = True
        if(updateCallback):
            asyncio.create_task(updateCallback())

    asyncio.create_task(nested())

    # Fininished bumping, output other bot's states
    def make_embed():
        embed = discord.Embed(color=0x33ff33)
        embed.description = 'Bumping finished!'
        value = ''
        providers = sblpEntities.keys()
        for provider in providers:
            lastPayload = sblpEntities[provider]
            state = 'Unknown'
            if(lastPayload['type'] == MessageType.START):
                if(not timeouted):
                    state = 'Bumping...'
                else:
                    state = 'Timeout'
            if(lastPayload['type'] == MessageType.FINISHED):
                if('amount' in lastPayload):
                    state = 'Successfully bumped [%s servers]' % lastPayload['amount']
                else:
                    state = 'Successfully bumped'
            if(lastPayload['type'] == MessageType.ERROR):
                # You can improve this error handling using the passed error code
                if(lastPayload['message']):
                    state = 'Error: %s' % lastPayload['message']
                else:
                    state = 'Error'
            value += "<@%s>: `%s`\n" % (provider, state)
        if(not len(providers)):
            value = '*No other bump bots*'
        embed.add_field(name='Other bump bots', value=value, inline=False)
        return embed

    await bumpMessage.edit(embed=make_embed())

    async def update_callback():
        # Suggestion: Add some kind of check to see whether the content actually changed before editing the message
        await bumpMessage.edit(embed=make_embed())
    updateCallback = update_callback

bot.run(config.token)
