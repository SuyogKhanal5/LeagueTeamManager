# Import Statements
import random
import numpy as np
import os.path as path
import sqlite3
import discord
from discord import app_commands
import TourneyClasses
from TourneyClasses import Team, Tournament, Match
import pickle

# Get token from text file
token = ""

with open("token.txt") as f:
    token = f.readline()

# Connect to Database
dataFolder = "data/guildData/serverInfo/"
dbpath = dataFolder + "main.db"

mainDB = sqlite3.connect(dbpath)
cursor = mainDB.cursor()

# if database doesn't already exist, create it
if not path.isfile(dbpath):
    cursor.execute("CREATE TABLE servers(guildId, serverName, original_channel, team1, team2, players, channel1, channel2, mode, turn, team_size, tournament, elo)")

# Hash Map
roles = {
    0: "Top - ",
    1: "Jungle - ",
    2: "Mid - ",
    3: "Bottom - ",
    4: "Support - "
}

# create client object and slash commands
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    # TODO: remove id when deploying. current has banter server ID (also do for all commands)
    await tree.sync(guild=discord.Object(526081127643873280))
    print('Command: Shockwave')


@client.event
async def on_guild_join(ctx):
    cursor.execute(
        "INSERT INTO servers VALUES(?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)", (ctx.id, ctx.name))
    mainDB.commit()


@client.event
async def on_guild_remove(ctx):
    cursor.execute("""DELETE FROM servers WHERE guildId=?""", (ctx.id,))
    mainDB.commit()


# Helper Functions

# SQL get template function
async def get(guild_id, column):
    cursor.execute("SELECT " + column +
                   " FROM servers WHERE guildId=?", (guild_id,))
    return cursor.fetchone()[0]


# SQL update template function
async def update(guild_id, column, value):
    cursor.execute("UPDATE servers SET " + column +
                   "=? WHERE guildId=?", (value, guild_id))
    mainDB.commit()


# move players into their corresponding team channels
async def movefunc(ctx):
    channel1name = get(ctx.guild.id, "channel1")
    channel2name = get(ctx.guild.id, "channel2")
    team1 = get(ctx.guild.id, "team1")
    team2 = get(ctx.guild.id, "team2")
    new_og = str(ctx.message.author.voice.channel)

    update(ctx.guild.id, "original_channel", new_og)

    channel1 = discord.utils.get(ctx.guild.channels, name=channel1name)
    channel2 = discord.utils.get(ctx.guild.channels, name=channel2name)

    if channel1 is not None and channel2 is not None:
        for i in team1:
            member = discord.utils.get(ctx.guild.members, name=i)
            await member.move_to(channel1)

        for i in team2:
            member = discord.utils.get(ctx.guild.members, name=i)
            await member.move_to(channel2)
    else:
        await ctx.response.send_message('Team Channels Not Set! Use ".setTeams" to set teams.')


# TODO: what if there are more players in the channel than team sizes?
# or if number of members if odd?
async def randomizeTeamHelper(ctx):
    await clearTeamsHelper(ctx)

    members = []
    team1 = Team()
    team2 = Team()

    channel = ctx.message.author.voice.channel

    for i in channel.members:
        members.append(i)

    m = np.array(members)
    np.random.shuffle(m)

    for i in range(len(members)):
        if i < len(members) / 2:
            team1.add_player(m[i])
        else:
            team2.add_player(m[i].name)

    # seriialize both team objs





    # TODO: remove names, ids, result*, teamids
    # how are these handled now?
    update(ctx.guild.id, "team1", team1)
    update(ctx.guild.id, "team2", team2)


# TODO: add roles parameter
async def makeEmbedString(team : Team):
    for player in team.players:
        teamString += player.name + "\n"

    return teamString

