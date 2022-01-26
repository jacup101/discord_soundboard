import random

import discord
from discord import FFmpegPCMAudio, SlashCommandGroup
from discord.ext.tasks import loop
import asyncio
from youtube_dl import YoutubeDL
from discord.commands import slash_command  # Importing the decorator that makes slash commands.
from discord.ext import commands
from discord.commands import Option
import json
import discord.utils as discUtils
import youtube_dl
import uuid


cancelEmote = "❌"
fastForwardEmote = "⏩"
emoteJSON = None
currentlyActiveGuilds = {}

randomJoin = False
randomTrigger = "🔄"

intents = discord.Intents.all()
intents.members = True

bot = discord.Bot(intents=intents)

helpTrigger = "❓"
helpMessage = []

soundboardTrigger = "🎵"
testing_servers = [772655489871511572, 933121643881066516]
queueEnabled = False
queueTrigger = "🇶"

musicJSON = {}
musicList = []
musicURLs = []

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':   'True'}
ytdl = YoutubeDL(YDL_OPTIONS)
FFMPEG_OPTIONS = {'before_options': '-reconnect 1   -reconnect_streamed 1 -reconnect_delay_max 5',  'options': '-vn'}

# TODO: Make queue accept only songitems, not emoteitems, thru type field
class GuildPlayer:
    voice = None
    guildID = None
    queue = []
    toSkip = False

    def __init__(self, guildID, voice):
        self.guildID = guildID
        self.voice = voice
        self.queue = []

    def get_voice(self):
        return self.voice

    def is_queue_empty(self):
        return len(self.queue) == 0

    def add_item_to_queue(self, item):
        self.queue.append(item)

    def add_items_to_queue(self, item, amount):
        for i in range(amount):
            self.add_item_to_queue(item)

    def pop_item_from_queue(self):
        return self.queue.pop(0)

    def get_to_skip(self):
        return self.toSkip

    def set_skip(self):
        self.toSkip = True

    def reset_skip(self):
        self.toSkip = False

class Item:
    name = "default"
    fileName = "default.mp3"
    type = "EmoteItem"

    def __init__(self, name, fileName, type):
        self.name = name
        self.fileName = fileName
        self.type = type

    def __str__(self):
        return "{name}".format(name=self.name)



@bot.event
async def on_connect():
    global emoteJSON, helpMessage
    await bot.register_commands()
    activity = discord.Game(name="Nemo me impune lacessit", type=3)
    await bot.change_presence(status=discord.Status.idle,activity=activity)
    print("Bot is online\nReading Data")
    with open("emote_to_mp3.json") as f:
        json_data = json.load(f)
        emoteJSON = json_data["list"]
        helperString = ""
        for listItem in emoteJSON:
            helperString += "{emote} - {description}\n".format(emote=listItem["emote"], description=listItem["description"])
        helpMessage.append(helperString)


@bot.event
async def on_message(message):
    global emoteJSON, cancelEmote, currentlyActiveGuilds, randomJoin, queueEnabled, helpMessage
    if message.author.bot:
        return

    guildID = message.guild.id
    if message.content.count(cancelEmote) > 0:
        guildPlayer = currentlyActiveGuilds[guildID]
        if guildPlayer is not None:
            voice = guildPlayer.get_voice()
            await voice.disconnect()
            currentlyActiveGuilds[guildID] = None
        return

    if message.content.count(queueTrigger) > 0:
        queueEnabled = not queueEnabled
        return

    if message.content.count(helpTrigger) > 0:
        await message.channel.send(helpMessage[0])

    if message.content.count(soundboardTrigger) > 0:
        await create_soundboard(emoteJSON, message)
        return
    await check_for_emote(emoteJSON, guildID, message, message.author, message_get_count, None)


@bot.event
async def on_raw_reaction_add(payload):
    global bot, emoteJSON, currentlyActiveGuilds, cancelEmote
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    author = guild.get_member(payload.user_id)
    message = await channel.fetch_message(payload.message_id)
    if author.bot:
        return

    guildID = guild.id

    if payload.emoji.name.count(cancelEmote) > 0:
        guildPlayer = currentlyActiveGuilds[guildID]
        if guildPlayer is not None:
            voice = guildPlayer.get_voice()
            await voice.disconnect()
            currentlyActiveGuilds[guildID] = None
        return

    if payload.emoji.name.count(fastForwardEmote) > 0:
        guildPlayer = currentlyActiveGuilds[guildID]
        if guildPlayer is not None:
            guildPlayer.set_skip()
        return

    await check_for_emote(emoteJSON, guildID, message, author, react_get_count, payload)