# prints teams in discord channel
async def printEmbed(ctx, team1 : Team = None, team2 : Team = None):
    # TODO: remove result*, playerString
    team1_embedString = makeEmbedString(team1)
    team2_embedString = makeEmbedString(team2)
    captain1id = get(ctx.guild.id, "captain1")
    captain2id = get(ctx.guild.id, "captain2")
    captain1 = discord.utils.get(ctx.guild.members, id=captain1id)
    captain2 = discord.utils.get(ctx.guild.members, id=captain2id)
    playerString = get(ctx.guild.id, "playerString")
    players = get(ctx.guild.id, "players")

    team1_embed = discord.Embed(
        title="TEAM 1", description=team1_embedString, color=discord.Color.blue()
    )
    team2_embed = discord.Embed(
        title="TEAM 2", description=team2_embedString, color=discord.Color.red()
    )

    await ctx.response.send_message(embed=team1_embed)
    await ctx.response.send_message(embed=team2_embed)

    if channel is not None:
        playerString = ""
        for player in channel.members:
            # TODO: remove result1 and result2
            if (
                player.name != captain1.name
                and player.name != captain2.name
                and player.name in result1
                and player.name in result2
            ):
                if player.name not in players:
                    players.append(player.name)
                playerString += player.name + "\n"

        update(ctx.guild.id, "players", players)
        # TODO: remove playerString
        update(ctx.guild.id, "playerString", playerString)

        players_embed = discord.Embed(
            title="PLAYERS", description=playerString, color=discord.Color.dark_purple()
        )
        await ctx.response.send_message(embed=players_embed)
    else:
        playerString = get(ctx.guild.id, "playerString")
        players = get(ctx.guild.id, "players")
        for player in players:
            if (
                player != captain1.name
                and player != captain2.name
                and result1.__contains__(player) == False
                and result2.__contains__(player) == False
            ):
                if players.__contains__(player.name) == False:
                    players.append(player.name)
                playerString += player.name + "\n"

        update(ctx.guild.id, "players", players)

        players_embed = discord.Embed(
            title="PLAYERS", description=playerString, color=discord.Color.dark_purple()
        )
        await ctx.response.send_message(embed=players_embed)


# sets channels for teams
# TODO: change teams to expect array of two team names
async def setTeamHelper(ctx, teams="Team-1 Team-2"):
    teamsList = teams.split()

    guild = ctx.guild

    channel1 = discord.utils.get(ctx.guild.channels, name=teamsList[0])

    if channel1 is None:
        await guild.create_voice_channel(name=teamsList[0])
        channel1 = discord.utils.get(ctx.guild.channels, name=teamsList[0])

    channel2 = discord.utils.get(ctx.guild.channels, name=teamsList[1])

    if channel2 is None:
        await guild.create_voice_channel(name=teamsList[1])
        channel2 = discord.utils.get(ctx.guild.channels, name=teamsList[1])

    update(guild.id, "channel1", teamsList[0])
    update(guild.id, "channel2", teamsList[1])

    await ctx.response.send_message("Channels set!")

# TODO: rename this wtf
# randomizes teams and player roles


async def both(ctx):
    await randomizeTeamHelper(ctx)
    await randomRoleHelper(ctx)


async def randomRoleHelper(ctx):
    global roles

    result1 = ""
    result2 = ""

    team1 = get(ctx.guild.id, "team1")
    team2 = get(ctx.guild.id, "team2")

    random.shuffle(team1)
    random.shuffle(team2)

    # TODO: currently hardcoded but should add a way to create team of any size
    # e.g. based on game, different hashmaps for role
    for i in range(10):
        if i < 5:
            result1 += roles.get(i % 5) + str(team1[i % 5]) + "\n"
        else:
            result2 += roles.get(i % 5) + str(team2[i % 5]) + "\n"

    update(ctx.guild.id, "result1", result1)
    update(ctx.guild.id, "result2", result2)