# Payload not necessary here, but passed in anyway
async def message_get_count(listItem, message, payload):
    return message.content.count(listItem['emote'])


# Message not necessary here, but passed in anyway
async def react_get_count(listItem, message, payload):
    if "yes" in listItem['is_custom']:

        countItem = payload.emoji.name.count(listItem['name'])
    else:
        countItem = payload.emoji.name.count(listItem['emote'])
    return countItem


async def add_reactions(list, message, start, end):
    length = end - start + 1
    for i in range(length):
        item = list[start+i]
        emote = item["emote"]
        await message.add_reaction(emote)


async def create_soundboard(list, message):
    num = len(list)
    numReact = 20
    numLists = int(num / numReact) + 1
    for i in range(numLists):
        multiple = i * numReact
        if i < numLists - 1:

            msg = await message.channel.send("** **")
            await add_reactions(list, msg, multiple, multiple + numReact - 1)
        else:
            msg = await message.channel.send("** **")
            await add_reactions(list, msg, multiple, num - 1)


async def check_for_emote(list, guildID, message, author, method, payload):
    global currentlyActiveGuilds, queueEnabled

    print(message.content)
    for listItem in list:
        countItem = await method(listItem, message, payload)
        if countItem > 0:
            if 'yes' in listItem['is_random']:
                fileName = "music/" + random.choice(listItem["random"])
            else:
                fileName = "music/" + listItem['audio']
            found = True
            limit = int(listItem['limit'])
            finalItem = listItem
            break
        # print("{emote} had count {count}".format(emote=listItem['emote'], count=countItem))


    # Check if the guild is empty (or has never been accessed before)
    isActive = False
    try:
        check = currentlyActiveGuilds[guildID]
        if check is not None:
            isActive = True
    except:
        # Do nothing
        isActive = False
    if isActive is False:
        if countItem > 0 and author.voice:
            channel = author.voice.channel
            await join_voice(channel, guildID, finalItem, fileName, countItem, limit)
            await run_voice(guildID)

        elif countItem > 0 and not author.voice:
            guild = message.guild
            for channel in guild.voice_channels:
                print(channel)
                if len(channel.members) > 0:
                    await join_voice(channel, guildID, finalItem, fileName, countItem, limit)
                    await run_voice(guildID)
                    break
    elif isActive is True and queueEnabled is True:
        if countItem > 0:
            guildPlayer = await read_value(guildID)
            item = Item(finalItem["name"], fileName, "EmoteItem")
            guildPlayer.add_items_to_queue(item, min(finalItem["limit"], countItem))


async def read_value(guildID):
    # Assumes that Guild ID is already a key in the dict, since it should never be accessed otherwise
    # Todo: Check if Guild ID is a key
    global currentlyActiveGuilds
    return currentlyActiveGuilds[guildID]


async def set_none(guildID):
    global currentlyActiveGuilds
    currentlyActiveGuilds[guildID] = None


async def join_voice(channel, guildID, listItem, fileName, countItem, limit):
    try:
        voice = await channel.connect()
        guildPlayer = GuildPlayer(guildID, voice)
        item = Item(listItem["name"], fileName, "EmoteItem")
        guildPlayer.add_items_to_queue(item, min(countItem, limit))
        # guildPlayer.add_item_to_queue(YoutubeItem("https://www.youtube.com/watch?v=7HgJIAUtICU"))
        currentlyActiveGuilds[guildID] = guildPlayer
    except:
        return


async def join_voice_music(channel, guildID, item):
    try:
        voice = await channel.connect()
        guildPlayer = GuildPlayer(guildID, voice)
        guildPlayer.add_item_to_queue(item)
        currentlyActiveGuilds[guildID] = guildPlayer
    except:
        return