# chooses captains for each team at random
async def captainsHelper(ctx, captain_1, captain_2):
    await clearTeamsHelper(ctx)

    # TODO: remove result1, result2, using_captains_ and original_channel
    result1 = ""
    result2 = ""
    team1ids = []
    team2ids = []
    team1 = []
    team2 = []

    update(ctx.guild.id, "captain1", captain_1.id)
    update(ctx.guild.id, "captain2", captain_2.id)
    update(ctx.guild.id, "using_captains", True)
    update(ctx.guild.id, "original_channel",
           str(ctx.message.author.voice.channel))
    original_channel = get(ctx.guild.id, "original_channel")

    if captain_1 is None or captain_2 is None:
        await ctx.response.send_message("Mention two team captains!")
    elif captain_1 == captain_2:
        await ctx.response.send_message("Mention two different people!")
    else:
        # TODO: why do we use captain_1? seems useless asf
        captain1 = captain_1
        result1 += str(captain1.name)
        update(ctx.guild.id, "result1", result1)
        team1ids.append(captain1.id)
        update(ctx.guild.id, "team1ids", team1ids)
        team1.append(captain1.name)
        update(ctx.guild.id, "team1", team1)

        captain2 = captain_2
        result2 += str(captain2.name)
        update(ctx.guild.id, "result2", result2)
        team2ids.append(captain2.id)
        update(ctx.guild.id, "team2ids", team2ids)
        team2.append(captain2.name)
        update(ctx.guild.id, "team2", team2)

        await printEmbed(
            ctx, discord.utils.get(ctx.guild.channels, name=original_channel)
        )

        await ctx.response.send_message("Captains selected!")
        await ctx.response.send_message(
            captain_1.mention
            + ', type ".choose  @_____" to pick a player for your team'
        )


# function for captain to choose a specific team member
async def chooseFunc(ctx, member):
    # TODO: remove drafted, captainsNum
    drafted = get(ctx.guild.id, "drafted")
    team_size = get(ctx.guild.id, "team_size")
    captainNum = get(ctx.guild.id, "captainNum")
    captain1id = get(ctx.guild.id, "captain1")
    captain2id = get(ctx.guild.id, "captain2")

    captain1 = discord.utils.get(ctx.guild.members, id=captain1id)
    captain2 = discord.utils.get(ctx.guild.members, id=captain2id)

    # TODO: clean this up. maybe use guard clauses instead?
    if drafted < (team_size * 2):
        if captainNum == 1 and ctx.message.author.id == captain1.id:
            await chooseHelper(ctx, member, 1)
        elif captainNum == 2 and ctx.message.author.id == captain2.id:
            await chooseHelper(ctx, member, 2)
        else:
            if (captainNum == 1 and ctx.message.author.id == captain2.id) or (
                captainNum == 2 and ctx.message.author.id == captain1.id
            ):
                await ctx.response.send_message("Not Your Turn!")
            elif (
                ctx.message.author.id != captain1.id
                and ctx.message.author.id != captain2.id
            ):
                await ctx.response.send_message("Only team captains can use this command!")


# choose random player from all remaining players
async def chooseRandomMember(ctx):
    randomMember = await getRandomMember(ctx)
    await chooseFunc(ctx, randomMember)


async def getRandomMember(ctx):
    players = get(ctx.guild.id, "players")

    player_members = []

    for player in players:
        player_members.append(discord.utils.get(
            ctx.guild.members, name=player))

    # TODO: instead, choose a random index in [0, arr_size - 1] and use that.
    # no need to shuffle
    m = np.array(player_members)
    np.random.shuffle(m)

    return m[0]


# helper fn for choosing team members from players that haven't been chosen
# TODO: using capNum sounds messy. why not just use their id?
async def chooseHelper(ctx, member, capNum):
    # TODO: remove result1, result2
    captain1 = get(ctx.guild.id, "captain1")
    captain2 = get(ctx.guild.id, "captain2")
    players = get(ctx.guild.id, "players")
    team1 = get(ctx.guild.id, "team1")
    team2 = get(ctx.guild.id, "team2")
    result1 = get(ctx.guild.id, "result1")
    result2 = get(ctx.guild.id, "result2")
    ids = get(ctx.guild.id, "ids")

    captain1 = discord.utils.get(ctx.guild.members, id=captain1id)
    captain2 = discord.utils.get(ctx.guild.members, id=captain2id)

    channel = ctx.message.author.voice.channel
    # TODO: what is the purpose of switch?
    switch = True

    if (
        member not in team1
        and member not in team2
        and member.name in players
    ):
        if capNum == 1:
            result1 += "\n" + member.name
            team1.append(member.name)
            update(ctx.guild.id, "team1", team1)
            update(ctx.guild.id, "result1", result1)
        else:
            result2 += "\n" + member.name
            team2.append(member.name)
            update(ctx.guild.id, "team2", team2)
            update(ctx.guild.id, "result2", result2)

        players.remove(member.name)
        ids.append(member.id)

        update(ctx.guild.id, "players", players)
        update(ctx.guild.id, "ids", ids)

        await printEmbed(ctx, channel)
    else:
        # TODO: cleanup this if-else ladder
        switch = False
        await ctx.response.send_message(
            "Player has already been selected or does not exist in the player list."
        )

    if players == []:
        await ctx.response.send_message(
            'You\'ve drafted the maximum number of people for the team size! Use ".move" to move everyone to the channels!'
        )
        return

    if capNum == 2 and switch:
        update(ctx.guild.id, "captainNum", 1)
        await ctx.response.send_message(
            captain1.mention + ', type ".choose  @_____" to pick a player for your team'
        )
    elif capNum == 1 and switch:
        update(ctx.guild.id, "captainNum", 2)
        await ctx.response.send_message(
            captain2.mention + ', type ".choose  @_____" to pick a player for your team'
        )
    else:
        if capNum == 1:
            await ctx.response.send_message(
                captain1.mention
                + ', type ".choose  @_____" to pick a player for your team'
            )
        else:
            await ctx.response.send_message(
                captain2.mention
                + ', type ".choose  @_____" to pick a player for your team'
            )


# TODO: RENAME THIS TO SOMETHING REAL ????
# sets up teams and moves them into respective channels
async def all(ctx, teams):
    await printEmbed(ctx)
    await setTeamHelper(ctx, teams)
    await movefunc(ctx)


# clears all current teams
async def clearTeamsHelper(ctx):
    guild_id = ctx.guild.id

    # TODO: remove unused columns
    update(guild_id, "original_channel", "")
    update(guild_id, "team1", "")
    update(guild_id, "team2", "")
    update(guild_id, "players", "")
    update(guild_id, "team_size", 5)
    update(guild_id, "mode", "Normal")
    update(guild_id, "turn", 1)

# Commands
# TODO: change ids when putting into production


@tree.command(
    name="set-team-size",
    description="Set the size of the teams",
    guild=discord.Object(id=526081127643873280)
)
async def setTeamSize(ctx, *, sizechange: int):
    update(ctx.guild.id, "team_size", sizechange)
    await ctx.response.send_message("Set team size!")


@tree.command(
    name="set-team-channels",
    description="Set the team channels",
    guild=discord.Object(id=526081127643873280)
)
async def setTeamChannels(ctx, *, team1: str, team2: str):
    await setTeamHelper(ctx, team1 + " " + team2)


@tree.command(
    name="move",
    description="Move players to their respective channels",
    guild=discord.Object(id=526081127643873280)
)
async def move(ctx):
    await movefunc(ctx)


# TODO: update website to current shockwave website
@tree.command(
    name="help",
    description="Get a list of commands",
    guild=discord.Object(id=526081127643873280)
)
async def help(ctx):
    await ctx.response.send_message("Visit WEBSITE NOT READY for a full list of commands")


# TODO: rename fullRandom to makeTeams
@tree.command(
    name="make-teams",
    description="Randomizes teams, roles, sets team channels, and moves players to their respective channels",
    guild=discord.Object(id=526081127643873280)
)
async def fullRandom(ctx, roles: bool = False, movevar: bool = True):
    if roles == 'True':
        await both(ctx)
    else:
        await randomizeTeamHelper(ctx)

    if movevar:
        await move(ctx)