async def run_voice(guildID):
    guildQueue = await read_value(guildID)
    while guildQueue.is_queue_empty() is False:
        voice = guildQueue.get_voice()
        item = guildQueue.pop_item_from_queue()

        if voice is not None:
            if isinstance(item, Item):
                try:
                    player = voice.play(FFmpegPCMAudio(item.fileName))
                    while voice.is_playing():
                        guildQueue = await read_value(guildID)
                        if guildQueue.get_to_skip() is True:
                            voice.stop()
                            guildQueue.reset_skip()
                        await asyncio.sleep(0)
                except:
                    print("Apparent disconnect")
            guildQueue = await read_value(guildID)
        else:
            break
    guildQueue = await read_value(guildID)
    voice = guildQueue.get_voice()
    if voice is not None:
        print("Should DC Here")
        await voice.disconnect(force=True)
        await set_none(guildID)
    else:
        print("Apparently disconnected manually, exiting")



async def get_songs(ctx):
    global musicList
    """Returns a list of colors that begin with the characters entered so far."""
    return [song for song in musicList if song.startswith(ctx.value.lower())]



class Music(commands.Cog):


    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'songs/default.mp3'
    }

    def __init__(self, bot):
        global musicList, musicURLs, musicJSON
        self.bot = bot
        with open("songlist.json") as f:
            musicJSON = json.load(f)
        musicList = musicJSON["list"]
        musicURLs = musicJSON["url"]
        self.option = Option(str, "Hello", autocomplete=discUtils.basic_autocomplete(musicList))

    @slash_command(guild_ids=[772655489871511572,348566046653022209])
    async def add(
            self,
            ctx,
            title: Option(str, "Title of the song"),
            link: Option(str, "Youtube Link"),
    ):
        global musicList, musicURLs, musicJSON
        """Add a song thru a youtube link"""
        #TODO: Don't allow for duplicates
        if title in musicList or title in "list" or title in "url" or link in musicURLs:
            await ctx.respond("Song already exists, will not add")
        else:
            await ctx.respond("Attempting to add {title}. Please note: I can only download one song at a time, so wait until I say success before trying again uwu".format(title=title))
            unique_filename = str(uuid.uuid4())
            try:
                await self.download_song(unique_filename, link, title)
                print("Song downloaded")
            except:
                await ctx.respond("Error downloading song, please try again")
                return
            try:
                await self.save_song(title, f"songs/{unique_filename}.mp3", link)
                print("Song saved")
            except:
                await ctx.respond("Error saving to songlist, please try again")
                return
            print("Success")
            await ctx.respond("Success!")

    @slash_command(name="play", guild_ids=[772655489871511572,348566046653022209])
    async def play(
            self,
            ctx: discord.ApplicationContext,
            song: Option(str, "Song Name", autocomplete=discUtils.basic_autocomplete(get_songs))

    ):
        if song not in musicList:
            await ctx.respond("Song does not exist :(")
            return

        author = ctx.author
        guildID = ctx.guild_id
        isActive = False
        item = Item(musicJSON[song]["title"], musicJSON[song]["location"], "SongItem")
        try:
            check = currentlyActiveGuilds[guildID]
            if check is not None:
                isActive = True
        except:
            # Do nothing
            isActive = False
        if isActive is False:
            if author.voice:
                channel = author.voice.channel
                await ctx.respond(f"{song} now playing!")
                await join_voice_music(channel, guildID, item)
                await run_voice(guildID)


            elif not author.voice:
                guild = ctx.guild
                for channel in guild.voice_channels:
                    print(channel)
                    if len(channel.members) > 0:
                        await ctx.respond(f"{song} now playing!")
                        await join_voice_music(channel, guildID, item)
                        await run_voice(guildID)
                        break


        elif isActive is True:
            guildPlayer = await read_value(guildID)
            guildPlayer.add_items_to_queue(item, 1)
            await ctx.respond(f"{song} added to queue!")

    async def save_song(self, title, filename, url):
        global musicList, musicURLs, musicJSON
        musicList.append(title)
        musicURLs.append(url)
        musicJSON[title] = {"title": title, "location": filename, "url": url}
        musicJSON["list"] = musicList
        musicJSON["url"] = musicURLs
        with open("songlist.json", "w") as f:
            json.dump(musicJSON, f)

    async def download_song(self, filename, url, title):
        self.ydl_opts['outtmpl'] = "songs/{fname}.mp3".format(fname=filename)

        try:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
        except:
            raise Exception("Something went wrong")





bot.add_cog(Music(bot))
bot.run("Your token here")