@tree.command(
    name="return",
    description="Return all members (including spectators) to the original channel",
    guild=discord.Object(id=526081127643873280)
)
async def returnAll(ctx):
    og = get(ctx.guild.id, "original_channel")
    original_channel = discord.utils.get(ctx.guild.channels, name=og)
    chan1 = get(ctx.guild.id, "channel1")
    chan2 = get(ctx.guild.id, "channel2")
    original_channel = discord.utils.get(ctx.guild.channels, name=og)
    channel1 = discord.utils.get(ctx.guild.channels, name=chan1)
    channel2 = discord.utils.get(ctx.guild.channels, name=chan2)

    if original_channel == "":
        await ctx.response.send_message(
            'You have not been seperated into team voice channels! Use ".move" first.'
        )
    else:
        aggregate = channel1.members
        aggregate.extend(channel2.members)

        for i in aggregate:
            await i.move_to(original_channel)


@tree.command(
    name="captains",
    description="Start captain draft",
    guild=discord.Object(id=526081127643873280)
)
async def captains(ctx, captain_1: discord.Member = None, captain_2: discord.Member = None, random: bool = False):
    if len(ctx.message.author.voice.channel.members) < 2:
        ctx.response.send_message("Not enough players in the voice channel!")
    else:
        if random:
            players = []
            for player in ctx.message.author.voice.channel.members:
                players.append(player.name)

            update(ctx.guild.id, "players", players)

            # randomly choose captains
            captain1 = await getRandomMember(ctx)
            while captain1 is None:
                captain1 = await getRandomMember(ctx)

            # make sure captain1 and captain2 are different
            captain2 = await getRandomMember(ctx)
            while captain2 is None and captain2 == captain1:
                captain2 = await getRandomMember(ctx)

        # TODO: given our current code, is this check needed? yes since they can pass in no captains and random is false with more than 2 in vc
        if captain1 is None or captain_2 is None:
            ctx.response.send_message("Mention two team captains!")

        await captainsHelper(ctx, captain_1, captain_2)


@tree.command(
    name="choose",
    description="Choose a player for your team (captains only)",
    guild=discord.Object(id=526081127643873280)
)
async def choose(ctx, member: discord.Member = None, random: bool = False):
    if random:
        await chooseRandomMember(ctx)
    else:
        await chooseFunc(ctx, member)


@tree.command(
    name="clear",
    description="Clear data",
    guild=discord.Object(id=526081127643873280)
)
async def clearAll(ctx, clear_channels: bool = False, clear_tournament: bool = False, clear_elo: bool = False):
    await clearTeamsHelper(ctx)

    if clear_channels:
        update(ctx.guild.id, "channel1", "")
        update(ctx.guild.id, "channel2", "")

    if clear_tournament:
        update(ctx.guild.id, "tournament", "")
    
    if clear_elo:
        update(ctx.guild.id, "elo", "")

    await ctx.response.send_message("Cleared!")


@tree.command(
    name="notify",
    description="Notify a player of an invite to a team",
    guild=discord.Object(id=526081127643873280)
)
async def notify(ctx, member: discord.Member):
    team_size = get(ctx.guild.id, "team_size")
    channel = await member.create_dm()
    invite_channel = ctx.message.author.voice.channel
    invite_link = await invite_channel.create_invite(max_uses=1, unique=True)
    content = (
        ctx.message.author.name
        + " has invited you to a "
        + str(team_size * 2)
        + " man!\n\n"
        + str(invite_link)
    )
    await channel.response.send_message(content)
    await ctx.response.send_message("Sent an invite for the " + str(team_size * 2) + " man!")


@tree.command(
    name="roll",
    description="Roll a number between 1 and the number you provide",
    guild=discord.Object(id=526081127643873280)
)
async def roll(ctx, *, num: int):
    if int(num) > 1:
        rand = random.randint(1, int(num))
        await ctx.response.send_message("You rolled " + str(rand))
    else:
        await ctx.response.send_message("Please use a number greater than 1.")


@tree.command(
    name="randomize-roles",
    description="Randomize roles",
    guild=discord.Object(id=526081127643873280)
)
async def randomizeRoles(ctx):
    await randomRoleHelper(ctx)
    await printEmbed(ctx)

# TODO: move this somewhere else??
# or move all the setup code at the start to a main function here
client.run(token)
